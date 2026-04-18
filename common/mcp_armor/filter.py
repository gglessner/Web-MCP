"""Core content filtering logic for MCP Armor.

Provides functions to filter sensitive data from strings, dicts, and lists.
"""

from __future__ import annotations

import hashlib
import re
import logging
from typing import Any

try:
    from .config import FilterConfig, FilterPattern
except ImportError:
    from config import FilterConfig, FilterPattern


class ContentFilter:
    """Content filter that redacts sensitive patterns from text and data structures."""
    
    def __init__(self, config: FilterConfig):
        """Initialize the filter with a configuration.
        
        Args:
            config: FilterConfig containing patterns and settings.
        """
        self.config = config
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        self._compiled_patterns: list[tuple[FilterPattern, re.Pattern]] = []
        for pattern in self.config.patterns:
            if pattern.enabled and pattern.pattern:
                try:
                    compiled = re.compile(pattern.pattern, re.MULTILINE)
                    self._compiled_patterns.append((pattern, compiled))
                except re.error as e:
                    logging.warning(f"Invalid regex pattern '{pattern.name}': {e}")

        self._sensitive_key_patterns: list[re.Pattern] = []
        for key_pattern in getattr(self.config, "sensitive_keys", []):
            try:
                self._sensitive_key_patterns.append(re.compile(key_pattern))
            except re.error as e:
                logging.warning(f"Invalid sensitive_keys regex '{key_pattern}': {e}")

    def _is_sensitive_key(self, key: str) -> bool:
        return any(rx.fullmatch(key) for rx in self._sensitive_key_patterns)

    @staticmethod
    def _hash_secret(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    
    def filter_string(self, text: str) -> tuple[str, list[dict]]:
        """Filter sensitive data from a string.

        If a pattern defines a named group ``(?P<secret>...)``, only that
        span is redacted; the surrounding context (label, separator) is
        preserved. Patterns without a ``secret`` group redact group 0.

        Args:
            text: The input string to filter.

        Returns:
            Tuple of (filtered_text, list of redaction records).
        """
        if not text:
            return text, []

        # Collect candidate spans across all patterns.
        # Each span: (start, end, replacement, pattern_name)
        spans: list[tuple[int, int, str, str]] = []
        for pattern, compiled in self._compiled_patterns:
            for match in compiled.finditer(text):
                groups = match.groupdict()
                if "secret" in groups and groups["secret"]:
                    start, end = match.start("secret"), match.end("secret")
                else:
                    start, end = match.start(), match.end()
                spans.append((start, end, pattern.replacement, pattern.name))

        if not spans:
            return text, []

        # Resolve overlaps: leftmost-first, ties broken by widest.
        # Sort key: (start ascending, end descending). Python's sort is
        # stable, so equal (start, end) preserves pattern scan order.
        spans.sort(key=lambda s: (s[0], -s[1]))
        kept: list[tuple[int, int, str, str]] = []
        last_end = -1
        for span in spans:
            if span[0] >= last_end:
                kept.append(span)
                last_end = span[1]

        # Build redaction records from kept spans only — no plaintext stored.
        redactions = []
        for start, end, replacement, name in kept:
            secret_bytes = text[start:end].encode("utf-8")
            redactions.append({
                "pattern": name,
                "span": (start, end),
                "matched_len": end - start,
                "matched_hash": hashlib.sha256(secret_bytes).hexdigest()[:8],
                "replacement": replacement,
            })

        if self.config.dry_run:
            return text, redactions

        # Apply right-to-left so earlier indices stay valid.
        result = text
        for start, end, replacement, _ in reversed(kept):
            result = result[:start] + replacement + result[end:]

        return result, redactions
    
    def filter_dict(
        self, 
        data: dict, 
        _path: str = "",
        _redactions: list[dict] | None = None
    ) -> tuple[dict, list[dict]]:
        """Recursively filter sensitive data from a dictionary.
        
        Args:
            data: The dictionary to filter.
            _path: Internal parameter for tracking nested path (do not use).
            _redactions: Internal parameter for tracking redactions (do not use).
            
        Returns:
            Tuple of (filtered_dict, list of redaction records).
        """
        if _redactions is None:
            _redactions = []
        
        if not isinstance(data, dict):
            return data, _redactions
        
        result = {}
        for key, value in data.items():
            current_path = f"{_path}.{key}" if _path else str(key)
            key_is_sensitive = isinstance(key, str) and self._is_sensitive_key(key)

            if key_is_sensitive and isinstance(value, str):
                # Whole-value redaction triggered by key name. Don't run text
                # patterns on the value — that would let "harmless-looking"
                # secrets through. The key told us this is a secret; trust it.
                result[key] = "[REDACTED]"
                _redactions.append({
                    "pattern": "<sensitive_key>",
                    "key": key,
                    "path": current_path,
                    "matched_len": len(value),
                    "matched_hash": self._hash_secret(value),
                    "replacement": "[REDACTED]",
                })
            elif isinstance(value, str):
                filtered_value, value_redactions = self.filter_string(value)
                _redactions.extend(value_redactions)
                result[key] = filtered_value
            elif isinstance(value, dict):
                filtered_value, _ = self.filter_dict(value, current_path, _redactions)
                result[key] = filtered_value
            elif isinstance(value, list):
                filtered_value, _ = self.filter_list(value, current_path, _redactions)
                result[key] = filtered_value
            else:
                # int, float, bool, None — pass through.
                result[key] = value

        return result, _redactions
    
    def filter_list(
        self, 
        data: list, 
        _path: str = "",
        _redactions: list[dict] | None = None
    ) -> tuple[list, list[dict]]:
        """Recursively filter sensitive data from a list.
        
        Args:
            data: The list to filter.
            _path: Internal parameter for tracking nested path (do not use).
            _redactions: Internal parameter for tracking redactions (do not use).
            
        Returns:
            Tuple of (filtered_list, list of redaction records).
        """
        if _redactions is None:
            _redactions = []
        
        if not isinstance(data, list):
            return data, _redactions
        
        result = []
        for i, item in enumerate(data):
            current_path = f"{_path}[{i}]"
            
            if isinstance(item, str):
                filtered_item, item_redactions = self.filter_string(item)
                _redactions.extend(item_redactions)
                result.append(filtered_item)
            elif isinstance(item, dict):
                filtered_item, _ = self.filter_dict(item, current_path, _redactions)
                result.append(filtered_item)
            elif isinstance(item, list):
                filtered_item, _ = self.filter_list(item, current_path, _redactions)
                result.append(filtered_item)
            else:
                result.append(item)
        
        return result, _redactions
    
    def filter(self, data: Any) -> tuple[Any, list[dict]]:
        """Filter sensitive data from any supported type.

        Strings are filtered as text. JSON-string detection was removed:
        callers who want structural filtering of a JSON payload should
        ``json.loads`` it themselves, filter the dict, then re-serialize.
        The library does not guess.

        Args:
            data: str, dict, or list. Other types pass through unchanged.

        Returns:
            Tuple of (filtered_data, list of redaction records).
        """
        if isinstance(data, str):
            return self.filter_string(data)
        if isinstance(data, dict):
            return self.filter_dict(data)
        if isinstance(data, list):
            return self.filter_list(data)
        return data, []


def filter_content(
    data: Any, 
    config: FilterConfig | None = None
) -> tuple[Any, list[dict]]:
    """Convenience function to filter content with default or custom config.
    
    Args:
        data: The data to filter.
        config: Optional FilterConfig. If not provided, uses default config.
        
    Returns:
        Tuple of (filtered_data, list of redaction records).
    """
    if config is None:
        config = load_default_config()
    
    filter_instance = ContentFilter(config)
    return filter_instance.filter(data)


# Import this at module level to avoid circular import
try:
    from .config import load_default_config
except ImportError:
    from config import load_default_config