"""GitHub MCP Server - Read-only tools for multiple GitHub instances.

Provides 20 read-only tools for exploring repositories, issues, pull requests,
files, and security posture across github.com and GitHub Enterprise servers.

Protected by MCP Armor - filters sensitive data before sending to AI models.
"""

from __future__ import annotations

import base64
from datetime import datetime
import functools
import os
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from github import GithubException

from .config import load_config
from .clients import GitHubClients

# Add mcp_armor package root to path:
# MCPs/github_mcp/server.py -> MCPs/libs (which contains mcp_armor/)
_this_dir = Path(__file__).resolve().parent
_libs_root = _this_dir.parent / "libs"
_mcp_armor_pkg_dir = _libs_root / "mcp_armor"
if _mcp_armor_pkg_dir.exists():
    import sys
    sys.path.insert(0, str(_libs_root))
    from mcp_armor import ContentFilter, MCPLogger, load_config as load_armor_config

# Initialize MCP Armor (if available)
try:
    _armor_config = load_armor_config(str(_mcp_armor_pkg_dir / "patterns.yaml"))
    _filter = ContentFilter(_armor_config)
    # Always write logs under MCPs/github_mcp/logs
    _logs_dir = _this_dir / "logs"
    _log_session_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _logger = MCPLogger(
        log_file=str(_logs_dir / f"github_mcp_armor_{_log_session_ts}.log"),
        console_output=False
    )
    _MCP_ARMOR_AVAILABLE = True
except Exception as e:
    _filter = None
    _logger = None
    _MCP_ARMOR_AVAILABLE = False
    print(f"MCP Armor initialization failed: {e}")


def _filter_response(result, tool_name: str):
    """Filter sensitive data from response using MCP Armor."""
    if not _MCP_ARMOR_AVAILABLE or _filter is None:
        if _logger:
            _logger.log_response(tool_name, result, [])
        return result
    
    # Filter the result - handles dict, list, str
    if isinstance(result, dict):
        filtered, redactions = _filter.filter_dict(result)
    elif isinstance(result, list):
        filtered, redactions = _filter.filter_list(result)
    elif isinstance(result, str):
        filtered, redactions = _filter.filter_string(result)
    else:
        filtered, redactions = result, []
    
    # Log redactions if any
    if _logger:
        _logger.log_response(tool_name, filtered, redactions)
    
    return filtered


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

_config = load_config()
_gh = GitHubClients(_config)

mcp = FastMCP(
    "GitHub MCP (Protected)",
    instructions=(
        "Read-only GitHub tools for exploring repositories, issues, PRs, "
        "code, and security across multiple GitHub servers. "
        "All repo-scoped tools accept a repo_url parameter "
        "(e.g. https://github.com/owner/repo). "
        "Use list_servers to see configured GitHub instances. "
        "This MCP is protected by MCP Armor - sensitive data is filtered before AI sees it."
    ),
)


_raw_tool_decorator = mcp.tool


def _mcp_tool_with_armor(func):
    """Wrap each MCP tool so MCP Armor logs/filtering always run."""
    @functools.wraps(func)
    def _wrapped(*args, **kwargs):
        if _logger:
            _logger.log_request(func.__name__, {"args": list(args), "kwargs": kwargs})
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            if _logger:
                _logger.log_error(func.__name__, e)
            # Return structured error so every tool call has a response log entry.
            result = _error(e)
        return _filter_response(result, func.__name__)

    return _raw_tool_decorator(_wrapped)


# Ensure every @mcp.tool below is wrapped with MCP Armor behavior.
mcp.tool = _mcp_tool_with_armor


def _error(e: Exception) -> dict:
    """Format an exception as a structured error response."""
    if isinstance(e, GithubException):
        return {"error": True, "status": e.status, "message": str(e.data)}
    return {"error": True, "message": str(e)}


# ===================================================================
# Server Management
# ===================================================================


@mcp.tool
def list_servers() -> list[dict]:
    """List all configured GitHub servers with their names, hostnames,
    and whether they are authenticated."""
    return _gh.list_servers()


# ===================================================================
# Repository Tools
# ===================================================================


