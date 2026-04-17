"""MCP Armor - Protect sensitive data in MCP traffic.

This library provides middleware functionality to:
1. Log all requests and responses passing through an MCP server
2. Filter sensitive data (passwords, tokens, certificates) before sending to AI models
3. Configure filtering patterns via YAML files

Author: Garland Glessner <gglessner@gmail.com>
License: GNU General Public License v3.0 (GPL-3.0)

Quick Start:
    from mcp_armor import ContentFilter, MCPLogger, load_config
    
    # Load configuration (from patterns.yaml or defaults)
    config = load_config()
    
    # Create filter and logger
    filter = ContentFilter(config)
    logger = MCPLogger(log_file="mcp_filter.log", console_output=True)
    
    # Filter data before sending to AI
    filtered_data, redactions = filter.filter(original_data)
    logger.log_response("tool_name", filtered_data, redactions)

For more advanced usage, see the documentation in the individual modules.
"""

from .config import (
    FilterConfig,
    FilterPattern,
    load_config,
    load_default_config,
)
from .filter import (
    ContentFilter,
    filter_content,
)
from .logger import (
    MCPLogger,
    get_logger,
    reset_logger,
)

# Version
__version__ = "1.0.0"

# Author
__author__ = "Garland Glessner <gglessner@gmail.com>"

# License
__license__ = "GNU General Public License v3.0 (GPL-3.0)"

# Public API
__all__ = [
    # Config
    "FilterConfig",
    "FilterPattern", 
    "load_config",
    "load_default_config",
    
    # Filter
    "ContentFilter",
    "filter_content",
    
    # Logger
    "MCPLogger",
    "get_logger",
    "reset_logger",
    
    # Version
    "__version__",
    
    # Author & License
    "__author__",
    "__license__",
]