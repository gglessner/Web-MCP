# Attack-Technique Skills — Design

**Date:** 2026-04-17
**Author:** Garland Glessner (gglessner@gmail.com)
**Status:** Approved for planning
**Sub-project:** 4 of 5 in the Web-MCP skill-library track

## Purpose

Produce thirty `testing-*` skills — one per web-app attack technique — that teach Claude how to run, interpret, and document each attack class during an authorized penetration test. The skills plug into the methodology (scoping, RoE, phases, evidence-capture) laid down by sub-project 3 and consume the MCP-server usage skills from sub-project 2. Together they cover OWASP 2021 Top 10 plus high-frequency adjacent techniques used in real engagements.

## Non-goals

- No reporting or deliverable skills (sub-project 5).
- No chain/decision-tree wiring between testing-* skills (each stands alone; "see also" links may be layered in later).
- No specific forward references to unwritten `reporting-*` skills — severity guidance stays inline.
- No scripts/ subdirectories for payload libraries — payloads inlined in `## Tool commands` where concise, referenced by external link where not.
- No distinct plans per batch — one plan, three internal batches with checkpoints.

## Deliverables

Thirty files under `.claude/skills/`, flat at the top level:

```
.claude/skills/
# Injection family (10)
├── testing-sqli/SKILL.md
├── testing-nosqli/SKILL.md
├── testing-command-injection/SKILL.md
├── testing-xss-reflected/SKILL.md
├── testing-xss-stored/SKILL.md
├── testing-xss-dom/SKILL.md
├── testing-ssti/SKILL.md
├── testing-xxe/SKILL.md
├── testing-header-injection/SKILL.md
├── testing-ldap-injection/SKILL.md
# Access Control (5)
├── testing-idor/SKILL.md
├── testing-missing-function-access/SKILL.md
├── testing-privilege-escalation/SKILL.md
├── testing-path-traversal/SKILL.md
├── testing-csrf/SKILL.md
# Auth & Session (4)
├── testing-auth-bypass/SKILL.md
├── testing-session-management/SKILL.md
├── testing-jwt/SKILL.md
├── testing-password-reset/SKILL.md
# Server-side (4)
├── testing-ssrf/SKILL.md
├── testing-deserialization/SKILL.md
├── testing-file-upload/SKILL.md
├── testing-open-redirect/SKILL.md
# Protocol-level (2)
├── testing-request-smuggling/SKILL.md
├── testing-cache-poisoning/SKILL.md
# Client-side (3)
├── testing-cors/SKILL.md
├── testing-clickjacking/SKILL.md
├── testing-prototype-pollution/SKILL.md
# Other (2)
├── testing-graphql/SKILL.md
└── testing-sensitive-data-exposure/SKILL.md
```

**Target body lengths:** ~200-250 lines per skill; 400-line hard cap per conventions.

Each follows the 8-section template locked in by sub-project 1 (`docs/skill-conventions.md`).

## Skill template (applies to all 30)

**Frontmatter:**

```yaml
---
name: testing-<attack>
description: <one-line action phrase — what this tests — including an OWASP 2021 A-category tag>
---
```

Description rules:
- ≤ 175 characters for headroom.
- Third-person action phrase, as in prior sub-projects.
- OWASP 2021 category tag where applicable. Example: `Test for OWASP A03 SQL Injection — error-based, blind, UNION, and time-based — via Burp Repeater and sqlmap.`
- Where an attack class doesn't cleanly map to one OWASP category (e.g., `testing-header-injection`), the tag is dropped or replaced with a descriptive label (e.g., "OWASP Top 10 adjacent").

**Body — 8 H2 sections in canonical order:**

1. `## When to use` — opens with `Prerequisite skills: <list>.` on its own line. Skill names in backticks. List includes: `methodology-scoping`, `methodology-rules-of-engagement`, relevant `recon-*` skill(s), and relevant `mcp-*` skill(s). Then a paragraph on when the attack applies.
2. `## Signal to look for` — bullets: request/response patterns, input-handling tells, framework signatures that suggest the attack may succeed.
3. `## Test steps` — numbered runbook: probe → confirm → escalate → document. Tool invocations in fenced code blocks. Every invasive step cross-references `methodology-rules-of-engagement`.
4. `## Tool commands` — hybrid:
   - **Shell block** with the canonical external tool (sqlmap, dalfox, nuclei template, etc.), including a `# Success:` comment.
   - **MCP block** with the corresponding Burp/browser MCP tool calls. Every signature verified against the authoritative `.claude/skills/mcp-*/SKILL.md`.
