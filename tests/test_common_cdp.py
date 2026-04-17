import asyncio
import json

import pytest
import websockets

from common.cdp import CDPSession, CDPError


async def _fake_cdp(ws):
    """Fake CDP server: echo method name in result, emit loadEventFired on Page.enable."""
    async for raw in ws:
        msg = json.loads(raw)
        mid = msg["id"]
        method = msg["method"]
        if method == "Page.enable":
            await ws.send(json.dumps({"id": mid, "result": {}}))
            await ws.send(json.dumps({
                "method": "Page.loadEventFired",
                "params": {"timestamp": 1.0},
            }))
        else:
            await ws.send(json.dumps({"id": mid, "result": {"method": method}}))


@pytest.mark.asyncio
async def test_cdp_send_and_event():
    async with websockets.serve(_fake_cdp, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        url = f"ws://127.0.0.1:{port}"

        events = []

        def on_event(name, params):
            events.append((name, params))

        async with CDPSession(url, on_event=on_event) as sess:
            result = await sess.send("Page.enable")
            assert result == {}
            # Give event loop a tick to receive the event
            await asyncio.sleep(0.05)
            assert ("Page.loadEventFired", {"timestamp": 1.0}) in events


@pytest.mark.asyncio
async def test_cdp_send_returns_result():
    async with websockets.serve(_fake_cdp, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        url = f"ws://127.0.0.1:{port}"
        async with CDPSession(url) as sess:
            r = await sess.send("DOM.getDocument", {"depth": -1})
            assert r == {"method": "DOM.getDocument"}


@pytest.mark.asyncio
async def test_cdp_error_response_raises():
    async def err_server(ws):
        async for raw in ws:
            mid = json.loads(raw)["id"]
            await ws.send(json.dumps({
                "id": mid,
                "error": {"code": -32000, "message": "boom"},
            }))

    async with websockets.serve(err_server, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        async with CDPSession(f"ws://127.0.0.1:{port}") as sess:
            with pytest.raises(RuntimeError, match="boom"):
                await sess.send("X.y")


@pytest.mark.asyncio
async def test_cdp_server_disconnect_fails_pending_send():
    """Server that drops the connection without replying — send() must fail, not hang."""

    async def dropper(ws):
        await asyncio.sleep(0.05)  # let the client send its request
        await ws.close()

    async with websockets.serve(dropper, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        async with CDPSession(f"ws://127.0.0.1:{port}") as sess:
            with pytest.raises((ConnectionError, RuntimeError)):
                await asyncio.wait_for(sess.send("X.y"), timeout=1.0)


@pytest.mark.asyncio
async def test_cdp_clean_exit_with_pending_send():
    """Context manager exit while a send is awaiting — no hang, no warnings."""

    async def silent(ws):
        async for _ in ws:
            pass  # never reply

    async with websockets.serve(silent, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]

        async def run():
            async with CDPSession(f"ws://127.0.0.1:{port}") as sess:
                pending = asyncio.create_task(sess.send("X.y"))
                await asyncio.sleep(0.05)
                # Exiting the context manager should fail the pending send.
            with pytest.raises((ConnectionError, RuntimeError)):
                await pending

        await asyncio.wait_for(run(), timeout=2.0)
