"""Logging utilities for MCP Armor.

Provides structured logging for MCP requests, responses, and redactions.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any


class MCPLogger:
    """Logger for MCP traffic with support for file and console output."""
    
    def __init__(
        self, 
        log_file: str | Path | None = None,
        log_requests: bool = True,
        log_responses: bool = True,
        console_output: bool = False,
    ):
        """Initialize the MCP logger.
        
        Args:
            log_file: Path to log file. If None, logs to console only.
            log_requests: Whether to log incoming requests.
            log_responses: Whether to log outgoing responses.
            console_output: Whether to also output to console.
        """
        self.log_file = Path(log_file) if log_file else None
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.console_output = console_output
        
        # Set up the logger
        self._logger = logging.getLogger("mcp_armor")
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers = []
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self._logger.addHandler(console_handler)
        
        # File handler (if log file specified)
        if self.log_file:
            # Ensure parent directory exists
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file, mode="a", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self._logger.addHandler(file_handler)
        
        # Also log to stdout if no handlers configured
        if not console_output and not self.log_file:
            null_handler = logging.FileHandler(os.devnull)
            self._logger.addHandler(null_handler)
    
    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    def _truncate(self, data: Any, max_length: int = 10000) -> str:
        """Truncate data for logging."""
        try:
            if isinstance(data, (dict, list)):
                text = json.dumps(data, indent=2, default=str)
            else:
                text = str(data)
            
            if len(text) > max_length:
                return text[:max_length] + f"\n... (truncated, {len(text)} total bytes)"
            return text
        except Exception:
            return str(data)[:max_length]
    
    def log_request(
        self, 
        tool_name: str, 
        parameters: dict[str, Any],
    ) -> None:
        """Log an incoming MCP tool request.
        
        Args:
            tool_name: Name of the MCP tool being called.
            parameters: Parameters passed to the tool.
        """
        if not self.log_requests:
            return
        
        entry = {
            "type": "request",
            "timestamp": self._get_timestamp(),
            "tool": tool_name,
            "parameters": parameters,
        }
        
        self._logger.info(f"MCP Request: {tool_name}")
        if self.console_output or self.log_file:
            self._logger.debug(f"Request details: {self._truncate(parameters)}")
    
    def log_response(
        self, 
        tool_name: str, 
        response: Any,
        redactions: list[dict] | None = None,
    ) -> None:
        """Log an MCP tool response.
        
        Args:
            tool_name: Name of the MCP tool that was called.
            response: The response data.
            redactions: List of redactions performed (if any).
        """
        if not self.log_responses:
            return
        
        entry = {
            "type": "response",
            "timestamp": self._get_timestamp(),
            "tool": tool_name,
            "redactions": redactions or [],
        }
        
        # Log summary
        if redactions:
            self._logger.warning(
                f"MCP Response: {tool_name} - {len(redactions)} redactions applied"
            )
            for r in redactions:
                self._logger.debug(f"  Redacted: {r.get('pattern')} -> {r.get('replacement')}")
        else:
            self._logger.info(f"MCP Response: {tool_name}")
        
        # Log full response if debug enabled
        if self.log_file:
            self._logger.debug(f"Response content: {self._truncate(response)}")
    
    def log_error(
        self, 
        tool_name: str, 
        error: Exception,
    ) -> None:
        """Log an error from MCP tool execution.
        
        Args:
            tool_name: Name of the MCP tool that errored.
            error: The exception that occurred.
        """
        entry = {
            "type": "error",
            "timestamp": self._get_timestamp(),
            "tool": tool_name,
            "error": str(error),
            "error_type": type(error).__name__,
        }
        
        self._logger.error(f"MCP Error: {tool_name} - {type(error).__name__}: {error}")
    
    def log_filter_event(
        self,
        event_type: str,
        data: Any,
        redactions: list[dict] | None = None,
    ) -> None:
        """Log a general filtering event.
        
        Args:
            event_type: Type of event (e.g., "request", "response", "raw_data").
            data: The data being filtered.
            redactions: List of redactions performed.
        """
        if not redactions:
            return
        
        self._logger.info(
            f"Filter Event: {event_type} - {len(redactions)} redactions"
        )
        for r in redactions:
            self._logger.debug(f"  {r.get('pattern')}: '{r.get('matched')}' -> '{r.get('replacement')}'")


# Global logger instance (lazy initialization)
_global_logger: MCPLogger | None = None


def get_logger(
    log_file: str | Path | None = None,
    log_requests: bool = True,
    log_responses: bool = True,
    console_output: bool = False,
) -> MCPLogger:
    """Get or create the global logger instance.
    
    Args:
        log_file: Path to log file.
        log_requests: Whether to log requests.
        log_responses: Whether to log responses.
        console_output: Whether to output to console.
        
    Returns:
        MCPLogger instance.
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = MCPLogger(
            log_file=log_file,
            log_requests=log_requests,
            log_responses=log_responses,
            console_output=console_output,
        )
    return _global_logger


def reset_logger() -> None:
    """Reset the global logger (useful for testing)."""
    global _global_logger
    _global_logger = None