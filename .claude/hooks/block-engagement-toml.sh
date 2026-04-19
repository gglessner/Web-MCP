#!/usr/bin/env bash
# PreToolUse hook: deny direct reads of engagement.toml. The model should use
# the engagement_info MCP tool instead. Exit 2 = block (stderr is the reason).
input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // empty')
case "$tool" in
  Read)
    path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
    [[ "$path" == *engagement.toml ]] && {
      echo "engagement.toml contains credentials. Use the engagement_info MCP tool instead." >&2
      exit 2
    }
    ;;
  Grep)
    path=$(printf '%s' "$input" | jq -r '.tool_input.path // empty')
    [[ "$path" == *engagement.toml* ]] && {
      echo "engagement.toml contains credentials. Use the engagement_info MCP tool instead." >&2
      exit 2
    }
    ;;
  Bash)
    cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
    if printf '%s' "$cmd" | grep -q 'engagement\.toml'; then
      echo "Bash commands referencing engagement.toml are blocked. Use the engagement_info MCP tool instead." >&2
      exit 2
    fi
    ;;
esac
exit 0
