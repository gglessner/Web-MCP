"""Core content filtering logic for MCP Armor.

Provides functions to filter sensitive data from strings, dicts, and lists.
"""

from __future__ import annotations

import json
import re
import logging
from typing import Any, Union

from .config import FilterConfig, FilterPattern


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
                    compiled = re.compile(pattern.pattern)
                    self._compiled_patterns.append((pattern, compiled))
                except re.error as e:
                    logging.warning(f"Invalid regex pattern '{pattern.name}': {e}")
    
    def filter_string(self, text: str) -> tuple[str, list[dict]]:
        """Filter sensitive data from a string.
        
        Args:
            text: The input string to filter.
            
        Returns:
            Tuple of (filtered_text, list of redaction records).
        """
        if not text:
            return text, []
        
        redactions = []
        result = text
        
        # First pass: find all matches using finditer to get full match objects
        # We collect all matches first, then apply substitutions
        matches_to_apply = []  # List of (start, end, replacement)
        
        for pattern, compiled in self._compiled_patterns:
            for match in compiled.finditer(result):
                # match.group(0) is the full match (not just capture groups)
                full_match = match.group(0)
                redactions.append({
                    "pattern": pattern.name,
                    "matched": full_match,
                    "replacement": pattern.replacement,
                })
                matches_to_apply.append((match.start(), match.end(), pattern.replacement))
        
        if not self.config.dry_run and matches_to_apply:
            # Apply substitutions from end to start to preserve positions
            # Sort by position descending
            matches_to_apply.sort(key=lambda x: x[0], reverse=True)
            
            for start, end, replacement in matches_to_apply:
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
            current_path = f"{_path}.{key}" if _path else key
            
            # Filter the key name itself
            filtered_key, key_redactions = self.filter_string(key)
            _redactions.extend(key_redactions)
            
            # Filter the value
            if isinstance(value, str):
                filtered_value, value_redactions = self.filter_string(value)
                _redactions.extend(value_redactions)
                result[filtered_key] = filtered_value
            elif isinstance(value, dict):
                filtered_value, _ = self.filter_dict(value, current_path, _redactions)
                result[filtered_key] = filtered_value
            elif isinstance(value, list):
                filtered_value, _ = self.filter_list(value, current_path, _redactions)
                result[filtered_key] = filtered_value
            else:
                # For other types (int, float, bool, None), keep as-is
                result[filtered_key] = value
        
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
    
    def filter(
        self, 
        data: Any
    ) -> tuple[Any, list[dict]]:
        """Filter sensitive data from any supported data type.
        
        Supports: str, dict, list, and types that serialize to JSON.
        
        Args:
            data: The data to filter (str, dict, list, or JSON-serializable).
            
        Returns:
            Tuple of (filtered_data, list of redaction records).
        """
        if isinstance(data, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(data)
                filtered, redactions = self._filter_any(parsed)
                return json.dumps(filtered, indent=2, default=str), redactions
            except (json.JSONDecodeError, TypeError):
                # Not valid JSON, treat as plain string
                return self.filter_string(data)
        
        return self._filter_any(data)
    
    def _filter_any(self, data: Any) -> tuple[Any, list[dict]]:
        """Internal helper to filter any supported type."""
        redactions = []
        
        if isinstance(data, dict):
            filtered, redactions = self.filter_dict(data)
        elif isinstance(data, list):
            filtered, redactions = self.filter_list(data)
        elif isinstance(data, str):
            filtered, redactions = self.filter_string(data)
        else:
            filtered = data
        
        return filtered, redactions


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
from .config import load_default_config