5. `## Interpret results` — confirmation signals, false-positive traps, WAF/filter interference, severity considerations.
6. `## Finding writeup` — title pattern, severity guidance (Critical/High/Medium/Low with explicit triggers), description template, evidence per `methodology-evidence-capture`, suggested fix.
7. `## References` — exactly three to five links: the relevant OWASP WSTG section, the PortSwigger Web Security Academy topic (if one exists), the relevant CWE (e.g., `https://cwe.mitre.org/data/definitions/89.html` for SQLi), and tool docs (e.g., sqlmap wiki).
8. `## Authorization note` — the verbatim standard paragraph.

### Fixed conventions (from sub-project 3 lessons)

- American English in the body. Frontmatter `description` may retain OWASP-spelling verbatim.
- Glob skill-name references (`methodology-*`, `recon-*`, `testing-*`, `reporting-*`, `mcp-*`) inside backticks — never inside italic delimiters — so markdown does not eat the asterisks.
- MCP tool signatures must match the exact parameter names in the authoritative `.claude/skills/mcp-*/SKILL.md`. No invented names. `get_file_contents` (not `github_get_file_contents`). `burp_scope_modify` always includes both `add=` and `remove=`.
- Authorization note is a plain paragraph, not a blockquote.
- The authorization caveat appears only in `## Authorization note`, never restated elsewhere.

## Per-skill content

The bulk per-skill detail lives in the implementation plan; the spec captures the distinguishing points (description draft, primary recon prerequisite, tool choices, severity-guidance anchors).

### Injection family

**testing-sqli**
- **Description:** `Test for OWASP A03 SQL Injection — error-based, blind, UNION, and time-based — via Burp Repeater and sqlmap.`
- **Prereqs:** `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `recon-content-discovery`, `mcp-burp`.
- **Canonical tool:** `sqlmap -u <url> --batch --risk=1 --level=2`.
- **MCP:** `burp_repeater_send` with crafted SQL payload; `burp_proxy_history(contains="' OR ")` to correlate.
- **Severity anchors:** unauthenticated data extraction = Critical; authenticated = High; blind-only with limited extraction = Medium.
- **References:** OWASP WSTG INPV-05, PortSwigger SQLi, CWE-89, sqlmap wiki.

**testing-nosqli**
- **Description:** `Test for OWASP A03 NoSQL Injection against MongoDB, CouchDB, and similar stores via operator-syntax and JS-injection payloads.`
- **Prereqs:** as above, `recon-api-enum` primary.
- **Canonical tool:** manual payloads through Burp Repeater; optional `NoSQLMap`.
- **MCP:** `burp_repeater_send` with `{"$ne": null}` or `{"$gt": ""}` style payloads.
- **Severity anchors:** authentication bypass = Critical; authenticated enumeration = Medium-High.
- **References:** OWASP WSTG INPV-05 §NoSQL, PortSwigger NoSQL, CWE-943.

**testing-command-injection**
- **Description:** `Test for OWASP A03 OS Command Injection in user-controlled inputs flowing to shell execution — including blind via time delay.`
- **Prereqs:** `recon-api-enum`, `recon-content-discovery`, `mcp-burp`.
- **Canonical tool:** Burp Repeater with payloads like `; sleep 10 #`, `` `sleep 10` ``, `| curl <callback>`; commix for automation.
- **MCP:** `burp_repeater_send` with time-delay payloads; measure round-trip time.
- **Severity anchors:** RCE confirmed = Critical; blind without extracted data = High.
- **References:** OWASP WSTG INPV-12, PortSwigger OS command injection, CWE-78.

