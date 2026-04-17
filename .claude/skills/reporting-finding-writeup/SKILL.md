---
name: reporting-finding-writeup
description: Write a single web pentest finding — title, severity, description, impact, reproduction steps, evidence references, remediation — from captured artifacts.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-evidence-capture`, `reporting-severity-rubric`.

Use this skill per confirmed finding, after evidence is captured and severity is rated.

## Signal to look for

- Confirmed positive from any `testing-*` skill with evidence satisfying `methodology-evidence-capture`.
- Need to hand off a single finding for review or aggregation into `reporting-deliverable-report`.

## Test steps

1. Populate the canonical 7-section finding template (shown in `## Tool commands`).
2. Apply `reporting-severity-rubric` to fix the severity (CVSS vector + qualitative band).
3. Ensure reproduction steps are numbered MCP tool calls per `methodology-evidence-capture`.
4. Link evidence files by relative path within the engagement directory.
5. Redact sensitive data (real credentials, real PII) before delivery.
6. Run a peer-review pass for language and accuracy.

## Tool commands

**Canonical 7-section finding template:**

```
# [Severity] — [Title]

**Severity:** [Band] ([CVSS:3.1/...])

## Description
[1-paragraph technical summary of what is wrong and where.]

## Impact
[1-paragraph business framing — what an attacker can do, what assets
are at risk, what compliance implications apply.]

## Reproduction
1. [Step 1 — MCP or shell call, copy-pasteable]
2. [Step 2]
...

## Evidence
- [request.http] — raw HTTP request
- [response.http] — raw HTTP response
- [screenshot.png] — rendered state after exploitation
- [source.md] — source-code references (repo + SHA + line range)

## Remediation
[Concrete code/config change. Not "sanitize inputs" — show the patch.]
```

---

**Worked example 1 — SQL Injection**

```
# Critical — SQL Injection in /api/users/search

**Severity:** Critical (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H)

## Description
The `q` parameter of GET /api/users/search is concatenated directly into a
MySQL SELECT statement without parameterization, enabling full database
read/write by unauthenticated attackers.

## Impact
An unauthenticated attacker can exfiltrate all user records including
hashed passwords and PII, modify or delete data, and potentially achieve
OS-level code execution via INTO OUTFILE — putting all customer data and
PCI-DSS compliance at risk.

## Reproduction
1. burp_proxy_history(host="app.example.com", contains="/api/users/search") — locate baseline request.
2. burp_repeater_send(raw_base64=<b64 of GET with q=1' OR '1'='1>, host="app.example.com", port=443, secure=true, tab_name="sqli-bool")
3. Confirm HTTP 200 with >1 record in the response.
4. burp_repeater_send(raw_base64=<b64 of GET with UNION SELECT user,password,3 FROM mysql.user-- payload>, host="app.example.com", port=443, secure=true, tab_name="sqli-union")
5. Confirm DB credentials in response body via burp_proxy_request(id=<N>).

## Evidence
- evidence/sqli/request.http — raw request with UNION payload
- evidence/sqli/response.http — response containing mysql.user rows
- evidence/sqli/screenshot.png — browser render showing credential leak
- evidence/sqli/source.md — UserRepository.java commit a3f9b2d lines 42-47

## Remediation
Replace string concatenation with a prepared statement:

// Before (vulnerable)
String sql = "SELECT * FROM users WHERE name = '" + q + "'";

// After (safe)
PreparedStatement ps = conn.prepareStatement(
    "SELECT * FROM users WHERE name = ?");
ps.setString(1, q);
ResultSet rs = ps.executeQuery();
```

---

**Worked example 2 — IDOR**

```
# High — Insecure Direct Object Reference on /api/orders/{id}

**Severity:** High (CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:L/A:N)

## Description
GET /api/orders/{id} returns order details for any numeric ID without
verifying that the authenticated user owns that order, allowing horizontal
privilege escalation across all customer records.

## Impact
Any authenticated customer can read order history, shipping addresses, and
partial payment data belonging to other customers. Bulk enumeration exposes
the full customer base, violating GDPR Article 32 and PCI-DSS Req 7.

## Reproduction
1. browser_navigate(url="https://app.example.com/orders/10042") — load own order as authenticated user.
2. browser_snapshot() — confirm own order renders.
3. burp_match_replace_set(rules=[{"match":"session=<own>","replace":"session=<victim>","type":"request_header","enabled":true}])
4. burp_repeater_send(raw_base64=<b64 of GET /api/orders/10043>, host="app.example.com", port=443, secure=true, tab_name="idor-probe")
5. Confirm via burp_proxy_request(id=<N>) that a different user's order is returned.

## Evidence
- evidence/idor/request.http — request for order ID 10043
- evidence/idor/response.http — response with different user's PII
- evidence/idor/screenshot.png — browser showing another user's address
- evidence/idor/source.md — OrderController.java commit b7c1d4e lines 88-95

## Remediation
Add ownership check before returning order data:

// Before (vulnerable)
Order order = orderRepo.findById(id);

// After (safe)
Order order = orderRepo.findByIdAndUserId(id, currentUser.getId());
if (order == null) {
    throw new ResponseStatusException(HttpStatus.FORBIDDEN);
}
```

---

**Worked example 3 — Reflected XSS**

```
# Medium — Reflected XSS in /search?term=

**Severity:** Medium (CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N)

## Description
The `term` query parameter on /search is reflected into the HTML response
inside a <p> tag without HTML-encoding, allowing injection of arbitrary
script via a crafted URL.

## Impact
An attacker can deliver a malicious link that executes JavaScript in the
victim's browser session, enabling session-token theft, credential phishing,
or defacement — affecting any unauthenticated user who clicks the link.

## Reproduction
1. browser_navigate(url="https://app.example.com/search?term=%3Csvg%2Fonload%3Dalert(1)%3E")
2. browser_eval(expression="!!document.querySelector('svg[onload]')") — expect true (payload executed).
3. browser_screenshot(full_page=true) — capture rendered alert / injected element.
4. burp_proxy_history(host="app.example.com", contains="/search?term=") — record request/response pair.

## Evidence
- evidence/xss/request.http — GET /search with script payload
- evidence/xss/response.http — response with unencoded <script> in body
- evidence/xss/screenshot.png — alert dialog showing session cookie
- evidence/xss/source.md — SearchController.java commit c9e2f7a lines 31-35

## Remediation
HTML-encode all user-supplied output at render time:

// Before (vulnerable)
model.addAttribute("term", request.getParameter("term"));
// In template: <p>Results for: ${term}</p>

// After (safe — Thymeleaf escapes by default)
model.addAttribute("term", request.getParameter("term"));
// In template: <p>Results for: <span th:text="${term}"></span></p>
// Or with explicit escaping:
import org.springframework.web.util.HtmlUtils;
String safe = HtmlUtils.htmlEscape(request.getParameter("term"));
```

## Interpret results

The finding is "ready to ship" when every section is populated and the reproduction steps work from a fresh Claude session (third-party reproducibility per `methodology-evidence-capture`).

Common pitfalls:

- Reproduction step references a burned one-time token — re-capture the evidence with a fresh token before delivery.
- Impact paragraph describes the attack technique instead of the business consequence — rewrite to state what assets are at risk and what regulatory or financial exposure results.

## Finding writeup

<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->

## References

- OWASP WSTG Reporting: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/
- NIST SP 800-115 §6: https://csrc.nist.gov/pubs/sp/800/115/final

## Authorization note

<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->
