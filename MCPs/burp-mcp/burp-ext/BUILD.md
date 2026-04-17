# Building burp-mcp-bridge

```bash
cd MCPs/burp-mcp/burp-ext
./gradlew shadowJar
# Produces build/libs/burp-mcp-bridge.jar
```

Load in Burp: Extensions → Add → Extension type: Java → Extension file: `build/libs/burp-mcp-bridge.jar` → Next.

Verify: Burp → Extensions → Output shows `burp-mcp-bridge listening on 127.0.0.1:8775`.

Smoke test from host:
```bash
curl -s http://127.0.0.1:8775/meta | python -m json.tool
```

Expected: `{"ok": true, "data": {"edition": "COMMUNITY_EDITION", "version": "...", "bridge_version": "0.1.0"}}`.