**testing-xss-reflected**
- **Description:** `Test for OWASP A03 Reflected XSS in query-string, URL-path, and form-parameter reflection points.`
- **Prereqs:** `recon-content-discovery`, `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`.
- **Canonical tool:** dalfox, XSStrike, or manual Burp Repeater payloads; `browser_navigate` + `browser_eval` to confirm execution.
- **MCP:** `burp_repeater_send` with `<svg/onload=...>`, `"><script>...</script>`; `browser_eval("!!document.querySelector('svg[onload]')")`.
- **Severity anchors:** authenticated-origin JS execution = High; one-click impact (SSO token steal) = Critical.
- **References:** OWASP WSTG CLNT-01, PortSwigger XSS, CWE-79.

**testing-xss-stored**
- **Description:** `Test for OWASP A03 Stored XSS in persistent inputs (comments, profile fields, filenames, review fields).`
- **Prereqs:** `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`.
- **Canonical tool:** manual submission via Burp Repeater, confirm rendering via `browser_navigate` + `browser_eval`.
- **MCP:** `burp_repeater_send` (submit) + `browser_navigate` (view) + `browser_eval` (confirm JS ran).
- **Severity anchors:** persistent cross-user execution = Critical.
- **References:** OWASP WSTG CLNT-02, PortSwigger Stored XSS, CWE-79.

**testing-xss-dom**
- **Description:** `Test for OWASP A03 DOM-based XSS — sinks executing attacker-controlled input without server round-trip.`
- **Prereqs:** `recon-js-analysis` (primary), `recon-sitemap-crawl`, `mcp-browser`.
- **Canonical tool:** DOM Invader (Burp Pro extension), manual `browser_eval` probes.
- **MCP:** `browser_eval("location.hash='<payload>'; ...")`; `browser_network_log` to confirm no server round-trip.
- **Severity anchors:** same as reflected.
- **References:** OWASP WSTG CLNT-03, PortSwigger DOM XSS, CWE-79.

**testing-ssti**
- **Description:** `Test for OWASP A03 Server-Side Template Injection against Jinja2, Twig, Freemarker, Smarty, ERB, and similar engines.`
- **Prereqs:** `recon-tech-fingerprinting` (to know the engine), `mcp-burp`.
- **Canonical tool:** tplmap, manual payloads (`{{7*7}}`, `${7*7}`, `<%= 7*7 %>`).
- **MCP:** `burp_repeater_send` with engine-specific payloads; response body should reflect evaluated expression.
- **Severity anchors:** RCE via template = Critical; confirmed code evaluation without RCE = High.
- **References:** OWASP WSTG INPV-18, PortSwigger SSTI, CWE-94.

**testing-xxe**
- **Description:** `Test for OWASP A03 XML External Entity injection — SOAP, XML-uploading endpoints, and XML-serialized APIs.`
- **Prereqs:** `recon-api-enum`, `recon-content-discovery`, `mcp-burp`.
- **Canonical tool:** manual Burp Repeater with XXE payloads; OOB via Burp Collaborator (Pro) or interactsh.
- **MCP:** `burp_repeater_send` with `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>`; read response for file contents.
- **Severity anchors:** file read = High; OOB data exfil = High; RCE (rare) = Critical.
- **References:** OWASP WSTG INPV-07, PortSwigger XXE, CWE-611.

**testing-header-injection**
- **Description:** `Test for HTTP Header Injection — CRLF, host-header injection, cache-key injection — affecting response splitting and routing.`
- **Prereqs:** `recon-sitemap-crawl`, `mcp-burp`.
- **Canonical tool:** manual Burp Repeater with `\r\n`-encoded payloads, `Host:` manipulation.
- **MCP:** `burp_repeater_send` with injected CRLF; `burp_proxy_history` to compare baseline vs. injected response.
- **Severity anchors:** response splitting enabling XSS = High; cache poisoning = High; reflected host = Medium.
- **References:** OWASP WSTG INPV-15, PortSwigger HTTP host header attacks, CWE-93.

