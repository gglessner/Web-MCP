# GitHub MCP + MCP Armor

A secure implementation of the Model Context Protocol (MCP) that enables AI assistants to explore GitHub repositories without exposing secrets found within those repositories to remote frontier AI models.

## The Problem

When you use an MCP server to access GitHub repositories with an AI assistant, the AI can read everything - including secrets that may be accidentally committed to the repository:

```
AI Assistant → MCP Request → GitHub API → Response (with secrets!) → AI Assistant
                                                              ↑
                                    Secrets in your repo: API keys,
                                    passwords, tokens, database credentials
```

**Without protection, secrets in your repositories can be:**
- Sent to remote AI models (potentially outside your infrastructure)
- Leaked through AI context windows
- Stored in AI conversation history
- Exposed via AI logging systems
- Used by the AI in ways you didn't intend

Examples of secrets that might be in your repo:
- API keys hardcoded in source files
- Database passwords in configuration files
- Cloud credentials in environment variables
- OAuth tokens in config files
- SSH private keys
- AWS access keys
- GitHub tokens
- And 95+ other secret patterns

## The Solution: MCP Armor

This project combines two components to provide secure GitHub repository exploration:

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   AI Assistant (Claude, Cursor, etc.)           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub MCP Server                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              MCP Armor Filter Layer                       │  │
│  │  • Scans all repo content for 95+ secret patterns         │  │
│  │  • Redacts secrets before AI sees them                    │  │
│  │  • Logs all redactions for auditing                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub API                                  │
│         (Accessing your repositories with your PAT)             │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Request Handling**: The AI requests repository data (files, issues, commits, etc.)
2. **GitHub API Call**: GitHub MCP fetches the requested data using your PAT
3. **Content Scanning**: Before returning the response, MCP Armor scans ALL content for:
   - GitHub tokens (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)
   - Passwords and API keys in code and configs
   - Database connection strings
   - AWS/Azure/Google cloud credentials
   - SSH private keys and certificates
   - JWT tokens and OAuth secrets
   - And 95+ other secret patterns
4. **Redaction**: All detected secrets are replaced with `[REDACTED]`
5. **Safe Response**: The AI receives the data without any secrets

This ensures that even if a developer accidentally commits secrets to a repo, those secrets never reach the AI assistant.

## Components

### github_mcp

**Version**: 1.0.0

A read-only MCP server providing 20+ tools for GitHub operations:

| Category | Tools |
|----------|-------|
| **Server Management** | `list_servers` |
| **Repositories** | `list_repos`, `get_repo`, `list_branches`, `list_commits`, `list_tags` |
| **Issues** | `list_issues`, `get_issue`, `list_issue_comments` |
| **Pull Requests** | `list_pulls`, `get_pull`, `list_pull_files`, `list_pull_comments` |
| **Files/Code** | `get_file_contents`, `get_directory_tree` |
| **Search** | `search_repos`, `search_code`, `search_issues` |
| **Security** | `get_security_overview`, `list_dependabot_alerts` |

> **Note:** The github_mcp is **read-only** and does not provide tools to clone or download full repository contents to local files. However, you can:
> - View individual file contents with `get_file_contents`
> - Browse directory trees with `get_directory_tree` (up to 5 levels deep)
> - Get download URLs via `list_tags` (provides `zipball_url` and `tarball_url`) to download with external tools like `curl` or `git clone`

### mcp_armor

A Python library that filters sensitive data from MCP traffic:

- **95+ pattern detections** including GitHub tokens, AWS keys, Azure secrets, database connections, JWTs, and more
- **Recursive filtering** for dictionaries, lists, and nested structures
- **Audit logging** to track all redactions
- **Configurable patterns** via YAML configuration

## Installation

### Prerequisites

- Python 3.9+
- GitHub Personal Access Token(s)

### Setup

1. **Install dependencies**:

```bash
cd MCPs/libs/mcp_armor
pip install -r requirements.txt
```

2. **Configure your GitHub token(s)**:

Create a `config.json` file (or use environment variables):

```json
{
  "servers": {
    "github.com": {
      "base_url": "https://api.github.com",
      "token_env": "GITHUB_TOKEN",
      "description": "GitHub.com"
    }
  },
  "default_server": "github.com"
}
```

Then set the environment variable:

```bash
# Linux/macOS
export GITHUB_TOKEN=ghp_your_token_here

# Windows
set GITHUB_TOKEN=ghp_your_token_here
```

3. **Run the MCP server**:

```bash
python -m github_mcp
```

Or configure it in your AI assistant's MCP settings.

## Security Features

### Response Filtering

The MCP Armor filter layer automatically detects and redacts:

- **GitHub Tokens**: `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, `glpat-`
- **Passwords**: password=, passwd=, pwd= in code and configs
- **API Keys**: Generic API keys, client secrets
- **Cloud Credentials**: AWS keys, Azure secrets, GCP keys, Aliyun keys
- **Database Connections**: PostgreSQL, MySQL, MongoDB, Redis, Oracle
- **OAuth Tokens**: Bearer tokens, JWTs, OAuth secrets
- **SSH Keys**: Private keys, certificates
- **Infrastructure**: Vault tokens, Kubernetes secrets

### What Gets Protected

| Data Type | Example | Protected |
|-----------|---------|-----------|
| Source code | `api_key = "sk_live_abc123"` | ✅ Redacted |
| Config files | `password: "secret123"` | ✅ Redacted |
| Environment files | `AWS_SECRET=xyz` | ✅ Redacted |
| Database URLs | `postgresql://user:pass@host` | ✅ Redacted |
| API credentials | `ghp_tokenabcdefghijklmnop` | ✅ Redacted |
| SSH keys | `-----BEGIN PRIVATE KEY-----` | ✅ Redacted |
| Cloud configs | `AKIAIOSFODNN7EXAMPLE` | ✅ Redacted |

### Audit Logging

All MCP interactions are logged to:
```
MCPs/github_mcp/logs/github_mcp_armor_[timestamp].log
```

Logs include:
- Request parameters
- Redacted content (showing what was filtered)
- Which patterns matched which secrets

## Example: Protected Response

**Before MCP Armor** (dangerous - secrets in your repo exposed):
```json
{
  "filename": "config.js",
  "content": "const apiKey = 'sk_live_abc123'; const dbPassword = 'secret123';",
  "repo": "owner/myapp"
}
```

**After MCP Armor** (safe - secrets redacted):
```json
{
  "filename": "config.js",
  "content": "const apiKey = '[REDACTED]'; const dbPassword = '[REDACTED]';",
  "repo": "owner/myapp"
}
```

## Configuration

### Pattern Customization

Edit `MCPs/libs/mcp_armor/patterns.yaml` to add or modify detection patterns:

```yaml
patterns:
  - name: "my_company_api_key"
    pattern: "MYCOMPANY_[A-Za-z0-9]{20,}"
    replacement: "[REDACTED]"
    enabled: true
```

### Multiple GitHub Instances

```json
{
  "servers": {
    "github.com": {
      "base_url": "https://api.github.com",
      "token_env": "GITHUB_TOKEN",
      "description": "GitHub.com"
    },
    "github.enterprise": {
      "base_url": "https://github.enterprise.com/api/v3",
      "token_env": "GHE_TOKEN",
      "description": "GitHub Enterprise"
    }
  },
  "default_server": "github.com"
}
```

## Project Structure

```
MCP Armor/
├── MCPs/
│   ├── github_mcp/           # GitHub MCP Server
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── clients.py        # GitHub API client management
│   │   ├── config.py         # Configuration loader
│   │   ├── server.py         # MCP server with Armor integration
│   │   └── logs/             # Audit logs
│   └── libs/
│       └── mcp_armor/        # Security filtering library
│           ├── __init__.py
│           ├── config.py
│           ├── filter.py     # Content filtering
│           ├── logger.py     # Audit logging
│           ├── patterns.yaml # Secret detection patterns
│           └── requirements.txt
├── skills/
│   └── github-repository-security/
└── README.md
```

## Integration with AI Assistants

### Claude Desktop (Claude Code)

Add to your `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxx"
      }
    }
  }
}
```

### Cursor

Configure via Settings → MCP Servers.

### Other MCP Clients

The server communicates via stdio using the MCP protocol. Any MCP-compatible client will work.

## Benefits

| Benefit | Description |
|---------|-------------|
| **Secret Protection** | API keys, passwords, tokens in repos stay secret |
| **Safe Code Review** | Let AI analyze code without exposing credentials |
| **Secure Exploration** | Browse repositories without accidental exposure |
| **Audit Trail** | Complete logging of all redactions |
| **Multi-Cloud Ready** | Works with GitHub Enterprise, multiple servers |
| **Open Source** | Full transparency on how data is handled |

## Why This Matters

When you give an AI assistant access to your GitHub repositories, you're giving it read access to everything - including secrets that shouldn't be there. Even with best practices, secrets sometimes leak into code:

- Developers testing locally
- Old commits that were supposed to be removed
- Configuration files for internal tools
- Backup files

MCP Armor ensures that when your AI assistant reads your repositories, it never sees these secrets. The AI can help you with code review, debugging, and exploration without creating a security risk.

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

- **mcp_armor**: GPL-3.0
- **github_mcp**: GPL-3.0

See [LICENSE](LICENSE) for details.

## Author

Garland Glessner <gglessner@gmail.com>

---

**⚡ Secure your AI-assisted code exploration with MCP Armor - because secrets in your repos deserve protection.**