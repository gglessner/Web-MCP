"""Entry point for `python -m github_mcp` or `python -m MCPs.github_mcp`."""

from .server import mcp

if __name__ == "__main__":
    mcp.run()