**testing-ldap-injection**
- **Description:** `Test for OWASP A03 LDAP Injection in auth forms and directory-query endpoints.`
- **Prereqs:** `recon-api-enum`, `mcp-burp`.
- **Canonical tool:** manual Burp Repeater with `*)(uid=*))(|(uid=*` payloads.
- **MCP:** `burp_repeater_send` with LDAP wildcard payloads; success on auth bypass = different response body.
- **Severity anchors:** auth bypass = Critical; blind enumeration = Medium.
- **References:** OWASP WSTG INPV-06, PortSwigger LDAP injection (note: academy coverage is limited), CWE-90.

### Access Control

**testing-idor**
- **Description:** `Test for OWASP A01 IDOR / BOLA — direct object references accessible without authorization check.`
- **Prereqs:** `recon-api-enum`, `recon-sitemap-crawl`, `mcp-burp`.
- **Canonical tool:** manual Burp Repeater with id mutation (incrementing, decrementing, UUIDs swap); match-replace rules for session substitution.
- **MCP:** `burp_match_replace_set` to swap session cookies between accounts; `burp_repeater_send` to re-issue.
- **Severity anchors:** unauthenticated access = Critical; cross-user read = High; cross-user write = High-Critical.
- **References:** OWASP WSTG ATHZ-04, PortSwigger IDOR, CWE-639.

**testing-missing-function-access**
- **Description:** `Test for OWASP A01 Missing Function-Level Access Control — forced browsing to admin/privileged endpoints without checks.`
- **Prereqs:** `recon-content-discovery`, `recon-api-enum`, `mcp-burp`.
- **Canonical tool:** ffuf with role-specific wordlists; manual enumeration via Burp sitemap.
- **MCP:** `burp_sitemap(prefix=...)` → request each admin endpoint as low-priv user; observe 200 vs 403.
- **Severity anchors:** admin access via low-priv = Critical.
- **References:** OWASP WSTG ATHZ-02, PortSwigger Access Control, CWE-284.

**testing-privilege-escalation**
- **Description:** `Test for OWASP A01 Privilege Escalation — horizontal (peer user) and vertical (role uplift) via parameter tampering and role-assignment endpoints.`
- **Prereqs:** `recon-api-enum`, `recon-sitemap-crawl`, `mcp-burp`.
- **Canonical tool:** manual Burp Repeater with role parameter tampering (`role=admin`), privilege-assignment API abuse.
- **MCP:** `burp_repeater_send` with tampered role/ownership parameters; compare responses for peer accounts.
- **Severity anchors:** role uplift to admin = Critical; horizontal peer access = High.
- **References:** OWASP WSTG ATHZ-03, PortSwigger Access Control, CWE-269.

**testing-path-traversal**
- **Description:** `Test for OWASP A01 Path Traversal / LFI in file-serving parameters — ../, encoded variants, null-byte bypass.`
- **Prereqs:** `recon-content-discovery`, `mcp-burp`.
- **Canonical tool:** manual payloads (`../../../../etc/passwd`, URL-encoded `%2e%2e%2f`, null `%00`), ffuf with traversal wordlists.
- **MCP:** `burp_repeater_send` with traversal payloads; compare response to the expected static file.
- **Severity anchors:** arbitrary file read = High; source-code disclosure = High; `/etc/passwd` style sensitive file = High.
- **References:** OWASP WSTG ATHZ-01, PortSwigger Directory traversal, CWE-22.

**testing-csrf**
- **Description:** `Test for OWASP A01 CSRF — missing anti-CSRF tokens, SameSite misconfiguration, GET-based state changes.`
- **Prereqs:** `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`.
- **Canonical tool:** Burp CSRF PoC generator (Pro); manual cross-origin form submission via a test page.
- **MCP:** `burp_repeater_send` without CSRF token; `browser_navigate` to hosted PoC to confirm cross-origin exploitability.
- **Severity anchors:** state change on sensitive action = High; auth change = Critical.
- **References:** OWASP WSTG SESS-05, PortSwigger CSRF, CWE-352.

### Auth & Session

**testing-auth-bypass**
- **Description:** `Test for OWASP A07 Authentication Bypass — parameter tampering, forced-browsing of post-auth pages, SQL-injection-in-auth.`
- **Prereqs:** `recon-sitemap-crawl`, `mcp-burp`.
- **Canonical tool:** manual Burp Repeater bypass probes.
- **MCP:** `burp_repeater_send` with tampered auth parameters; `browser_navigate` to post-auth page without login.
- **Severity anchors:** full bypass = Critical; bypass with limited impact = High.
- **References:** OWASP WSTG ATHN-01..04, PortSwigger Authentication, CWE-287.

