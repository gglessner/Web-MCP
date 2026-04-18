---
name: recon-subdomain-enum
description: Enumerate subdomains of a target organisation using passive sources (CT logs, passive DNS) and active probes, then load results into Burp scope for downstream testing.
---

# Subdomain Enumeration

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`.

Use this skill during early-phase recon to expand the attack surface beyond an
initial URL. When an engagement provides only a root domain, siblings often host
different application stacks, older software versions, or developer endpoints
that are not otherwise surfaced. Running subdomain enumeration before any
active application testing ensures you have a complete picture of what assets
fall within scope.

## Signal to look for

- The engagement scope lists a root domain (e.g., `target.com`) without
  enumerating specific hostnames.
- A newly discovered asset (subdomain, IP block) may have siblings hosted
  on the same infrastructure.
- Tech fingerprinting reveals cloud-hosted infrastructure (AWS CloudFront,
  Azure Front Door, GCP Load Balancer) where sibling services commonly cluster
  under the same parent domain.

## Test steps

1. Run passive enumeration:
   ```
   subfinder -d target.com -silent
   ```
2. Run CT log harvest:
   ```
   curl -s 'https://crt.sh/?q=%25.target.com&output=json' | jq -r '.[].name_value' | sort -u
   ```
3. Optional: `amass enum -passive -d target.com` (passive mode only —
   active mode would violate RoE rate limits; see `methodology-rules-of-engagement`).
4. De-duplicate and filter results against the in-scope host wildcards confirmed
   via `methodology-scoping`. Discard any host that falls outside the approved
   asset list.
5. Load newly confirmed in-scope hosts into Burp:
   ```
   burp_scope_modify(add=["https://newsub.target.com"], remove=[])
   ```
6. Optional: resolve each candidate with `dig +short <host>` to filter
   unreachable entries before testing.

## Tool commands

Shell (canonical):

```bash
# Passive DNS enumeration via ProjectDiscovery Subfinder
subfinder -d target.com -silent
# Success: one subdomain per line printed to stdout, exit 0

# CT log harvest from crt.sh
curl -s 'https://crt.sh/?q=%25.target.com&output=json' | jq -r '.[].name_value' | sort -u
# Success: deduplicated list of CN/SAN values printed to stdout

# Passive-only amass (no active probing)
amass enum -passive -d target.com
# Success: subdomains printed to stdout with source annotations, exit 0
```

MCP follow-up (after filtering to confirmed in-scope hosts):

```
# Verify a host is already in Burp scope
burp_scope_check(urls=["https://newsub.target.com"])
# Success: {"ok": true, "data": {"results": [{"url": "https://newsub.target.com", "in_scope": false}]}}

# Add confirmed in-scope hosts to Burp scope
burp_scope_modify(add=["https://newsub.target.com", "https://dev.target.com"], remove=[])
# Success: {"ok": true, "data": {"added": 2, "removed": 0}}
```

## Interpret results

**ACME DNS-01 records** — entries matching `_acme-challenge.*` are DNS TXT
challenge records used for certificate issuance. They are not testable hosts;
exclude them from further enumeration.

**Wildcard DNS false positives** — if every arbitrary name resolves (e.g.,
`randomstring.target.com` returns an IP), the domain uses wildcard DNS. Filter
the enumerated list by querying a name that almost certainly does not exist and
comparing the response; discard results that share the same IP as the wildcard
response.

**Stale CT entries** — Certificate Transparency logs are append-only; a host
that appeared in a historical certificate may no longer exist. Always verify
reachability (step 6 above, or `curl -I`) before treating a CT result as an
active target.

**Owned vs. third-party** — confirm that each resolved IP belongs to the target
organization before testing. A subdomain delegated to a SaaS provider (e.g., a
`CNAME` to `*.zendesk.com`) is third-party infrastructure and requires separate
authorization per `methodology-scoping`.

## Finding writeup

Subdomain enumeration results typically feed the attack-surface inventory rather
than producing a standalone finding. If enumeration surfaces an unintended asset
— for example, a development or staging environment that is publicly reachable —
write it up as **"Exposed non-production asset"**, severity Low to Medium.
Raise severity to High if the asset leaks credentials, session tokens, or
customer data.

Evidence per `methodology-evidence-capture`:

- The passive-source hit (subfinder or crt.sh output line) confirming the
  subdomain was enumerated.
- A `curl -I https://dev.target.com` response showing the host is reachable and
  returns a meaningful HTTP status (not a timeout or NXDOMAIN).
- A `burp_sitemap` entry if Burp has observed traffic to the asset.

## References

- OWASP WSTG Information Gathering — Enumerate Applications on Webserver
  (WSTG-INFO-04):
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/04-Enumerate_Applications_on_Webserver
- crt.sh Certificate Search: https://crt.sh/
- ProjectDiscovery Subfinder documentation:
  https://docs.projectdiscovery.io/tools/subfinder/

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
