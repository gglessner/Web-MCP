"""Chrome DevTools Protocol session over websocket."""
from __future__ import annotations

import asyncio
import itertools
import json
from typing import Any, Callable

import websockets
from websockets.asyncio.client import ClientConnection


EventCallback = Callable[[str, dict[str, Any]], None]


class CDPError(RuntimeError):
    """CDP protocol-level error. Subclass of RuntimeError for caller compatibility."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(f"CDP error {code}: {message}")
        self.code = code
        self.data = data


class CDPSession:
    """Async CDP client over websocket.

    Use as `async with CDPSession(url, on_event=cb) as sess: await sess.send(...)`.

    The optional `on_event` callback is invoked synchronously from the reader
    coroutine for every non-reply CDP event. It must be fast and non-blocking
    (e.g. a deque append or queue put_nowait); anything slower will starve
    request/response correlation.
    """

    def __init__(self, ws_url: str, *, on_event: EventCallback | None = None) -> None:
        self._url = ws_url
        self._on_event = on_event
        self._ws: ClientConnection | None = None
        self._reader_task: asyncio.Task | None = None
        self._pending: dict[int, asyncio.Future] = {}
        self._id_seq = itertools.count(1)

    async def __aenter__(self) -> "CDPSession":
        self._ws = await websockets.connect(self._url, max_size=64 * 1024 * 1024)
        self._reader_task = asyncio.create_task(self._reader())
        return self

    async def __aexit__(self, *exc: Any) -> None:
        # Close ws first so reader's `async for` exits cleanly via ConnectionClosedOK.
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
        # Await the reader so it finalizes _pending; no "Task was destroyed" warnings.
        if self._reader_task is not None and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except (asyncio.CancelledError, Exception):
                pass
        # Safety net: if any futures survived reader finalization, fail them now.
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("CDP session closed"))
        self._pending.clear()

    async def send(self, method: str, params: dict[str, Any] | None = None) -> Any:
        if self._ws is None:
            raise RuntimeError("CDP session not open; use 'async with CDPSession(...)'")

        mid = next(self._id_seq)
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[mid] = fut
        await self._ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        return await fut

    async def _reader(self) -> None:
        if self._ws is None:
            raise RuntimeError("CDP session not open; use 'async with CDPSession(...)'")

        try:
            async for raw in self._ws:
                msg = json.loads(raw)
                if "id" in msg:
                    fut = self._pending.pop(msg["id"], None)
                    if fut is None:
                        continue
                    if "error" in msg:
                        err = msg["error"]
                        fut.set_exception(
                            CDPError(
                                code=int(err.get("code", 0)),
                                message=err.get("message", "cdp error"),
                                data=err.get("data"),
                            )
                        )
                    else:
                        fut.set_result(msg.get("result", {}))
                else:
                    method = msg.get("method")
                    params = msg.get("params", {})
                    if method and self._on_event:
                        self._on_event(method, params)
        except (asyncio.CancelledError, websockets.ConnectionClosed):
            pass
        finally:
            # Whatever caused the reader to exit, fail in-flight callers.
            exc = ConnectionError("CDP websocket closed")
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(exc)
            self._pending.clear()


async def discover_targets(http_url: str = "http://127.0.0.1:9222") -> list[dict]:
    """Return CDP target list via DevTools HTTP endpoint."""
    import httpx
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(f"{http_url}/json")
        resp.raise_for_status()
        return resp.json()