**testing-session-management**
- **Description:** `Test for OWASP A07 Session Management flaws — predictable IDs, missing rotation, fixation, weak cookie flags, missing expiry.`
- **Prereqs:** `recon-sitemap-crawl`, `mcp-burp`.
- **Canonical tool:** manual analysis of cookie flags (Secure, HttpOnly, SameSite) via `curl -I`; Burp Sequencer (Pro) for predictability.
- **MCP:** `burp_proxy_history(contains="Set-Cookie")`; `burp_proxy_request(id=<N>)` to inspect raw Set-Cookie headers.
- **Severity anchors:** session fixation = High; predictable session IDs = High; missing Secure flag = Medium.
- **References:** OWASP WSTG SESS-01..09, PortSwigger Sessions, CWE-384/614.

**testing-jwt**
- **Description:** `Test for OWASP A07 JWT flaws — algorithm confusion (alg:none, HS256/RS256 swap), weak signing, kid path traversal, exp bypass.`
- **Prereqs:** `recon-sitemap-crawl`, `mcp-burp`.
- **Canonical tool:** `jwt_tool`, manual Burp Repeater with rewritten tokens.
- **MCP:** `burp_repeater_send` with tampered JWT; inspect response for acceptance.
- **Severity anchors:** alg:none or signing-key exposure = Critical; algorithm confusion = Critical; weak secret = High.
- **References:** OWASP WSTG SESS-10, PortSwigger JWT attacks, CWE-347.

**testing-password-reset**
- **Description:** `Test for OWASP A07 Password Reset flaws — predictable tokens, host-header injection in reset link, user-enumeration via response differential.`
- **Prereqs:** `recon-sitemap-crawl`, `mcp-burp`.
- **Canonical tool:** manual flow walking via Burp Repeater.
- **MCP:** `burp_repeater_send` with tampered reset-request host header; `burp_proxy_history` to compare success/failure responses for enumeration.
- **Severity anchors:** reset-token takeover = Critical; host-header link hijack = Critical; enumeration = Low-Medium.
- **References:** OWASP WSTG ATHN-09, PortSwigger Authentication, CWE-640.

### Server-side

**testing-ssrf**
- **Description:** `Test for OWASP A10 SSRF — cloud metadata, internal services, file:// and gopher:// protocol abuse.`
- **Prereqs:** `recon-api-enum`, `mcp-burp`.
- **Canonical tool:** Burp Collaborator (Pro) or interactsh for OOB; manual payloads targeting `http://169.254.169.254/latest/meta-data/`, `file:///etc/passwd`, `http://localhost:<port>/`.
- **MCP:** `burp_repeater_send` with SSRF payloads; `burp_collaborator` or OOB observation.
- **Severity anchors:** cloud metadata read = Critical; internal service access = High; DNS callback only = Medium.
- **References:** OWASP WSTG SSRF (new section, 2021), PortSwigger SSRF, CWE-918.

**testing-deserialization**
- **Description:** `Test for OWASP A08 Insecure Deserialization — Java (ysoserial), .NET (ysoserial.net), Python pickle, PHP serialize, Node.js.`
- **Prereqs:** `recon-tech-fingerprinting`, `recon-js-analysis`, `mcp-burp`.
- **Canonical tool:** `ysoserial`, `ysoserial.net`, manual PHP-serialize payloads.
- **MCP:** `burp_repeater_send` with serialized payload replacing the legitimate one; OOB via Collaborator/interactsh for confirmation.
- **Severity anchors:** RCE confirmed = Critical; DoS-only = High.
- **References:** OWASP WSTG INPV-11, PortSwigger Deserialization, CWE-502.

