---
name: testing-password-reset
description: Test for OWASP A07 Password Reset flaws — predictable tokens, host-header injection in reset link, user-enumeration via response differential.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `mcp-burp`.

Use this skill when the app has a "forgot password" flow that allows users to request a password reset link or token delivered out-of-band (typically via email).

## Signal to look for

- A reset-request endpoint (e.g., `/forgot-password`, `/reset`, `/auth/recover`) that accepts an email address.
- An emailed reset link containing a token (e.g., `?token=abc123` or similar query parameter).
- Differential response between submitting a known-valid email and an invalid email — differences may appear in response body text, content length, HTTP status code, or response time.

## Test steps

1. **User enumeration:** POST a reset request for a known-valid email address, then repeat with an invalid email. Compare the response body, content length, HTTP status code, and response time for any consistent differential that reveals whether an account exists.
2. **Host-header injection:** POST the reset request with the `Host` header overridden to an attacker-controlled domain (e.g., `Host: attacker.com`). Check whether the emailed reset link references the injected host instead of the canonical application domain.
3. **Token predictability:** Request multiple resets in quick succession and collect the resulting tokens. Compare tokens for patterns, sequential increments, timestamp embedding, or other low-entropy characteristics.
4. **Token reuse:** Consume a valid reset token to complete a password reset, then immediately submit the same token again. Observe whether the second submission is rejected or accepted.
5. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell — host-header injection probe:**

```bash
curl -X POST -H "Host: attacker.com" --data 'email=victim@target.com' https://target.example.com/reset
# Success: emailed reset link references attacker.com
```

**MCP — replay injected request via Burp Repeater:**

```
burp_repeater_send(raw_base64=<b64 with injected Host>, host="target.example.com", port=443, secure=true, tab_name="reset-probe")
```

Expected envelope:

```json
{"ok": true, "status": 200, "body": "..."}
```

**MCP — review proxy history for enumeration differential:**

```
burp_proxy_history(host="target.example.com", contains="reset")
```

Expected envelope:

```json
{"ok": true, "items": [...]}
```

Review the returned items for response-length or body-content differences between the valid-email and invalid-email requests.

## Interpret results

- **Host-header link hijack confirmed** when the emailed reset link contains the attacker-controlled host instead of the legitimate application domain — meaning a victim who clicks the link sends their reset token to the attacker's server.
- **User enumeration confirmed** when there is a consistent, reproducible differential (different body text, different content length, different status code, or measurably different response time) between the valid-email and invalid-email reset requests.
- **Token reuse confirmed** when a second submission of an already-consumed reset token succeeds in resetting the password again, indicating the token was not invalidated after first use.

## Finding writeup

- **Title:** `Password Reset <issue> at <endpoint>` (e.g., `Password Reset Host-Header Injection at /reset`).
- **Severity:**
  - Reset-token account takeover: Critical
  - Host-header link hijack: Critical
  - User enumeration via response differential: Low-Medium
- **Evidence** per `methodology-evidence-capture`: include the HTTP request (with injected header or differential payload), the HTTP response, and a redacted excerpt of the emailed reset link showing the injected host or token. Redact victim email addresses and any personal information.
- **Fix:**
  - Bind reset tokens to the requesting account and invalidate them on first use.
  - Generate tokens with cryptographically secure randomness and sufficient entropy (minimum 128 bits).
  - Always construct reset links from a canonical base URL configured server-side — never trust the `Host` request header for URL generation.
  - Return identical responses (body, length, status, and timing) for both valid and invalid email submissions to prevent user enumeration.

## References

- OWASP WSTG ATHN-09 (Weaker Authentication in Alternative Channel): `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/09-Testing_for_Weaker_Authentication_in_Alternative_Channel`
- PortSwigger Authentication: `https://portswigger.net/web-security/authentication`
- CWE-640: `https://cwe.mitre.org/data/definitions/640.html`

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
