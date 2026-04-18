import json
import re
from logging.handlers import RotatingFileHandler
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


def test_log_timestamp_has_microseconds_and_z(tmp_path):
    logger = setup_logger("ts-mcp", log_dir=tmp_path)
    logger.info("x")
    line = (tmp_path / "ts-mcp.log").read_text().splitlines()[-1]
    rec = json.loads(line)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", rec["ts"])


def test_logger_uses_rotating_handler(tmp_path):
    logger = setup_logger("rot-mcp", log_dir=tmp_path)
    h = logger.handlers[0]
    assert isinstance(h, RotatingFileHandler)
    assert h.maxBytes == 10 * 1024 * 1024
    assert h.backupCount == 3