**testing-file-upload**
- **Description:** `Test for OWASP A01/A04 File Upload vulnerabilities — extension bypass, MIME spoofing, polyglot, path traversal via filename.`
- **Prereqs:** `recon-content-discovery`, `mcp-burp`.
- **Canonical tool:** manual upload via Burp Repeater with crafted filenames (`shell.php.jpg`, `shell.phtml`), double-extension, null-byte, content-type spoof.
- **MCP:** `burp_repeater_send` with multipart upload; `browser_navigate` to the uploaded path to confirm execution.
- **Severity anchors:** RCE via uploaded web shell = Critical; overwrite via path traversal = High; stored XSS via upload = High.
- **References:** OWASP WSTG BUSL-09/INPV-03, PortSwigger File upload, CWE-434.

**testing-open-redirect**
- **Description:** `Test for Open Redirect in login-next, SSO-return-to, and download parameters — enables phishing and SSRF pivots.`
- **Prereqs:** `recon-api-enum`, `mcp-burp`.
- **Canonical tool:** manual Burp Repeater with redirect-parameter mutations (absolute URL, scheme-less, userinfo, null).
- **MCP:** `burp_repeater_send` with redirect payload; inspect `Location:` header.
- **Severity anchors:** SSO-phishing facilitator = Medium-High; pure UX redirect = Low.
- **References:** OWASP WSTG CLNT-04, PortSwigger Redirect, CWE-601.

### Protocol-level

**testing-request-smuggling**
- **Description:** `Test for HTTP Request Smuggling (desync) — CL.TE, TE.CL, TE.TE variants against front-end/back-end chains.`
- **Prereqs:** `recon-tech-fingerprinting`, `mcp-burp`.
- **Canonical tool:** Burp "HTTP Request Smuggler" extension; manual Burp Repeater with carefully-crafted CL/TE headers.
- **MCP:** `burp_repeater_send` with smuggled payload; confirm via second-request poisoning.
- **Severity anchors:** confirmed smuggling = Critical; suspected without confirmation = High.
- **References:** OWASP WSTG Request smuggling, PortSwigger HTTP request smuggling (canonical), CWE-444.

**testing-cache-poisoning**
- **Description:** `Test for Web Cache Poisoning — unkeyed-input reflection, cache-key manipulation, cache deception.`
- **Prereqs:** `recon-tech-fingerprinting`, `mcp-burp`.
- **Canonical tool:** Burp "Param Miner" extension (for unkeyed-input discovery); manual probing.
- **MCP:** `burp_repeater_send` with candidate unkeyed headers; re-fetch without the header to confirm persisted response.
- **Severity anchors:** persistent XSS via cache = Critical; DoS-only = High.
- **References:** OWASP WSTG Cache (2021 addition), PortSwigger Web cache poisoning, CWE-349 (Acceptance of Extraneous Untrusted Data).

### Client-side

**testing-cors**
- **Description:** `Test for OWASP A05 CORS misconfiguration — wildcard origin with credentials, reflected origin, null origin, subdomain trust.`
- **Prereqs:** `recon-js-analysis`, `recon-sitemap-crawl`, `mcp-burp`.
- **Canonical tool:** manual Burp Repeater with mutated `Origin:` header; hosted PoC page for confirmation.
- **MCP:** `burp_repeater_send` with crafted `Origin:`; inspect `Access-Control-Allow-Origin` + `Access-Control-Allow-Credentials`.
- **Severity anchors:** authenticated cross-origin read with credentials = High-Critical; reflective origin without credentials = Medium.
- **References:** OWASP WSTG CLNT-07, PortSwigger CORS, CWE-942.

**testing-clickjacking**
- **Description:** `Test for Clickjacking — missing X-Frame-Options or frame-ancestors CSP directive on sensitive state-changing pages.`
- **Prereqs:** `recon-sitemap-crawl`, `mcp-browser`.
- **Canonical tool:** manual PoC HTML with iframe; `curl -I` to inspect frame-protection headers.
- **MCP:** `browser_navigate` to hosted PoC frame of the target; visual confirmation via `browser_screenshot`.
- **Severity anchors:** UI-redress on auth action = Medium-High; on static page = Low.
- **References:** OWASP WSTG CLNT-09, PortSwigger Clickjacking, CWE-1021.

