from __future__ import annotations

import asyncio
import json
from typing import Any


class MCPTestClient:
    def __init__(self, call_timeout: int = 90) -> None:
        self._call_timeout = call_timeout
        self._process: asyncio.subprocess.Process | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._request_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._reader_task: asyncio.Task | None = None

    async def start(self, command: str, *args: str | list[str]) -> None:
        cmd: list[str] = [command]
        for arg in args:
            if isinstance(arg, list):
                cmd.extend(arg)
            else:
                cmd.append(arg)

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=10 * 1024 * 1024,
        )
        self._reader = self._process.stdout
        self._writer = self._process.stdin
        self._reader_task = asyncio.create_task(self._read_loop())
        await self._initialize()

    async def _read_loop(self) -> None:
        assert self._reader is not None
        try:
            while True:
                line = await self._reader.readline()
                if not line:
                    break
                try:
                    message = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                if "id" in message and message["id"] in self._pending:
                    future = self._pending.pop(message["id"])
                    if not future.done():
                        future.set_result(message)
        except asyncio.CancelledError:
            pass

    async def _send(self, method: str, params: dict[str, Any] | None = None, *, notification: bool = False) -> dict:
        assert self._writer is not None
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if notification:
            self._writer.write((json.dumps(message) + "\n").encode("utf-8"))
            await self._writer.drain()
            return {}

        self._request_id += 1
        request_id = self._request_id
        message["id"] = request_id
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future
        self._writer.write((json.dumps(message) + "\n").encode("utf-8"))
        await self._writer.drain()

        try:
            response = await asyncio.wait_for(future, timeout=self._call_timeout)
        except asyncio.TimeoutError:
            self._pending.pop(request_id, None)
            raise TimeoutError(f"Timeout waiting for response to {method}")
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        return response.get("result", {})

    async def _initialize(self) -> None:
        await self._send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "playwright-mcp-python-tests", "version": "1.0.0"},
            },
        )
        await self._send("notifications/initialized", {}, notification=True)

    async def list_tools(self) -> list[dict]:
        result = await self._send("tools/list")
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        params: dict[str, Any] = {"name": name}
        if arguments is not None:
            params["arguments"] = arguments
        return await self._send("tools/call", params)

    async def close(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
