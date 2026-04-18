"""Out-of-band callback receiver — wraps interactsh-client for blind-vuln detection."""
from __future__ import annotations

import json
import shutil
import subprocess
import threading
import time
from typing import Any


class OOBReceiver:
    def __init__(self, provider: str = "interactsh"):
        self._provider = provider
        self._proc = None
        self._payload: dict[str, str] | None = None
        self._interactions: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._reader: threading.Thread | None = None

    def _spawn(self):
        binary = shutil.which("interactsh-client")
        if not binary:
            raise RuntimeError("interactsh-client not on PATH")
        return subprocess.Popen(
            [binary, "-json", "-v"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )

    def _ensure_started(self) -> None:
        if self._provider != "interactsh":
            raise NotImplementedError(f"oob provider {self._provider!r} not implemented")
        if self._proc is not None:
            return
        self._proc = self._spawn()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            with self._lock:
                if (msg.get("type") == "payload" or "unique-id" in msg
                        or (msg.get("domain") and self._payload is None)):
                    dom = msg.get("domain") or msg.get("data") or msg.get("unique-id")
                    if dom:
                        self._payload = {"domain": dom, "url": f"http://{dom}/"}
                elif msg.get("protocol"):
                    self._interactions.append({
                        "id": len(self._interactions) + 1,
                        "protocol": msg.get("protocol"),
                        "remote_addr": msg.get("remote_address") or msg.get("remote-address"),
                        "timestamp": msg.get("timestamp"),
                        "raw_request": msg.get("raw") or msg.get("raw-request"),
                    })

    def get_payload(self, timeout_s: float = 10.0) -> dict[str, str]:
        self._ensure_started()
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            with self._lock:
                if self._payload:
                    return dict(self._payload)
            time.sleep(0.05)
        raise TimeoutError("interactsh-client did not emit a payload domain")

    def poll(self, since_id: int = 0) -> list[dict[str, Any]]:
        self._ensure_started()
        with self._lock:
            return [i for i in self._interactions if i["id"] > since_id]

    def close(self) -> None:
        if self._proc:
            self._proc.terminate()