**testing-prototype-pollution**
- **Description:** `Test for Prototype Pollution in Node.js and client-side JS — source/sink analysis, gadget identification, payload delivery.`
- **Prereqs:** `recon-js-analysis`, `recon-sitemap-crawl`, `mcp-browser`.
- **Canonical tool:** DOM Invader prototype-pollution mode (Burp Pro); manual `browser_eval` probes.
- **MCP:** `browser_eval("Object.prototype.polluted=true; <trigger>")`; inspect for gadget execution.
- **Severity anchors:** XSS via gadget chain = High; DoS or logic bypass = Medium.
- **References:** PortSwigger Prototype pollution (primary), OWASP WSTG CLNT-13, CWE-1321.

### Other

**testing-graphql**
- **Description:** `Test for GraphQL-specific flaws — introspection leakage, batching abuse, alias-based rate-limit bypass, field duplication, deep-query DoS.`
- **Prereqs:** `recon-api-enum`, `mcp-burp`.
- **Canonical tool:** `graphql-voyager` (schema exploration), manual Burp Repeater crafted queries.
- **MCP:** `burp_repeater_send` with introspection, alias-stacked, or deeply-nested queries.
- **Severity anchors:** auth-bypass via alias/field duplication = High-Critical; introspection leak = Medium; deep-query DoS = Medium.
- **References:** OWASP API Security Top 10 (API8: Lack of Resources & Rate Limiting), PortSwigger GraphQL, CWE-863 (Incorrect Authorization) for alias/field auth-bypass cases.

**testing-sensitive-data-exposure**
- **Description:** `Test for OWASP A02 Sensitive Data Exposure in responses — PII, tokens, credentials, stack traces, debug output.`
- **Prereqs:** `recon-sitemap-crawl`, `recon-content-discovery`, `mcp-burp`.
- **Canonical tool:** Burp "Hunt Methodology" or regex-based grep over `burp_proxy_history`; TruffleHog patterns.
- **MCP:** `burp_proxy_history(contains="Authorization:")`, `burp_proxy_history(contains="BEGIN RSA")`, etc.
- **Severity anchors:** credentials leaked = Critical; PII = High; stack traces with path disclosure = Low-Medium.
- **References:** OWASP WSTG INFO-05, PortSwigger Information disclosure, CWE-200.

## Cross-reference map

Approach A from sub-project 3 continues here: testing-* skills declare `methodology-*` and `mcp-*` and `recon-*` prerequisites in `## When to use`, reference `methodology-evidence-capture` in `## Finding writeup`, but do NOT cross-reference peer testing-* skills. A later pass can add "see also" links once all thirty exist.

Every cross-reference uses the skill name inside backticks, never a path.

## Tool-commands style (hybrid)

Each testing-* skill's `## Tool commands` contains two fenced blocks:

- **Shell:** the canonical external-tool invocation (sqlmap, dalfox, ysoserial, jwt_tool, ffuf, nuclei, etc.), with a `# Success:` or `# Failure:` comment indicating the expected observable.
- **MCP:** the equivalent or follow-up Burp/browser MCP call, with the expected response envelope (`{"ok": true, "data": {...}}`).

Both blocks are required for every testing-* skill. Where a specific attack has no MCP equivalent beyond generic `burp_repeater_send`, the MCP block shows exactly that call with a concrete example payload.

## Authorization stance

All thirty testing-* skills end with the standard authorization paragraph verbatim (as a plain paragraph, no blockquote):

> Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.

Every skill's `## Test steps` includes an explicit reference to `methodology-rules-of-engagement` on any step that could be invasive (payload injection, POST with mutated data, automated scanning), so Claude is reminded to verify RoE before acting.

## Quality bar

Per `docs/skill-conventions.md`:

- [ ] Directory name matches `name:` frontmatter.
- [ ] Frontmatter has exactly two fields (`name`, `description`); description ≤ 175 characters.
- [ ] All 8 H2 sections present in canonical order.
- [ ] At least one Shell command AND at least one MCP tool call in `## Tool commands`.
- [ ] Authorization paragraph verbatim, plain paragraph.
- [ ] External links in `## References` resolve at commit time.
- [ ] `SKILL.md` under ~400 lines; target 200-250.

