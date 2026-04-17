# GitHub Repository Security Analysis Skill

This skill provides capabilities to analyze GitHub repositories for security posture using the GitHub MCP.

## Overview

Use this skill to perform comprehensive security analysis of GitHub repositories, including:
- Checking branch protection settings
- Finding exposed secrets or sensitive data
- Analyzing dependency vulnerabilities
- Reviewing security policies
- Examining code for security issues

## Available Tools

The GitHub MCP provides these tools (use `github` server):

### Server Management
- `list_servers` - List all configured GitHub instances

### Repository Analysis
- `get_repo` - Get detailed repository information
- `list_branches` - List all branches
- `list_commits` - List commits with filters
- `get_security_overview` - Get security posture overview

### File Analysis
- `get_file_contents` - Get file or directory contents
- `get_directory_tree` - Get repository file tree

### Security Scanning
- `list_dependabot_alerts` - List vulnerability alerts
- `search_code` - Search for patterns in code

## Finding Exposed Secrets

When searching for exposed secrets, use `search_code` with common patterns:

### Common Secret Patterns
```
password repo:owner/repo
token repo:owner/repo
api_key repo:owner/repo
secret repo:owner/repo
```

### Important: Filtered Secrets

When you find what appears to be a secret (password, token, API key, etc.), **always verify if it has been filtered by MCP Armor**.

If the value appears as `[REDACTED]`, it means MCP Armor has detected and filtered a sensitive value before it was sent to the AI. This is a security protection feature.

**Example of filtered secret in code:**
```python
# The actual password was: "super_secret_password_123"
# MCP Armor filtered it, showing:
password = "[REDACTED]"  # This was filtered by MCP Armor
```

**Example of unfiltered secret (requires immediate action):**
```python
# This secret was NOT filtered - needs remediation!
password = "actual_plaintext_password"  # NOT filtered - security risk!
```

### Actions When Secrets Are Found

1. **[REDACTED] values**: The secret is protected. Note the location in your report.
2. **Unfiltered secrets**: Flag as critical severity - the secret was exposed to the AI and may need rotation.

## Usage Examples

### Check Repository Security Posture
```
Use get_security_overview with repo_url: "https://github.com/owner/repo"
```

### Find Potential Secrets
```
Use search_code with query: "password repo:owner/repo language:python"
```

### List Vulnerability Alerts
```
Use list_dependabot_alerts with repo_url: "https://github.com/owner/repo", severity: "critical"
```

### Examine Branch Protection
```
Use get_security_overview and look for "default_branch_protected" in the response
```

## Security Analysis Workflow

1. **Initial Reconnaissance**
   - Use `get_security_overview` to understand repo security posture
   - Use `list_branches` to identify all branches

2. **Secret Detection**
   - Use `search_code` with common secret patterns
   - Document any `[REDACTED]` values (protected) vs unfiltered secrets (critical)

3. **Dependency Analysis**
   - Use `list_dependabot_alerts` to find known vulnerabilities
   - Check for outdated dependencies

4. **Code Review**
   - Use `get_directory_tree` to understand structure
   - Use `get_file_contents` to examine specific files

## Security Considerations

- All analysis is read-only via the GitHub MCP
- MCP Armor filters sensitive data before AI sees it
- Secrets displayed as `[REDACTED]` are protected by MCP Armor
- Always verify if secrets were filtered before reporting findings