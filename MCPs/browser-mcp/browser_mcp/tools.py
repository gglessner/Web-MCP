"""browser-mcp tool implementations."""
from __future__ import annotations

import asyncio
import base64
import shutil
import tempfile
import time
from collections import deque

from pathlib import Path

from common.cdp import CDPError, CDPSession, discover_targets
from common.evidence import EvidencePathError, write_evidence
from common.mcp_base import ErrorCode, error_envelope, ok_envelope

from .chrome_launcher import (
    ChromeNotFoundError,
    build_chrome_argv,
    launch_chrome,
    resolve_chrome_binary,
)


class BrowserSession:
    """Owns a single Chrome process + attached CDP session."""

    def __init__(
        self,
        *,
        chrome_candidates: list[str],
        cdp_port: int,
        default_proxy: str | None,
        user_data_dir_root: str,
        navigation_timeout_s: int = 30,
        evidence_root: Path | None = None,
    ) -> None:
        self._candidates = chrome_candidates
        self._cdp_port = cdp_port
        self._default_proxy = default_proxy
        self._udd_root = user_data_dir_root
        self._nav_timeout = navigation_timeout_s
        self._evidence_root = evidence_root

        self._proc = None
        self._udd: str | None = None
        self._cdp: CDPSession | None = None
        self._cdp_cm = None
        self._network_log: deque[dict] = deque(maxlen=5000)
        self._network_seq = 0
        self._load_events: asyncio.Queue[float] = asyncio.Queue()

    def is_attached(self) -> bool:
        return self._cdp is not None and self._proc is not None and self._proc.poll() is None

    def _on_event(self, method: str, params: dict) -> None:
        if method.startswith("Network."):
            self._network_seq += 1
            self._network_log.append({"seq": self._network_seq, "method": method, "params": params})
        elif method == "Page.loadEventFired":
            try:
                self._load_events.put_nowait(params.get("timestamp", time.time()))
            except asyncio.QueueFull:
                pass
        elif method == "Page.javascriptDialogOpening":
            # Auto-dismiss any JS dialogs (alert/confirm/prompt) so they don't block navigation.
            if self._cdp is not None:
                asyncio.ensure_future(
                    self._cdp.send("Page.handleJavaScriptDialog", {"accept": True})
                )

    async def launch(
        self,
        *,
        headless: bool = False,
        proxy: str | None = None,
    ) -> dict:
        if self.is_attached():
            await self.close()

        try:
            binary = resolve_chrome_binary(self._candidates)
        except ChromeNotFoundError as e:
            return error_envelope(ErrorCode.INTERNAL, str(e))

        udd = tempfile.mkdtemp(prefix="web-mcp-chrome-", dir=self._udd_root)
        self._udd = udd
        argv = build_chrome_argv(
            binary=binary,
            cdp_port=self._cdp_port,
            proxy=proxy if proxy is not None else self._default_proxy,
            headless=headless,
            user_data_dir=udd,
        )
        self._proc = launch_chrome(argv)

        # Poll for CDP ready
        ws_url: str | None = None
        for _ in range(50):
            try:
                targets = await discover_targets(f"http://127.0.0.1:{self._cdp_port}")
                for t in targets:
                    if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                if ws_url:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.1)

        if not ws_url:
            await self.close()
            return error_envelope(
                ErrorCode.INTERNAL,
                "Chrome started but CDP target did not appear within 5s",
            )

        self._cdp_cm = CDPSession(ws_url, on_event=self._on_event)
        self._cdp = await self._cdp_cm.__aenter__()
        await self._cdp.send("Page.enable")
        await self._cdp.send("Network.enable")
        await self._cdp.send("Runtime.enable")
        await self._cdp.send("DOM.enable")

        return ok_envelope({"chrome_binary": binary, "cdp_url": ws_url})

    async def close(self) -> dict:
        if self._cdp_cm is not None:
            try:
                await self._cdp_cm.__aexit__(None, None, None)
            except Exception:
                pass
        self._cdp = None
        self._cdp_cm = None
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
        self._proc = None
        if self._udd:
            shutil.rmtree(self._udd, ignore_errors=True)
        self._udd = None
        return ok_envelope({"closed": True})

    def _require_attached(self) -> dict | None:
        if not self.is_attached():
            return error_envelope(
                ErrorCode.TARGET_NOT_ATTACHED,
                "no browser session; call browser_launch first",
            )
        return None

    async def _drain_load_events(self) -> None:
        while not self._load_events.empty():
            try:
                self._load_events.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def navigate(self, url: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        await self._drain_load_events()
        try:
            await self._cdp.send("Page.navigate", {"url": url})
        except Exception as e:
            return error_envelope(ErrorCode.INTERNAL, f"Page.navigate failed: {e}")
        try:
            await asyncio.wait_for(self._load_events.get(), timeout=self._nav_timeout)
        except asyncio.TimeoutError:
            return error_envelope(
                ErrorCode.TIMEOUT,
                f"load event not received within {self._nav_timeout}s",
                detail={"url": url},
            )
        return ok_envelope({"url": url})

    async def wait_for(self, selector: str, *, timeout_s: float = 10.0,
                       state: str = "attached") -> dict:
        err = self._require_attached()
        if err:
            return err
        if state not in ("attached", "visible"):
            return error_envelope(ErrorCode.BAD_INPUT,
                                  f"state must be 'attached' or 'visible', got {state!r}")
        deadline = time.monotonic() + timeout_s
        interval = 0.1
        while True:
            root = await self._root_node_id()
            found = await self._cdp.send(
                "DOM.querySelector", {"nodeId": root, "selector": selector}
            )
            node_id = found.get("nodeId", 0)
            if node_id:
                if state == "attached":
                    return ok_envelope({"nodeId": node_id, "selector": selector})
                try:
                    await self._cdp.send("DOM.getBoxModel", {"nodeId": node_id})
                    return ok_envelope({"nodeId": node_id, "selector": selector})
                except Exception:
                    pass
            if time.monotonic() >= deadline:
                break
            await asyncio.sleep(interval)
            interval = min(interval * 1.5, 0.5)
        return error_envelope(
            ErrorCode.TIMEOUT,
            f"selector not {state} within {timeout_s}s",
            detail={"selector": selector},
        )

    async def snapshot(self) -> dict:
        err = self._require_attached()
        if err:
            return err
        dom = await self._cdp.send("DOM.getDocument", {"depth": -1})
        ax = await self._cdp.send("Accessibility.getFullAXTree")
        return ok_envelope({"dom": dom, "accessibility": ax})

    async def _root_node_id(self) -> int:
        doc = await self._cdp.send("DOM.getDocument", {"depth": 0})
        return doc["root"]["nodeId"]

    async def query(self, selector: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        root = await self._root_node_id()
        found = await self._cdp.send(
            "DOM.querySelector", {"nodeId": root, "selector": selector}
        )
        node_id = found.get("nodeId", 0)
        if not node_id:
            return error_envelope(
                ErrorCode.BAD_INPUT, "selector not found", detail={"selector": selector}
            )
        html = await self._cdp.send("DOM.getOuterHTML", {"nodeId": node_id})
        return ok_envelope({"html": html.get("outerHTML", ""), "nodeId": node_id})

    async def click(self, selector: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        root = await self._root_node_id()
        found = await self._cdp.send(
            "DOM.querySelector", {"nodeId": root, "selector": selector}
        )
        node_id = found.get("nodeId", 0)
        if not node_id:
            return error_envelope(
                ErrorCode.BAD_INPUT, "selector not found", detail={"selector": selector}
            )
        box = await self._cdp.send("DOM.getBoxModel", {"nodeId": node_id})
        quad = box["model"]["content"]
        cx = (quad[0] + quad[4]) / 2
        cy = (quad[1] + quad[5]) / 2
        for phase in ("mousePressed", "mouseReleased"):
            await self._cdp.send(
                "Input.dispatchMouseEvent",
                {"type": phase, "x": cx, "y": cy, "button": "left", "clickCount": 1},
            )
        return ok_envelope({"clicked": selector, "x": cx, "y": cy})

    async def fill(self, selector: str, text: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        root = await self._root_node_id()
        found = await self._cdp.send(
            "DOM.querySelector", {"nodeId": root, "selector": selector}
        )
        node_id = found.get("nodeId", 0)
        if not node_id:
            return error_envelope(
                ErrorCode.BAD_INPUT, "selector not found", detail={"selector": selector}
            )
        await self._cdp.send("DOM.focus", {"nodeId": node_id})
        await self._cdp.send("Input.insertText", {"text": text})
        return ok_envelope({"filled": selector, "length": len(text)})

    async def screenshot(self, *, full_page: bool = False,
                         save_to: str | None = None) -> dict:
        err = self._require_attached()
        if err:
            return err
        params = {"format": "png", "captureBeyondViewport": full_page}
        resp = await self._cdp.send("Page.captureScreenshot", params)
        b64 = resp.get("data", "")
        if save_to:
            if self._evidence_root is None:
                return error_envelope(ErrorCode.INTERNAL, "evidence_root not configured")
            try:
                png = base64.b64decode(b64)
                path = write_evidence(self._evidence_root, save_to, png)
            except EvidencePathError as e:
                return error_envelope(ErrorCode.BAD_INPUT, str(e))
            rel = str(path.relative_to(Path(self._evidence_root).resolve().parent))
            return ok_envelope({"format": "png", "bytes": len(png), "saved": rel})
        return ok_envelope({"format": "png", "base64": b64})

    async def eval_js(self, expression: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        resp = await self._cdp.send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        exc = resp.get("exceptionDetails")
        return ok_envelope(
            {
                "value": resp.get("result", {}).get("value"),
                "type": resp.get("result", {}).get("type"),
                "exception": exc.get("text") if exc else None,
            }
        )

    async def cookies(self, urls: list[str] | None = None) -> dict:
        err = self._require_attached()
        if err:
            return err
        params = {"urls": urls} if urls else {}
        resp = await self._cdp.send("Network.getCookies", params)
        return ok_envelope({"cookies": resp.get("cookies", [])})

    def network_log(self, since_seq: int = 0) -> dict:
        err = self._require_attached()
        if err:
            return err
        events = [e for e in self._network_log if e["seq"] > since_seq]
        return ok_envelope({"events": events, "next_seq": self._network_seq})

    async def get_response_body(self, request_id: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        try:
            resp = await self._cdp.send(
                "Network.getResponseBody", {"requestId": request_id}
            )
        except CDPError as e:
            return error_envelope(
                ErrorCode.BAD_INPUT,
                f"response body unavailable for requestId={request_id}: {e}",
                detail={"hint": "body is only retrievable while the originating page is loaded"},
            )
        body = resp.get("body", "")
        is_b64 = resp.get("base64Encoded", False)
        length = len(base64.b64decode(body)) if is_b64 and body else len(body)
        return ok_envelope({
            "request_id": request_id,
            "base64_encoded": is_b64,
            "body": body,
            "length": length,
        })

    async def set_cookie(
        self,
        *,
        name: str,
        value: str,
        domain: str,
        path: str = "/",
        secure: bool = False,
        http_only: bool = False,
        same_site: str | None = None,
    ) -> dict:
        err = self._require_attached()
        if err:
            return err
        params = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": path,
            "secure": secure,
            "httpOnly": http_only,
        }
        if same_site:
            params["sameSite"] = same_site
        resp = await self._cdp.send("Network.setCookie", params)
        if not resp.get("success", False):
            return error_envelope(ErrorCode.INTERNAL, "setCookie returned success=false")
        return ok_envelope({"set": True})
