import json
import logging
from pathlib import Path

from common.logging import setup_logger


def test_setup_logger_writes_json_to_file(tmp_path: Path):
    log_dir = tmp_path / "logs"
    logger = setup_logger("test-mcp", log_dir=log_dir, level="DEBUG")

    logger.info("hello", extra={"req_id": "abc"})

    log_file = log_dir / "test-mcp.log"
    assert log_file.exists()
    line = log_file.read_text().strip().splitlines()[-1]
    record = json.loads(line)
    assert record["msg"] == "hello"
    assert record["level"] == "INFO"
    assert record["logger"] == "test-mcp"
    assert record["req_id"] == "abc"


def test_setup_logger_is_idempotent(tmp_path: Path):
    log_dir = tmp_path / "logs"
    a = setup_logger("dup", log_dir=log_dir)
    b = setup_logger("dup", log_dir=log_dir)
    assert a is b
    # No duplicated handlers
    assert len(a.handlers) == 1, f"expected single file handler, got {a.handlers}"


def test_setup_logger_does_not_leak_taskname(tmp_path: Path):
    import asyncio

    async def _log_from_task():
        logger = setup_logger("async-mcp", log_dir=tmp_path)
        logger.info("hello")

    asyncio.run(_log_from_task())
    line = (tmp_path / "async-mcp.log").read_text().strip().splitlines()[-1]
    record = json.loads(line)
    assert "taskName" not in record, f"taskName leaked: keys={sorted(record.keys())}"
