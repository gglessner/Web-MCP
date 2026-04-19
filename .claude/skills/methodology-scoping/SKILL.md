---
name: methodology-scoping
description: Define the scope of a web application penetration test — in-scope assets, excluded targets, third-party restrictions, credential handling — before any active testing begins.
---

# Scoping a Web Application Penetration Test

## When to use

Use this skill at the start of every engagement, before running any recon or
testing skill. It is especially necessary when the target list is ambiguous
("test this site" with no written asset list), when the sponsor has not provided
a formal scope document, or when a recon finding surfaces an asset whose scope
status is unclear — for example, a subdomain on a shared host or a resource
served through a third-party CDN.

## Signal to look for

- No written target list has been provided before testing begins.
- The user or sponsor says "test this site" without specifying what else is or
  is not in scope.
- A discovered asset sits on a borderline: shared hosting, a third-party CDN
  node, a different domain registered to the same organization, or a SaaS
  platform used by the target.
- Credentials have been mentioned but no rules around their use have been set.
- There is no signed-off artifact (email, PDF, ticket) confirming what was
  agreed.

## Test steps

1. Obtain the in-scope URL and/or IP list from the test sponsor in writing.
2. Obtain an explicit exclusion list: production data stores, payment systems,
   specific user accounts, or any other systems the sponsor places off-limits.
3. Confirm third-party and hosted-service restrictions — SaaS platforms, CDN
   providers, and cloud IaaS providers (AWS, Azure, GCP) may require their own
   pre-approval before you test infrastructure they operate on behalf of the
   customer.
4. Confirm credential-handling rules: test accounts versus real user accounts,
   password rotation policy during the test, and whether MFA is in scope or
   should be bypassed via test-account configuration.
5. Confirm data-retention and data-egress limits: what data may leave the test
   environment, how findings and evidence are stored, and when artifacts must
   be deleted.
6. Obtain a signed-off scope record — email thread, PDF, or ticket — and note
   the path or reference so it can be attached to the final report.

## Tool commands

Send the following questionnaire to the test sponsor before any testing begins.
Adapt field names to the engagement and include every item relevant to the engagement type.

```
SCOPE QUESTIONNAIRE — [Engagement name] — [Date]

1. In-scope assets (list all URLs, IP ranges, or CIDR blocks):

2. Explicitly out-of-scope assets or systems:

3. Third-party services in use (CDN, SaaS, cloud provider):
   - Pre-approval obtained from third party? [ ] Yes  [ ] No  [ ] N/A

4. Credential handling:
   - Test accounts provided? [ ] Yes  [ ] No
   - Account names/IDs:
   - Password rotation during test? [ ] Yes  [ ] No
   - MFA enabled on test accounts? [ ] Yes  [ ] No

5. Data-egress limits (what may leave the test environment):

6. Data-retention / deletion timeline for test artifacts:

7. Authorized testing window (dates and hours):

8. Emergency stop contact (name, phone):
```

Use these two shell commands as lightweight ownership spot-checks once a target
hostname has been confirmed in-scope — they do not probe the application:

```bash
# Check server headers to confirm you are hitting the expected target
curl -sI https://target.example.com | grep -i '^server\|^x-'

# Confirm nameserver delegation matches the expected registrant
dig +short target.example.com NS
```

## Interpret results

Classify each asset in one of three buckets:

- **Clearly in-scope** — the asset appears verbatim in the sponsor-approved
  list, or its IP resolves within an approved CIDR block. Proceed.
- **Clearly out-of-scope** — the asset is on the exclusion list, belongs to an
  unrelated organization, or sits on third-party infrastructure for which no
  pre-approval exists. Do not test; document that it was excluded.
- **Maybe — escalate** — the asset was discovered during recon and does not
  appear explicitly in either list; examples include an undocumented subdomain,
  a shared-hosting neighbour, or a third-party widget endpoint. Stop, document
  the question, and contact the sponsor in writing before testing. Do not assume
  inclusion; wait for a written response.

Any asset in the "maybe" bucket must be resolved before it is touched.
Undocumented scope expansion — even unintentional — can void the authorisation
that protects the tester legally.

## Write `engagement.toml`

Once the scope record above is agreed, the **tester** writes `engagement.toml`
at the repo root (copy `engagement.example.toml`). The `[scope].hosts` list is
the mechanical guardrail every `recon-*` and `testing-*` skill relies on —
browser-mcp and burp-mcp refuse hosts not listed there. The tester populates
`[credentials.*]` with the engagement-supplied test accounts.

**Do not read `engagement.toml`** — it contains credentials. Call the
`engagement_info` MCP tool to discover available credential names, identity
names, and scope hosts without seeing any secret values. Reference credentials
as `{{CRED:<name>.<field>}}`; the MCP servers expand the placeholder
server-side and redact the literal in all outputs. See
`docs/engagement-setup.md` for the full walkthrough.

## Finding writeup

<!-- Methodology skill — does not itself produce findings. -->

## References

- PTES Pre-engagement:
  http://www.pentest-standard.org/index.php/Pre-engagement
- OWASP WSTG Introduction:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/
- NIST SP 800-115 §3:
  https://csrc.nist.gov/pubs/sp/800/115/final

## Authorization note

Scoping is not a preliminary formality — it *is* authorization. The written
scope record produced by this skill is the legal and professional foundation
that makes all subsequent reconnaissance and testing legitimate. Without it,
the tester has no documented permission, and any probe — however benign —
could constitute unauthorized access under applicable computer-crime law. The
scope document should identify the authorizing individual at the target
organization by name and title, list every asset approved for testing, and
bear a date and signature (electronic is sufficient). Keep this artifact on
file for the duration of the engagement and for whatever retention period your
organization's policy or the client contract requires.

_If no such artifact exists, do not proceed to any recon-* or testing-* skill._