@mcp.tool
def list_repos(
    owner: str,
    server: Optional[str] = None,
    repo_type: str = "all",
    max_results: int = 30,
) -> list[dict] | dict:
    """List repositories for a user or organization.

    Args:
        owner: GitHub username or organization name.
        server: Server alias (from list_servers). Uses default if omitted.
        repo_type: Filter type - all, owner, public, private, member.
        max_results: Maximum number of repos to return (default 30).
    """
    try:
        client = _gh.get_client(server)
        user = client.get_user(owner)
        repos = user.get_repos(type=repo_type)
        results = []
        for repo in repos[:max_results]:
            results.append(
                {
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "private": repo.private,
                    "archived": repo.archived,
                    "default_branch": repo.default_branch,
                    "updated_at": str(repo.updated_at),
                    "html_url": repo.html_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


@mcp.tool
def get_repo(repo_url: str) -> dict:
    """Get detailed information about a repository.

    Args:
        repo_url: Full URL of the repository (e.g. https://github.com/owner/repo).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        return {
            "full_name": repo.full_name,
            "description": repo.description,
            "language": repo.language,
            "languages": repo.get_languages(),
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "watchers": repo.watchers_count,
            "private": repo.private,
            "archived": repo.archived,
            "default_branch": repo.default_branch,
            "license": repo.license.name if repo.license else None,
            "topics": repo.get_topics(),
            "created_at": str(repo.created_at),
            "updated_at": str(repo.updated_at),
            "pushed_at": str(repo.pushed_at),
            "html_url": repo.html_url,
            "clone_url": repo.clone_url,
            "size_kb": repo.size,
        }
    except Exception as e:
        return _error(e)


@mcp.tool
def list_branches(
    repo_url: str, max_results: int = 50
) -> list[dict] | dict:
    """List branches in a repository.

    Args:
        repo_url: Full URL of the repository.
        max_results: Maximum number of branches to return (default 50).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        results = []
        for branch in repo.get_branches()[:max_results]:
            results.append(
                {
                    "name": branch.name,
                    "protected": branch.protected,
                    "sha": branch.commit.sha,
                }
            )
        return results
    except Exception as e:
        return _error(e)


@mcp.tool
def list_commits(
    repo_url: str,
    branch: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    author: Optional[str] = None,
    max_results: int = 30,
) -> list[dict] | dict:
    """List commits in a repository with optional filters.

    Args:
        repo_url: Full URL of the repository.
        branch: Branch or SHA to list commits from. Defaults to the repo's default branch.
        since: ISO 8601 date string - only commits after this date (e.g. 2025-01-01).
        until: ISO 8601 date string - only commits before this date.
        author: Filter by commit author (GitHub username or email).
        max_results: Maximum number of commits to return (default 30).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        kwargs: dict = {}
        if branch:
            kwargs["sha"] = branch
        if since:
            kwargs["since"] = datetime.fromisoformat(since)
        if until:
            kwargs["until"] = datetime.fromisoformat(until)
        if author:
            kwargs["author"] = author

        results = []
        for commit in repo.get_commits(**kwargs)[:max_results]:
            results.append(
                {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "author_email": commit.commit.author.email,
                    "date": str(commit.commit.author.date),
                    "html_url": commit.html_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


@mcp.tool
def list_tags(
    repo_url: str, max_results: int = 30
) -> list[dict] | dict:
    """List tags in a repository.

    Args:
        repo_url: Full URL of the repository.
        max_results: Maximum number of tags to return (default 30).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        results = []
        for tag in repo.get_tags()[:max_results]:
            results.append(
                {
                    "name": tag.name,
                    "sha": tag.commit.sha,
                    "tarball_url": tag.tarball_url,
                    "zipball_url": tag.zipball_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


# ===================================================================
# Issue Tools
# ===================================================================


@mcp.tool
def list_issues(
    repo_url: str,
    state: str = "open",
    labels: Optional[str] = None,
    assignee: Optional[str] = None,
    max_results: int = 30,
) -> list[dict] | dict:
    """List issues in a repository (excludes pull requests).

    Args:
        repo_url: Full URL of the repository.
        state: Issue state filter - open, closed, or all.
        labels: Comma-separated label names to filter by.
        assignee: GitHub username to filter by assignee.
        max_results: Maximum number of issues to return (default 30).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        kwargs: dict = {"state": state}
        if labels:
            kwargs["labels"] = [
                repo.get_label(l.strip()) for l in labels.split(",")
            ]
        if assignee:
            kwargs["assignee"] = assignee

        results = []
        for issue in repo.get_issues(**kwargs)[:max_results]:
            if issue.pull_request:
                continue
            results.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "labels": [l.name for l in issue.labels],
                    "assignees": [a.login for a in issue.assignees],
                    "author": issue.user.login if issue.user else None,
                    "comments": issue.comments,
                    "created_at": str(issue.created_at),
                    "updated_at": str(issue.updated_at),
                    "html_url": issue.html_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


@mcp.tool
def get_issue(repo_url: str, number: int) -> dict:
    """Get full details of a specific issue including its body.

    Args:
        repo_url: Full URL of the repository.
        number: Issue number.
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        issue = repo.get_issue(number)
        return {
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "body": issue.body,
            "labels": [l.name for l in issue.labels],
            "assignees": [a.login for a in issue.assignees],
            "author": issue.user.login if issue.user else None,
            "milestone": issue.milestone.title if issue.milestone else None,
            "comments": issue.comments,
            "created_at": str(issue.created_at),
            "updated_at": str(issue.updated_at),
            "closed_at": str(issue.closed_at) if issue.closed_at else None,
            "html_url": issue.html_url,
        }
    except Exception as e:
        return _error(e)


@mcp.tool
def list_issue_comments(
    repo_url: str, number: int, max_results: int = 30
) -> list[dict] | dict:
    """List comments on a specific issue.

    Args:
        repo_url: Full URL of the repository.
        number: Issue number.
        max_results: Maximum number of comments to return (default 30).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        issue = repo.get_issue(number)
        results = []
        for comment in issue.get_comments()[:max_results]:
            results.append(
                {
                    "id": comment.id,
                    "author": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": str(comment.created_at),
                    "updated_at": str(comment.updated_at),
                    "html_url": comment.html_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


# ===================================================================
# Pull Request Tools
# ===================================================================


@mcp.tool
def list_pulls(
    repo_url: str,
    state: str = "open",
    base: Optional[str] = None,
    max_results: int = 30,
) -> list[dict] | dict:
    """List pull requests in a repository.

    Args:
        repo_url: Full URL of the repository.
        state: PR state filter - open, closed, or all.
        base: Filter by base branch name.
        max_results: Maximum number of PRs to return (default 30).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        kwargs: dict = {"state": state}
        if base:
            kwargs["base"] = base

        results = []
        for pr in repo.get_pulls(**kwargs)[:max_results]:
            results.append(
                {
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "author": pr.user.login if pr.user else None,
                    "head": pr.head.ref,
                    "base": pr.base.ref,
                    "draft": pr.draft,
                    "mergeable": pr.mergeable,
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "changed_files": pr.changed_files,
                    "created_at": str(pr.created_at),
                    "updated_at": str(pr.updated_at),
                    "html_url": pr.html_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


@mcp.tool
def get_pull(repo_url: str, number: int) -> dict:
    """Get full details of a specific pull request.

    Args:
        repo_url: Full URL of the repository.
        number: Pull request number.
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        pr = repo.get_pull(number)
        return {
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "body": pr.body,
            "author": pr.user.login if pr.user else None,
            "head": {"ref": pr.head.ref, "sha": pr.head.sha},
            "base": {"ref": pr.base.ref, "sha": pr.base.sha},
            "draft": pr.draft,
            "merged": pr.merged,
            "mergeable": pr.mergeable,
            "merge_commit_sha": pr.merge_commit_sha,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
            "commits": pr.commits,
            "comments": pr.comments,
            "review_comments": pr.review_comments,
            "labels": [l.name for l in pr.labels],
            "assignees": [a.login for a in pr.assignees],
            "requested_reviewers": [r.login for r in pr.requested_reviewers],
            "created_at": str(pr.created_at),
            "updated_at": str(pr.updated_at),
            "merged_at": str(pr.merged_at) if pr.merged_at else None,
            "closed_at": str(pr.closed_at) if pr.closed_at else None,
            "html_url": pr.html_url,
            "diff_url": pr.diff_url,
        }
    except Exception as e:
        return _error(e)


@mcp.tool
def list_pull_files(
    repo_url: str, number: int, max_results: int = 50
) -> list[dict] | dict:
    """List files changed in a pull request, including patch diffs.

    Args:
        repo_url: Full URL of the repository.
        number: Pull request number.
        max_results: Maximum number of files to return (default 50).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        pr = repo.get_pull(number)
        results = []
        for f in pr.get_files()[:max_results]:
            results.append(
                {
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "changes": f.changes,
                    "patch": f.patch,
                    "blob_url": f.blob_url,
                    "raw_url": f.raw_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


@mcp.tool
def list_pull_comments(
    repo_url: str, number: int, max_results: int = 50
) -> list[dict] | dict:
    """List review comments on a pull request.

    Args:
        repo_url: Full URL of the repository.
        number: Pull request number.
        max_results: Maximum number of comments to return (default 50).
    """
    try:
        ref = _gh.resolve_repo_url(repo_url)
        repo = ref.client.get_repo(f"{ref.owner}/{ref.repo}")
        pr = repo.get_pull(number)
        results = []
        for c in pr.get_review_comments()[:max_results]:
            results.append(
                {
                    "id": c.id,
                    "author": c.user.login if c.user else None,
                    "body": c.body,
                    "path": c.path,
                    "position": c.position,
                    "line": c.line,
                    "side": c.side,
                    "created_at": str(c.created_at),
                    "updated_at": str(c.updated_at),
                    "html_url": c.html_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


# ===================================================================
# File / Code Tools
# ===================================================================


@mcp.tool
def get_file_contents(
    repo_url: str,
    path: str,
    ref: Optional[str] = None,
) -> dict:
    """Get the contents of a file or directory listing from a repository.

    For text files, returns the decoded content. For binary files, returns
    metadata only. For directories, returns a listing of entries.

    Args:
        repo_url: Full URL of the repository.
        path: Path to the file or directory within the repo (e.g. "src/main.py").
        ref: Branch name, tag, or commit SHA. Defaults to the repo's default branch.
    """
    try:
        r = _gh.resolve_repo_url(repo_url)
        repo = r.client.get_repo(f"{r.owner}/{r.repo}")
        kwargs: dict = {}
        if ref:
            kwargs["ref"] = ref

        contents = repo.get_contents(path, **kwargs)

        # Directory listing
        if isinstance(contents, list):
            return {
                "type": "directory",
                "path": path,
                "entries": [
                    {
                        "name": c.name,
                        "path": c.path,
                        "type": c.type,
                        "size": c.size,
                    }
                    for c in contents
                ],
            }

        # Single file
        if contents.encoding == "base64" and contents.content:
            try:
                decoded = base64.b64decode(contents.content).decode("utf-8")
                return {
                    "type": "file",
                    "path": contents.path,
                    "size": contents.size,
                    "encoding": "utf-8",
                    "content": decoded,
                    "sha": contents.sha,
                    "html_url": contents.html_url,
                }
            except UnicodeDecodeError:
                return {
                    "type": "binary_file",
                    "path": contents.path,
                    "size": contents.size,
                    "sha": contents.sha,
                    "download_url": contents.download_url,
                    "html_url": contents.html_url,
                }

        return {
            "type": "file",
            "path": contents.path,
            "size": contents.size,
            "sha": contents.sha,
            "html_url": contents.html_url,
        }
    except Exception as e:
        return _error(e)


@mcp.tool
def get_directory_tree(
    repo_url: str,
    path: str = "",
    ref: Optional[str] = None,
    max_depth: int = 3,
) -> dict:
    """Recursively list the repository file tree for code exploration.

    Returns a nested tree structure up to max_depth levels deep.
    Useful for understanding project layout before reading specific files.

    Args:
        repo_url: Full URL of the repository.
        path: Starting directory path (empty string for repo root).
        ref: Branch name, tag, or commit SHA. Defaults to the repo's default branch.
        max_depth: Maximum depth to recurse (default 3, max 5).
    """
    try:
        r = _gh.resolve_repo_url(repo_url)
        repo = r.client.get_repo(f"{r.owner}/{r.repo}")
        sha = ref or repo.default_branch
        max_depth = min(max_depth, 5)

        # Use the Git Tree API with recursive option for efficiency
        tree = repo.get_git_tree(sha, recursive=True)
        prefix = path.strip("/")

        entries = []
        for item in tree.tree:
            item_path = item.path
            if prefix and not item_path.startswith(prefix + "/") and item_path != prefix:
                continue

            # Calculate relative depth
            rel_path = item_path[len(prefix):].lstrip("/") if prefix else item_path
            depth = rel_path.count("/")
            if depth >= max_depth:
                continue

            entries.append(
                {
                    "path": item_path,
                    "type": "directory" if item.type == "tree" else "file",
                    "size": item.size if item.type == "blob" else None,
                }
            )

        return {
            "repo": f"{r.owner}/{r.repo}",
            "ref": sha,
            "root": path or "/",
            "total_entries": len(entries),
            "entries": entries,
        }
    except Exception as e:
        return _error(e)


# ===================================================================
# Search Tools
# ===================================================================


@mcp.tool
def search_repos(
    query: str,
    server: Optional[str] = None,
    max_results: int = 20,
) -> list[dict] | dict:
    """Search for repositories on a GitHub server.

    Args:
        query: Search query (uses GitHub search syntax).
        server: Server alias (from list_servers). Uses default if omitted.
        max_results: Maximum number of results to return (default 20).
    """
    try:
        client = _gh.get_client(server)
        results = []
        for repo in client.search_repositories(query)[:max_results]:
            results.append(
                {
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "updated_at": str(repo.updated_at),
                    "html_url": repo.html_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


@mcp.tool
def search_code(
    query: str,
    server: Optional[str] = None,
    max_results: int = 20,
) -> list[dict] | dict:
    """Search for code across repositories on a GitHub server.

    Use GitHub search qualifiers like 'repo:', 'language:', 'path:', 'filename:'
    to narrow results. Example: "password repo:owner/repo language:python"

    Args:
        query: Search query (uses GitHub code search syntax).
        server: Server alias (from list_servers). Uses default if omitted.
        max_results: Maximum number of results to return (default 20).
    """
    try:
        client = _gh.get_client(server)
        results = []
        for code in client.search_code(query)[:max_results]:
            results.append(
                {
                    "name": code.name,
                    "path": code.path,
                    "repository": code.repository.full_name,
                    "sha": code.sha,
                    "html_url": code.html_url,
                    "score": code.score if hasattr(code, "score") else None,
                }
            )
        return results
    except Exception as e:
        return _error(e)


@mcp.tool
def search_issues(
    query: str,
    server: Optional[str] = None,
    max_results: int = 20,
) -> list[dict] | dict:
    """Search for issues and pull requests on a GitHub server.

    Use qualifiers like 'repo:', 'is:issue', 'is:pr', 'state:', 'label:'
    to narrow results. Example: "security bug is:issue state:open repo:owner/repo"

    Args:
        query: Search query (uses GitHub issues search syntax).
        server: Server alias (from list_servers). Uses default if omitted.
        max_results: Maximum number of results to return (default 20).
    """
    try:
        client = _gh.get_client(server)
        results = []
        for issue in client.search_issues(query)[:max_results]:
            results.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "repository": issue.repository.full_name,
                    "is_pull_request": issue.pull_request is not None,
                    "author": issue.user.login if issue.user else None,
                    "labels": [l.name for l in issue.labels],
                    "created_at": str(issue.created_at),
                    "html_url": issue.html_url,
                }
            )
        return results
    except Exception as e:
        return _error(e)


# ===================================================================
# Security Tools
# ===================================================================


@mcp.tool
def get_security_overview(repo_url: str) -> dict:
    """Get an aggregated security posture overview of a repository.

    Checks for: dependency manifest files, branch protection on default branch,
    Dependabot alerts counts, CODEOWNERS presence, and security policy.

    Args:
        repo_url: Full URL of the repository.
    """
    try:
        r = _gh.resolve_repo_url(repo_url)
        repo = r.client.get_repo(f"{r.owner}/{r.repo}")
        overview: dict = {
            "repo": repo.full_name,
            "private": repo.private,
            "default_branch": repo.default_branch,
        }

        # Check branch protection on default branch
        try:
            branch = repo.get_branch(repo.default_branch)
            overview["default_branch_protected"] = branch.protected
            if branch.protected:
                prot = branch.get_protection()
                overview["branch_protection"] = {
                    "enforce_admins": prot.enforce_admins.enabled if prot.enforce_admins else False,
                    "required_pull_request_reviews": prot.required_pull_request_reviews is not None,
                    "required_status_checks": prot.required_status_checks is not None,
                }
        except GithubException:
            overview["default_branch_protected"] = "unknown (insufficient permissions)"

        # Check for security-relevant files
        security_files = {
            "SECURITY.md": False,
            "CODEOWNERS": False,
            ".github/CODEOWNERS": False,
            ".github/dependabot.yml": False,
            ".github/dependabot.yaml": False,
        }
        for fpath in security_files:
            try:
                repo.get_contents(fpath)
                security_files[fpath] = True
            except GithubException:
                pass

        overview["security_policy"] = security_files.get("SECURITY.md", False)
        overview["codeowners"] = (
            security_files.get("CODEOWNERS", False)
            or security_files.get(".github/CODEOWNERS", False)
        )
        overview["dependabot_config"] = (
            security_files.get(".github/dependabot.yml", False)
            or security_files.get(".github/dependabot.yaml", False)
        )

        # Check for dependency manifest files
        dep_files = [
            "requirements.txt", "Pipfile", "pyproject.toml",
            "package.json", "pom.xml", "build.gradle", "go.mod",
            "Gemfile", "Cargo.toml", "composer.json",
            "packages.config", "Directory.Packages.props",
        ]
        found_deps = []
        for df in dep_files:
            try:
                repo.get_contents(df)
                found_deps.append(df)
            except GithubException:
                pass
        overview["dependency_files"] = found_deps

        # Try to get Dependabot alert counts via the REST API
        try:
            alerts = repo.get_vulnerability_alert()
            overview["vulnerability_alerts_enabled"] = alerts
        except GithubException:
            overview["vulnerability_alerts_enabled"] = "unknown"

        return overview
    except Exception as e:
        return _error(e)


@mcp.tool
def list_dependabot_alerts(
    repo_url: str,
    state: str = "open",
    severity: Optional[str] = None,
    max_results: int = 30,
) -> list[dict] | dict:
    """List Dependabot vulnerability alerts for a repository.

    Requires the PAT to have the 'security_events' scope or for the repo
    to have Dependabot alerts enabled.

    Args:
        repo_url: Full URL of the repository.
        state: Alert state filter - open, fixed, or dismissed.
        severity: Filter by severity - critical, high, medium, or low.
        max_results: Maximum number of alerts to return (default 30).
    """
    try:
        r = _gh.resolve_repo_url(repo_url)
        # PyGithub doesn't have direct Dependabot alert support,
        # so we use the REST API via the requester
        client = r.client
        headers, data = client._Github__requester.requestJsonAndCheck(
            "GET",
            f"/repos/{r.owner}/{r.repo}/dependabot/alerts",
            parameters={"state": state, "per_page": min(max_results, 100)},
        )

        results = []
        for alert in data[:max_results]:
            vuln = alert.get("security_vulnerability", {})
            advisory = alert.get("security_advisory", {})

            if severity and vuln.get("severity", "").lower() != severity.lower():
                continue

            results.append(
                {
                    "number": alert.get("number"),
                    "state": alert.get("state"),
                    "severity": vuln.get("severity"),
                    "package_name": vuln.get("package", {}).get("name"),
                    "package_ecosystem": vuln.get("package", {}).get("ecosystem"),
                    "vulnerable_version_range": vuln.get("vulnerable_version_range"),
                    "patched_version": (
                        vuln.get("first_patched_version", {}) or {}
                    ).get("identifier"),
                    "advisory_summary": advisory.get("summary"),
                    "advisory_description": advisory.get("description", "")[:500],
                    "cve_id": advisory.get("cve_id"),
                    "cvss_score": (advisory.get("cvss", {}) or {}).get("score"),
                    "cwes": [
                        cwe.get("cwe_id") for cwe in advisory.get("cwes", [])
                    ],
                    "created_at": alert.get("created_at"),
                    "html_url": alert.get("html_url"),
                }
            )
        return results
    except GithubException as e:
        if e.status == 403:
            return {
                "error": True,
                "message": (
                    "Dependabot alerts require the PAT to have 'security_events' "
                    "scope and Dependabot to be enabled on this repository."
                ),
            }
        return _error(e)
    except Exception as e:
        return _error(e)
