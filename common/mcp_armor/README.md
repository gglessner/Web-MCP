# MCP Armor

MCP Armor is a Python library that protects sensitive data in MCP (Model Context Protocol) traffic by filtering passwords, tokens, API keys, certificates, and other secrets before they reach AI models.

**Version**: 1.0.0  
**Author**: Garland Glessner <gglessner@gmail.com>  
**License**: GNU General Public License v3.0 (GPL-3.0)

## Installation

```bash
pip install pyyaml
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

## Quick Start

```python
from mcp_armor import ContentFilter, load_config

# Load configuration from patterns.yaml
config = load_config('patterns.yaml')

# Create filter
filter = ContentFilter(config)

# Filter a string
filtered, redactions = filter.filter_string("password=secret123")
print(filtered)  # Output: password=[REDACTED]

# Filter a dictionary (recursive)
data = {
    "username": "admin",
    "password": "super_secret",
    "api_key": "sk_live_abc123"
}
filtered_data, redactions = filter.filter_dict(data)
# filtered_data = {"username": "admin", "password": "[REDACTED]", "api_key": "[REDACTED]"}
```

## Configuration

Create a `patterns.yaml` file or use the default patterns:

```yaml
# Filter patterns - add/modify as needed
patterns:
  - name: "password_key_value"
    pattern: "(?i)(password|passwd|pwd)\\s*[:=]\\s*[^\\s]+"
    replacement: "[REDACTED]"
    enabled: true
```

## Using with MCP Server

To protect your MCP server responses:

```python
from mcp_armor import ContentFilter, load_config, MCPLogger
from your_mcp_server import mcp  # Your FastMCP or MCP server

# Initialize
config = load_config()
filter = ContentFilter(config)
logger = MCPLogger(log_file="mcp_armor.log", console_output=True)

# Wrap your tool responses
@mcp.tool
def my_tool():
    # ... your tool logic ...
    result = {"password": "secret", "data": "value"}
    
    # Filter the result
    filtered_result, redactions = filter.filter_dict(result)
    
    # Log the redactions
    logger.log_response("my_tool", filtered_result, redactions)
    
    return filtered_result
```

## Detected Secret Types

MCP Armor detects **95+ patterns** including:

- **Passwords**: password=, passwd=, pwd=, secrets
- **API Keys**: api_key, client_id, client_secret
- **GitHub Tokens**: ghp_, gho_, ghu_, ghs_, ghr_
- **GitLab Tokens**: glpat-
- **AWS Keys**: AKIA (access keys), aws_secret_access_key
- **Azure**: Client secrets, storage keys, connection strings
- **Google Cloud**: API keys, OAuth clients, private keys
- **Alibaba Cloud**: LTAI, AKID access keys
- **Certificates**: SSH private keys, PFX passwords
- **JWT Tokens**: eyJ... (JSON Web Tokens)
- **Database Connections**: postgresql://, mysql://, mongodb://, etc.
- **SaaS API Keys**: Stripe, SendGrid, Twilio, Slack, NPM, etc.
- **DevOps**: TravisCI, CircleCI, Artifactory
- **Monitoring**: Sentry DSN, New Relic, Datadog
- **ML/AI**: OpenAI, HuggingFace, Replicate
- **Email Services**: Mailgun, Mailchimp, Postmark
- **Environment Variables**: PASSWORD, SECRET, TOKEN, API_KEY, etc.

## All Secrets Replaced with [REDACTED]

All matched secrets are replaced with `[REDACTED]` for consistent AI handling.

## API

### ContentFilter

```python
filter = ContentFilter(config)
```

#### Methods

- `filter_string(text)` - Filter a string, returns `(filtered_text, redactions)`
- `filter_dict(data)` - Filter a dictionary recursively, returns `(filtered_dict, redactions)`
- `filter_list(data)` - Filter a list recursively, returns `(filtered_list, redactions)`
- `filter(data)` - Auto-detect type and filter, returns `(filtered_data, redactions)`

### MCPLogger

```python
logger = MCPLogger(log_file="mcp_armor.log", console_output=True)
```

#### Methods

- `log_request(tool_name, parameters)` - Log incoming requests
- `log_response(tool_name, response, redactions)` - Log responses with redactions
- `log_error(tool_name, error)` - Log errors
- `log_filter_event(event_type, data, redactions)` - Log filter events

### load_config

```python
config = load_config('patterns.yaml')
```

Loads configuration from YAML file. Returns `FilterConfig` object.

## Example: Complete MCP Server Protection

```python
from fastmcp import FastMCP
from mcp_armor import ContentFilter, load_config, MCPLogger, get_logger

# Initialize
config = load_config('patterns.yaml')
filter = ContentFilter(config)

mcp = FastMCP("Protected MCP")

@mcp.tool
def get_secret_data():
    """Returns sensitive data that needs protection."""
    return {
        "password": "my_secret_password",
        "api_key": "ghp_abcdefghijklmnopqrstuvwxyz123456",
        "database": "postgresql://user:password123@localhost:5432/mydb"
    }

# Use FastMCP's raw_response to filter
@mcp.tool
def process_data():
    raw_result = {"token": "Bearer abc123", "data": "important"}
    filtered, redactions = filter.filter_dict(raw_result)
    logger = get_logger()
    logger.log_response("process_data", filtered, redactions)
    return filtered
```

## Development

Run tests:
```bash
python -m pytest
```

Run the import test:
```bash
python test_import.py
```

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.