Additional sub-project 4 constraints:

- [ ] OWASP 2021 A-category tag present in description where the attack cleanly maps to one category.
- [ ] Prerequisite line at the top of `## When to use` lists the correct `methodology-*`, `recon-*`, and `mcp-*` skills per the cross-reference map.
- [ ] No specific forward reference to unwritten `reporting-*` skills.
- [ ] No peer testing-* cross-references in this sub-project.

## Discoverability & testing

Claude Code auto-discovers each skill via `.claude/skills/*/SKILL.md` on session start. Manual smoke tests (one per attack family, run after the full sub-project is merged):

- "The login form is rejecting `' OR 1=1 --` — what should I try next?" → surfaces `testing-sqli` or `testing-nosqli`.
- "This SPA has a search parameter that reflects into the DOM — how do I confirm XSS?" → surfaces `testing-xss-dom`.
- "Can I read `/etc/passwd` via this file-download endpoint?" → surfaces `testing-path-traversal`.
- "The JWT starts with `eyJhbGciOiJub25lIn0` — is that exploitable?" → surfaces `testing-jwt`.
- "The app fetches URLs server-side from a `url=` parameter. How do I probe for SSRF?" → surfaces `testing-ssrf`.
- "There's a `Location:` header with a user-controlled value. Can I make it redirect to evil.com?" → surfaces `testing-open-redirect`.
- "The file-upload endpoint checks Content-Type but not extension. Can I upload a web shell?" → surfaces `testing-file-upload`.
- "The `Origin:` header is reflected verbatim with `Access-Control-Allow-Credentials: true`. How bad is that?" → surfaces `testing-cors`.

## Commit strategy

Thirty atomic `feat(skills):` commits in batch order plus fix commits as needed:

**Batch 1 — Injection family (10 commits):** testing-sqli → testing-nosqli → testing-command-injection → testing-xss-reflected → testing-xss-stored → testing-xss-dom → testing-ssti → testing-xxe → testing-header-injection → testing-ldap-injection.

**Batch 2 — Access Control + Auth (9 commits):** testing-idor → testing-missing-function-access → testing-privilege-escalation → testing-path-traversal → testing-csrf → testing-auth-bypass → testing-session-management → testing-jwt → testing-password-reset.

**Batch 3 — Server-side, Protocol, Client, Other (11 commits):** testing-ssrf → testing-deserialization → testing-file-upload → testing-open-redirect → testing-request-smuggling → testing-cache-poisoning → testing-cors → testing-clickjacking → testing-prototype-pollution → testing-graphql → testing-sensitive-data-exposure.

Checkpoints between batches: controller reports the batch's commit SHAs to the user; user can review/adjust before the next batch begins.

A single plan covers all thirty tasks plus one final verification task (31 total).

## Out of scope

- Reporting / deliverables (`reporting-*`) — sub-project 5.
- Scripts/ payload-file subdirectories — payloads inline or external-linked.
- Chain/decision-tree peer references between testing-* skills — later pass.
- Specific forward references to unwritten reporting-* skills.
- Burp Pro–only extension coverage beyond a one-line mention (Param Miner, DOM Invader, HTTP Request Smuggler are referenced but not required).
- Automated plugin packaging — skills drop into `.claude/skills/` alongside existing files.
- Non-HTTP protocol testing (that is what `mcp-parley` covers, and no testing-* skill in this sub-project targets raw TCP / FIX / ISO 8583).

## Acceptance criteria

1. All thirty `SKILL.md` files exist at the paths in the Deliverables section.
2. Each passes the quality-bar checklist above.
3. Cross-references follow the map; names only, no paths.
4. Descriptions include OWASP A-category tags where applicable.
5. Manual smoke-test prompts each surface the intended skill when Claude Code is launched in the repo root.
6. Spec committed to `docs/superpowers/specs/2026-04-17-testing-skills-design.md`.
7. Thirty atomic `feat(skills):` commits in batch order; fix commits interleaved as needed.
8. Final verification task (Task 31 in the plan) runs a name/description/section/auth/cross-ref sweep across all thirty and is clean.
