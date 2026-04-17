import pytest

from browser_mcp.tools import BrowserSession


class _FakeProc:
    def __init__(self):
        self.terminated = False
        self.killed = False
        self._alive = True

    def poll(self):
        return None if self._alive else 0

    def terminate(self):
        self.terminated = True
        self._alive = False

    def kill(self):
        self.killed = True
        self._alive = False

    def wait(self, timeout=None):
        self._alive = False


class _FakeCM:
    def __init__(self):
        self.exited = False

    async def __aexit__(self, *a):
        self.exited = True


@pytest.mark.asyncio
async def test_close_is_idempotent(tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    sess._proc = _FakeProc()
    cm = _FakeCM()
    sess._cdp_cm = cm
    sess._cdp = object()

    r1 = await sess.close()
    assert r1["ok"] is True
    assert cm.exited is True
    assert sess._proc is None
    # second close should still succeed with no errors
    r2 = await sess.close()
    assert r2["ok"] is True
