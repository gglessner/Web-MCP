# Plan B — burp-mcp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build both halves of burp-mcp: a Kotlin Burp extension (Montoya API) that exposes Burp internals via a loopback HTTP server, and a thin Python MCP that maps each MCP tool 1:1 to an extension endpoint.

**Architecture:** Kotlin extension with Gradle + Shadow plugin produces a single fat jar loaded in Burp → Extensions. Extension runs JDK-bundled `com.sun.net.httpserver.HttpServer` on `127.0.0.1:8775`. Python MCP uses `httpx` + the `mcp` SDK; `common/burp_client.py` is the typed HTTP client. Pro-only features (Scanner/Intruder) detected at startup via `/meta` and return `PRO_REQUIRED` on Community.

**Tech Stack:** Kotlin 1.9+, Gradle 8+, Montoya API, JDK 17+, Shadow plugin (single-jar build). Python 3.13, `mcp`, `httpx`, `respx` (mocks), `pytest`, `pytest-asyncio`.

**Prereqs:** Plan A complete (`.venv`, `common/`). JDK 17+ on PATH. Burp Suite 2026.2.4 (already installed).

**Spec:** `docs/superpowers/specs/2026-04-16-web-mcp-stack-design.md`

---

### Task 1: Gradle + Kotlin skeleton with Montoya dependency

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/settings.gradle.kts`
- Create: `MCPs/burp-mcp/burp-ext/build.gradle.kts`
- Create: `MCPs/burp-mcp/burp-ext/gradle.properties`
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/BurpMcpExtension.kt`
- Create: `MCPs/burp-mcp/burp-ext/src/main/resources/META-INF/MANIFEST.MF` (only if needed; not generally)

- [ ] **Step 1: `settings.gradle.kts`**

```kotlin
rootProject.name = "burp-mcp-bridge"
```

- [ ] **Step 2: `gradle.properties`**

```
org.gradle.jvmargs=-Xmx2g
kotlin.code.style=official
```

- [ ] **Step 3: `build.gradle.kts`**

```kotlin
plugins {
    kotlin("jvm") version "1.9.25"
    id("com.gradleup.shadow") version "8.3.5"
}

repositories { mavenCentral() }

dependencies {
    compileOnly("net.portswigger.burp.extensions:montoya-api:2024.12")
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.3")
}

kotlin {
    jvmToolchain(17)
}

tasks.test {
    useJUnitPlatform()
}

tasks.shadowJar {
    archiveBaseName.set("burp-mcp-bridge")
    archiveClassifier.set("")
    archiveVersion.set("")
    mergeServiceFiles()
}

tasks.build {
    dependsOn(tasks.shadowJar)
}
```

- [ ] **Step 4: `BurpMcpExtension.kt` (entry point stub)**

```kotlin
package webmcp

import burp.api.montoya.BurpExtension
import burp.api.montoya.MontoyaApi

class BurpMcpExtension : BurpExtension {
    private var server: HttpBridgeServer? = null

    override fun initialize(api: MontoyaApi) {
        api.extension().setName("burp-mcp-bridge")
        val port = 8775
        server = HttpBridgeServer(api, port).also { it.start() }
        api.logging().logToOutput("burp-mcp-bridge listening on 127.0.0.1:$port")
        api.extension().registerUnloadingHandler {
            server?.stop()
            api.logging().logToOutput("burp-mcp-bridge stopped")
        }
    }
}
```

- [ ] **Step 5: Register as a BurpExtension service**

Create `MCPs/burp-mcp/burp-ext/src/main/resources/META-INF/services/burp.api.montoya.BurpExtension`:
```
webmcp.BurpMcpExtension
```

- [ ] **Step 6: Verify Gradle resolves dependencies**

```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle --version  # sanity: ≥ 8
gradle dependencies --configuration compileClasspath | head -20
```
Expected: Montoya API resolves from Maven Central. (If `gradle` not installed: `sudo apt-get install -y gradle` or use `./gradlew` after running `gradle wrapper` once.)

- [ ] **Step 7: Commit**

```bash
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "chore(burp-mcp): Gradle+Kotlin skeleton with Montoya API"
```

---

### Task 2: HTTP server scaffold + `/meta` endpoint + router

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt`
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/Routes.kt`
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/Json.kt`
- Create: `MCPs/burp-mcp/burp-ext/src/test/kotlin/webmcp/RoutesTest.kt`

- [ ] **Step 1: Write `Json.kt` (minimal JSON serializer to avoid extra deps)**

```kotlin
package webmcp

/** Dependency-free JSON writer/reader sufficient for the bridge's flat payloads. */
object Json {
    fun encode(value: Any?): String {
        val sb = StringBuilder()
        write(sb, value)
        return sb.toString()
    }

    private fun write(sb: StringBuilder, value: Any?) {
        when (value) {
            null -> sb.append("null")
            is Boolean -> sb.append(value)
            is Number -> sb.append(value)
            is String -> encodeString(sb, value)
            is Map<*, *> -> {
                sb.append('{')
                value.entries.forEachIndexed { i, (k, v) ->
                    if (i > 0) sb.append(',')
                    encodeString(sb, k.toString())
                    sb.append(':')
                    write(sb, v)
                }
                sb.append('}')
            }
            is Iterable<*> -> {
                sb.append('[')
                value.forEachIndexed { i, v ->
                    if (i > 0) sb.append(',')
                    write(sb, v)
                }
                sb.append(']')
            }
            else -> encodeString(sb, value.toString())
        }
    }

    private fun encodeString(sb: StringBuilder, s: String) {
        sb.append('"')
        for (c in s) {
            when (c) {
                '"' -> sb.append("\\\"")
                '\\' -> sb.append("\\\\")
                '\n' -> sb.append("\\n")
                '\r' -> sb.append("\\r")
                '\t' -> sb.append("\\t")
                '\b' -> sb.append("\\b")
                '\u000C' -> sb.append("\\f")
                else -> if (c.code < 0x20) sb.append("\\u%04x".format(c.code)) else sb.append(c)
            }
        }
        sb.append('"')
    }

    /** Minimal JSON parser — handles objects/arrays/strings/numbers/bool/null. */
    fun decode(s: String): Any? = Parser(s).parseValue().also { Parser(s).skipTrailing() }

    private class Parser(val src: String) {
        var i = 0
        fun parseValue(): Any? {
            skipWs()
            if (i >= src.length) error("empty")
            return when (src[i]) {
                '{' -> parseObject()
                '[' -> parseArray()
                '"' -> parseString()
                't', 'f' -> parseBool()
                'n' -> parseNull()
                else -> parseNumber()
            }
        }
        fun parseObject(): LinkedHashMap<String, Any?> {
            expect('{'); val out = LinkedHashMap<String, Any?>()
            skipWs(); if (peek() == '}') { i++; return out }
            while (true) {
                skipWs(); val k = parseString(); skipWs(); expect(':')
                out[k] = parseValue(); skipWs()
                if (peek() == ',') { i++; continue }
                expect('}'); return out
            }
        }
        fun parseArray(): ArrayList<Any?> {
            expect('['); val out = ArrayList<Any?>()
            skipWs(); if (peek() == ']') { i++; return out }
            while (true) {
                out.add(parseValue()); skipWs()
                if (peek() == ',') { i++; continue }
                expect(']'); return out
            }
        }
        fun parseString(): String {
            expect('"'); val sb = StringBuilder()
            while (i < src.length) {
                val c = src[i++]
                if (c == '"') return sb.toString()
                if (c == '\\') {
                    val esc = src[i++]
                    sb.append(when (esc) {
                        '"' -> '"'; '\\' -> '\\'; '/' -> '/'
                        'n' -> '\n'; 'r' -> '\r'; 't' -> '\t'
                        'b' -> '\b'; 'f' -> '\u000C'
                        'u' -> { val hex = src.substring(i, i + 4); i += 4; hex.toInt(16).toChar() }
                        else -> error("bad escape: $esc")
                    })
                } else sb.append(c)
            }
            error("unterminated string")
        }
        fun parseNumber(): Number {
            val start = i
            if (peek() == '-') i++
            while (i < src.length && (src[i].isDigit() || src[i] == '.' || src[i] == 'e' || src[i] == 'E' || src[i] == '+' || src[i] == '-')) i++
            val tok = src.substring(start, i)
            return if (tok.contains('.') || tok.contains('e') || tok.contains('E')) tok.toDouble() else tok.toLong()
        }
        fun parseBool(): Boolean =
            if (src.startsWith("true", i)) { i += 4; true }
            else if (src.startsWith("false", i)) { i += 5; false }
            else error("bad bool")
        fun parseNull(): Any? = if (src.startsWith("null", i)) { i += 4; null } else error("bad null")
        fun skipWs() { while (i < src.length && src[i].isWhitespace()) i++ }
        fun skipTrailing() { skipWs() }
        fun peek(): Char? = if (i < src.length) src[i] else null
        fun expect(c: Char) { if (peek() != c) error("expected '$c' at $i") ; i++ }
    }
}
```

- [ ] **Step 2: Write `Routes.kt` with a trivial router and `/meta`**

```kotlin
package webmcp

import burp.api.montoya.MontoyaApi

/** A single route: method + path pattern + handler. No regex groups used here. */
data class Route(
    val method: String,
    val path: String,
    val handler: (RequestCtx) -> Response,
)

data class RequestCtx(
    val method: String,
    val path: String,
    val query: Map<String, String>,
    val bodyJson: Map<String, Any?>?,
    val api: MontoyaApi,
)

data class Response(val status: Int, val json: Any?) {
    fun body(): String = Json.encode(json)
}

class Router(private val api: MontoyaApi) {
    private val routes = mutableListOf<Route>()

    fun register(method: String, path: String, handler: (RequestCtx) -> Response) {
        routes += Route(method, path, handler)
    }

    /** Simple matcher: exact method + exact or prefix-with-`{id}` path. */
    fun dispatch(method: String, fullPath: String, query: Map<String, String>, body: String?): Response {
        val pathOnly = fullPath
        val bodyJson = body?.takeIf { it.isNotBlank() }?.let { Json.decode(it) as? Map<String, Any?> }
        for (r in routes) {
            if (r.method != method) continue
            if (matches(r.path, pathOnly)) {
                val ctx = RequestCtx(method, pathOnly, query, bodyJson, api)
                return runCatching { r.handler(ctx) }.getOrElse {
                    Response(500, mapOf("ok" to false, "error" to mapOf(
                        "code" to "INTERNAL", "message" to (it.message ?: it::class.simpleName)
                    )))
                }
            }
        }
        return Response(404, mapOf("ok" to false, "error" to mapOf(
            "code" to "BAD_INPUT", "message" to "no route: $method $pathOnly"
        )))
    }

    private fun matches(pattern: String, path: String): Boolean {
        if (pattern == path) return true
        if ("{" !in pattern) return false
        val pParts = pattern.split('/')
        val xParts = path.split('/')
        if (pParts.size != xParts.size) return false
        return pParts.zip(xParts).all { (p, x) -> p.startsWith("{") || p == x }
    }

    companion object {
        fun pathParam(pattern: String, path: String, name: String): String? {
            val pParts = pattern.split('/')
            val xParts = path.split('/')
            if (pParts.size != xParts.size) return null
            for ((p, x) in pParts.zip(xParts)) if (p == "{$name}") return x
            return null
        }
    }
}

fun registerMetaRoute(router: Router) {
    router.register("GET", "/meta") { ctx ->
        val api = ctx.api
        val edition = runCatching { api.burpSuite().version().edition().toString() }.getOrDefault("UNKNOWN")
        val version = runCatching { api.burpSuite().version().name() + " " + api.burpSuite().version().major() + "." + api.burpSuite().version().minor() }.getOrDefault("unknown")
        Response(200, mapOf(
            "ok" to true,
            "data" to mapOf(
                "edition" to edition,   // "PROFESSIONAL" | "COMMUNITY_EDITION"
                "version" to version,
                "bridge_version" to "0.1.0",
            ),
        ))
    }
}
```

- [ ] **Step 3: Write `HttpBridgeServer.kt`**

```kotlin
package webmcp

import burp.api.montoya.MontoyaApi
import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.nio.charset.StandardCharsets
import java.util.concurrent.Executors

class HttpBridgeServer(private val api: MontoyaApi, private val port: Int) {
    private val server: HttpServer = HttpServer.create(InetSocketAddress("127.0.0.1", port), 0)
    private val router = Router(api)

    init {
        registerMetaRoute(router)
        // Later tasks call: registerProxyRoutes(router), registerRepeaterRoutes(router), etc.
        server.executor = Executors.newFixedThreadPool(4)
        server.createContext("/") { exchange -> handle(exchange) }
    }

    fun routerInstance(): Router = router  // for test wiring

    fun start() { server.start() }

    fun stop() { server.stop(0) }

    private fun handle(exchange: HttpExchange) {
        try {
            val method = exchange.requestMethod
            val uri = exchange.requestURI
            val path = uri.rawPath ?: "/"
            val query = (uri.rawQuery ?: "").split("&").filter { it.isNotBlank() }.associate {
                val eq = it.indexOf('=')
                if (eq < 0) it to "" else java.net.URLDecoder.decode(it.substring(0, eq), "UTF-8") to
                    java.net.URLDecoder.decode(it.substring(eq + 1), "UTF-8")
            }
            val body = exchange.requestBody.readBytes().toString(StandardCharsets.UTF_8)

            val resp = router.dispatch(method, path, query, body)
            val bytes = resp.body().toByteArray(StandardCharsets.UTF_8)
            exchange.responseHeaders.add("Content-Type", "application/json")
            exchange.sendResponseHeaders(resp.status, bytes.size.toLong())
            exchange.responseBody.use { it.write(bytes) }
        } catch (t: Throwable) {
            val err = Json.encode(mapOf("ok" to false, "error" to mapOf(
                "code" to "INTERNAL", "message" to (t.message ?: t::class.simpleName)
            ))).toByteArray()
            exchange.sendResponseHeaders(500, err.size.toLong())
            exchange.responseBody.use { it.write(err) }
        } finally {
            exchange.close()
        }
    }
}
```

- [ ] **Step 4: Write router test (no Burp needed for routing)**

`MCPs/burp-mcp/burp-ext/src/test/kotlin/webmcp/RoutesTest.kt`:
```kotlin
package webmcp

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class RoutesTest {
    @Test
    fun `router matches exact and param paths`() {
        val router = Router(api = FakeApi())
        router.register("GET", "/hello") { Response(200, mapOf("ok" to true)) }
        router.register("GET", "/proxy/request/{id}") { ctx ->
            val id = Router.pathParam("/proxy/request/{id}", ctx.path, "id")
            Response(200, mapOf("ok" to true, "id" to id))
        }

        val r1 = router.dispatch("GET", "/hello", emptyMap(), null)
        assertEquals(200, r1.status)

        val r2 = router.dispatch("GET", "/proxy/request/42", emptyMap(), null)
        assertTrue(r2.body().contains("\"id\":\"42\""))

        val r3 = router.dispatch("GET", "/nope", emptyMap(), null)
        assertEquals(404, r3.status)
    }

    @Test
    fun `json roundtrip`() {
        val payload = mapOf("ok" to true, "data" to listOf(1, "two", mapOf("k" to null)))
        val encoded = Json.encode(payload)
        val decoded = Json.decode(encoded) as Map<*, *>
        assertEquals(true, decoded["ok"])
    }
}

class FakeApi : burp.api.montoya.MontoyaApi {
    override fun burpSuite(): burp.api.montoya.BurpSuite = throw NotImplementedError()
    override fun extension(): burp.api.montoya.extension.Extension = throw NotImplementedError()
    override fun logging(): burp.api.montoya.logging.Logging = throw NotImplementedError()
    override fun http(): burp.api.montoya.http.Http = throw NotImplementedError()
    override fun proxy(): burp.api.montoya.proxy.Proxy = throw NotImplementedError()
    override fun scanner(): burp.api.montoya.scanner.Scanner = throw NotImplementedError()
    override fun scope(): burp.api.montoya.scope.Scope = throw NotImplementedError()
    override fun siteMap(): burp.api.montoya.sitemap.SiteMap = throw NotImplementedError()
    override fun repeater(): burp.api.montoya.repeater.Repeater = throw NotImplementedError()
    override fun intruder(): burp.api.montoya.intruder.Intruder = throw NotImplementedError()
    override fun collaborator(): burp.api.montoya.collaborator.Collaborator = throw NotImplementedError()
    override fun persistence(): burp.api.montoya.persistence.Persistence = throw NotImplementedError()
    override fun userInterface(): burp.api.montoya.ui.UserInterface = throw NotImplementedError()
    override fun utilities(): burp.api.montoya.utilities.Utilities = throw NotImplementedError()
    override fun websockets(): burp.api.montoya.websocket.WebSockets = throw NotImplementedError()
    override fun organizer(): burp.api.montoya.organizer.Organizer = throw NotImplementedError()
    override fun comparer(): burp.api.montoya.comparer.Comparer = throw NotImplementedError()
    override fun decoder(): burp.api.montoya.decoder.Decoder = throw NotImplementedError()
    override fun intelligence(): burp.api.montoya.intelligence.Intelligence = throw NotImplementedError()
}
```
Note: the exact set of `MontoyaApi` methods depends on the API version. If your version lacks some of these (or has extras), adjust the stub class. The compileOnly dependency in `build.gradle.kts` governs the surface.

- [ ] **Step 5: Run the test**

```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle test
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "feat(burp-mcp): HTTP bridge server, JSON codec, router + /meta endpoint"
```

---

### Task 3: `/proxy/history` and `/proxy/request/{id}`

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/ProxyRoutes.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt` (wire it in)

- [ ] **Step 1: Write `ProxyRoutes.kt`**

```kotlin
package webmcp

import burp.api.montoya.proxy.ProxyHttpRequestResponse
import java.util.Base64

fun registerProxyRoutes(router: Router) {
    router.register("GET", "/proxy/history") { ctx ->
        val host = ctx.query["host"]
        val method = ctx.query["method"]
        val statusMin = ctx.query["status"]?.toIntOrNull()
        val contains = ctx.query["contains"]
        val limit = (ctx.query["limit"]?.toIntOrNull() ?: 50).coerceAtMost(500)
        val cursor = ctx.query["cursor"]?.toIntOrNull() ?: 0

        val all: List<ProxyHttpRequestResponse> = ctx.api.proxy().history()
        val filtered = all.asSequence()
            .filter { host == null || it.finalRequest().httpService().host() == host }
            .filter { method == null || it.finalRequest().method().equals(method, ignoreCase = true) }
            .filter { statusMin == null || ((it.originalResponse()?.statusCode() ?: 0).toInt() >= statusMin) }
            .filter { contains == null || it.finalRequest().toByteArray().toString().contains(contains) || (it.originalResponse()?.toByteArray()?.toString()?.contains(contains) ?: false) }
            .toList()

        val page = filtered.drop(cursor).take(limit)
        val nextCursor = if (cursor + limit < filtered.size) cursor + limit else null

        Response(200, mapOf(
            "ok" to true,
            "data" to mapOf(
                "entries" to page.mapIndexed { i, h -> summarize(h, cursor + i) },
                "next_cursor" to nextCursor,
                "total" to filtered.size,
            ),
        ))
    }

    router.register("GET", "/proxy/request/{id}") { ctx ->
        val idStr = Router.pathParam("/proxy/request/{id}", ctx.path, "id")
        val idx = idStr?.toIntOrNull()
            ?: return@register Response(400, mapOf("ok" to false, "error" to mapOf(
                "code" to "BAD_INPUT", "message" to "id not integer: $idStr"
            )))
        val all = ctx.api.proxy().history()
        if (idx < 0 || idx >= all.size) {
            return@register Response(404, mapOf("ok" to false, "error" to mapOf(
                "code" to "BAD_INPUT", "message" to "id out of range: $idx (have ${all.size})"
            )))
        }
        val h = all[idx]
        Response(200, mapOf("ok" to true, "data" to detail(h, idx)))
    }
}

private fun summarize(h: ProxyHttpRequestResponse, id: Int): Map<String, Any?> {
    val req = h.finalRequest()
    val resp = h.originalResponse()
    return mapOf(
        "id" to id,
        "method" to req.method(),
        "url" to req.url(),
        "host" to req.httpService().host(),
        "status" to (resp?.statusCode()?.toInt()),
        "mime" to (resp?.statedMimeType()?.toString()),
        "length" to (resp?.toByteArray()?.length() ?: 0),
    )
}

private fun detail(h: ProxyHttpRequestResponse, id: Int): Map<String, Any?> {
    val req = h.finalRequest()
    val resp = h.originalResponse()
    return mapOf(
        "id" to id,
        "request" to mapOf(
            "method" to req.method(),
            "url" to req.url(),
            "raw_base64" to Base64.getEncoder().encodeToString(req.toByteArray().bytes),
        ),
        "response" to (resp?.let {
            mapOf(
                "status" to it.statusCode().toInt(),
                "raw_base64" to Base64.getEncoder().encodeToString(it.toByteArray().bytes),
            )
        }),
    )
}
```
**Note:** Montoya API specifics (method names, signatures) may differ slightly between Burp releases. If the build fails, look at imports and adjust — e.g., `ByteArray.length()` vs `.size`. Keep the behavior the same; do not change tests.

- [ ] **Step 2: Wire proxy routes in `HttpBridgeServer.kt`**

Modify the `init` block to add:
```kotlin
        registerMetaRoute(router)
        registerProxyRoutes(router)
```

- [ ] **Step 3: Build and verify compilation**

```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle build -x test
```
Expected: `BUILD SUCCESSFUL` and `build/libs/burp-mcp-bridge.jar` exists.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "feat(burp-mcp): proxy history list + per-id detail endpoints"
```

---

### Task 4: `/repeater/send` endpoint

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/RepeaterRoutes.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt`

- [ ] **Step 1: Write `RepeaterRoutes.kt`**

```kotlin
package webmcp

import burp.api.montoya.core.ByteArray as MByteArray
import burp.api.montoya.http.HttpService
import burp.api.montoya.http.message.requests.HttpRequest
import java.util.Base64

fun registerRepeaterRoutes(router: Router) {
    router.register("POST", "/repeater/send") { ctx ->
        val body = ctx.bodyJson ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "JSON body required")
        ))
        val tabName = body["tab_name"] as? String ?: "mcp-${System.currentTimeMillis()}"
        val rawB64 = body["raw_base64"] as? String
        val host = body["host"] as? String
        val port = (body["port"] as? Number)?.toInt()
        val secure = body["secure"] as? Boolean ?: true

        if (rawB64 == null || host == null || port == null) {
            return@register Response(400, mapOf("ok" to false, "error" to mapOf(
                "code" to "BAD_INPUT", "message" to "raw_base64, host, port required"
            )))
        }
        val rawBytes = Base64.getDecoder().decode(rawB64)
        val service = HttpService.httpService(host, port, secure)
        val req = HttpRequest.httpRequest(service, MByteArray.byteArray(*rawBytes))
        ctx.api.repeater().sendToRepeater(req, tabName)
        Response(200, mapOf("ok" to true, "data" to mapOf("tab" to tabName)))
    }
}
```

- [ ] **Step 2: Register the route in `HttpBridgeServer.kt`**

Add `registerRepeaterRoutes(router)` beside the others.

- [ ] **Step 3: Build**

```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle build -x test
```
Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "feat(burp-mcp): repeater/send endpoint"
```

---

### Task 5: `/scope` GET and POST

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/ScopeRoutes.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt`

- [ ] **Step 1: Write `ScopeRoutes.kt`**

```kotlin
package webmcp

fun registerScopeRoutes(router: Router) {
    router.register("GET", "/scope") { ctx ->
        // Montoya exposes `isInScope(url)` but not a scope enumeration; we document this.
        // Return a tiny echo endpoint: caller supplies candidate URLs to test.
        val candidatesCsv = ctx.query["test"] ?: ""
        val candidates = if (candidatesCsv.isBlank()) emptyList() else candidatesCsv.split(",")
        val results = candidates.associateWith { u -> ctx.api.scope().isInScope(u) }
        Response(200, mapOf("ok" to true, "data" to mapOf("checks" to results)))
    }

    router.register("POST", "/scope") { ctx ->
        val body = ctx.bodyJson ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "JSON body required")
        ))
        val add = (body["add"] as? List<*>)?.mapNotNull { it as? String } ?: emptyList()
        val remove = (body["remove"] as? List<*>)?.mapNotNull { it as? String } ?: emptyList()
        add.forEach { ctx.api.scope().includeInScope(it) }
        remove.forEach { ctx.api.scope().excludeFromScope(it) }
        Response(200, mapOf("ok" to true, "data" to mapOf("added" to add, "removed" to remove)))
    }
}
```

- [ ] **Step 2: Register the routes and build**

Add `registerScopeRoutes(router)`. Then:
```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle build -x test
```
Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 3: Commit**

```bash
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "feat(burp-mcp): scope read + add/remove endpoints"
```

---

### Task 6: `/sitemap` endpoint

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/SiteMapRoutes.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt`

- [ ] **Step 1: Write `SiteMapRoutes.kt`**

```kotlin
package webmcp

import burp.api.montoya.sitemap.SiteMapFilter

fun registerSiteMapRoutes(router: Router) {
    router.register("GET", "/sitemap") { ctx ->
        val prefix = ctx.query["prefix"]
        val filter = if (prefix != null) SiteMapFilter.prefixFilter(prefix) else null
        val entries = if (filter != null) ctx.api.siteMap().requestResponses(filter) else ctx.api.siteMap().requestResponses()
        val limit = (ctx.query["limit"]?.toIntOrNull() ?: 200).coerceAtMost(2000)
        val cursor = ctx.query["cursor"]?.toIntOrNull() ?: 0
        val list = entries.drop(cursor).take(limit).mapIndexed { i, h ->
            mapOf(
                "id" to (cursor + i),
                "method" to h.request().method(),
                "url" to h.request().url(),
                "status" to (h.response()?.statusCode()?.toInt()),
            )
        }
        val nextCursor = if (cursor + limit < entries.size) cursor + limit else null
        Response(200, mapOf("ok" to true, "data" to mapOf(
            "entries" to list, "next_cursor" to nextCursor, "total" to entries.size
        )))
    }
}
```

- [ ] **Step 2: Register, build, commit**

Add `registerSiteMapRoutes(router)`. Then:
```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle build -x test
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "feat(burp-mcp): sitemap endpoint with prefix filter + pagination"
```

---

### Task 7: `/scanner/scan` and `/scanner/issues` with Pro detection

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/ScannerRoutes.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt`

- [ ] **Step 1: Write `ScannerRoutes.kt`**

```kotlin
package webmcp

import burp.api.montoya.scanner.AuditConfiguration
import burp.api.montoya.scanner.BuiltInAuditConfiguration

fun registerScannerRoutes(router: Router) {

    fun proRequired(msg: String = "Scanner requires Burp Suite Professional") =
        Response(503, mapOf("ok" to false, "error" to mapOf(
            "code" to "PRO_REQUIRED", "message" to msg
        )))

    router.register("POST", "/scanner/scan") { ctx ->
        val isPro = ctx.api.burpSuite().version().edition().toString().contains("PROFESSIONAL", ignoreCase = true)
        if (!isPro) return@register proRequired()
        val body = ctx.bodyJson ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "JSON body required")
        ))
        val url = body["url"] as? String ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "url required")
        ))
        val mode = (body["mode"] as? String ?: "active").lowercase()
        val config = AuditConfiguration.auditConfiguration(
            if (mode == "passive") BuiltInAuditConfiguration.LEGACY_PASSIVE_AUDIT_CHECKS
            else BuiltInAuditConfiguration.LEGACY_ACTIVE_AUDIT_CHECKS
        )
        val task = ctx.api.scanner().startAudit(config)
        task.addUrl(url)
        Response(200, mapOf("ok" to true, "data" to mapOf("audit_id" to task.toString())))
    }

    router.register("GET", "/scanner/issues") { ctx ->
        val isPro = ctx.api.burpSuite().version().edition().toString().contains("PROFESSIONAL", ignoreCase = true)
        if (!isPro) return@register proRequired()
        val issues = ctx.api.siteMap().issues()
        val list = issues.mapIndexed { i, issue ->
            mapOf(
                "id" to i,
                "name" to issue.name(),
                "severity" to issue.severity().toString(),
                "confidence" to issue.confidence().toString(),
                "url" to issue.baseUrl(),
            )
        }
        Response(200, mapOf("ok" to true, "data" to mapOf("issues" to list, "total" to issues.size)))
    }
}
```

- [ ] **Step 2: Register, build, commit**

Add `registerScannerRoutes(router)`. Then:
```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle build -x test
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "feat(burp-mcp): scanner endpoints with Pro detection + PRO_REQUIRED error"
```

---

### Task 8: `/intruder/launch` endpoint

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/IntruderRoutes.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt`

- [ ] **Step 1: Write `IntruderRoutes.kt`**

```kotlin
package webmcp

import burp.api.montoya.core.ByteArray as MByteArray
import burp.api.montoya.http.HttpService
import burp.api.montoya.http.message.requests.HttpRequest
import java.util.Base64

fun registerIntruderRoutes(router: Router) {
    router.register("POST", "/intruder/launch") { ctx ->
        val isPro = ctx.api.burpSuite().version().edition().toString().contains("PROFESSIONAL", ignoreCase = true)
        if (!isPro) return@register Response(503, mapOf(
            "ok" to false, "error" to mapOf("code" to "PRO_REQUIRED", "message" to "Intruder requires Burp Pro")
        ))
        val body = ctx.bodyJson ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "JSON body required")
        ))
        val rawB64 = body["raw_base64"] as? String
        val host = body["host"] as? String
        val port = (body["port"] as? Number)?.toInt()
        val secure = body["secure"] as? Boolean ?: true
        val tabName = body["tab_name"] as? String ?: "mcp-${System.currentTimeMillis()}"
        if (rawB64 == null || host == null || port == null) {
            return@register Response(400, mapOf(
                "ok" to false, "error" to mapOf("code" to "BAD_INPUT",
                    "message" to "raw_base64, host, port required")
            ))
        }
        val bytes = Base64.getDecoder().decode(rawB64)
        val svc = HttpService.httpService(host, port, secure)
        val req = HttpRequest.httpRequest(svc, MByteArray.byteArray(*bytes))
        ctx.api.intruder().sendToIntruder(req, tabName)
        Response(200, mapOf("ok" to true, "data" to mapOf("tab" to tabName)))
    }
}
```

- [ ] **Step 2: Register, build, commit**

Add `registerIntruderRoutes(router)`. Then:
```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle build -x test
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "feat(burp-mcp): intruder/launch endpoint (Pro-gated)"
```

---

### Task 9: `/match-replace` read and write

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/MatchReplaceRoutes.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt`

- [ ] **Step 1: Write `MatchReplaceRoutes.kt`**

Note: Montoya does not currently expose match-replace rules as first-class API objects in all versions. This endpoint therefore uses Burp's user settings JSON as a pragmatic fallback: we round-trip the user settings blob and expose the `proxy.match_replace_rules` slice.

```kotlin
package webmcp

fun registerMatchReplaceRoutes(router: Router) {
    router.register("GET", "/match-replace") { ctx ->
        val settings = ctx.api.burpSuite().exportUserOptionsAsJson()
        val parsed = Json.decode(settings) as? Map<*, *>
        val rules = ((parsed?.get("user_options") as? Map<*, *>)?.get("proxy") as? Map<*, *>)
            ?.get("match_replace_rules")
        Response(200, mapOf("ok" to true, "data" to mapOf("rules" to rules)))
    }

    router.register("POST", "/match-replace") { ctx ->
        val body = ctx.bodyJson ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "JSON body required")
        ))
        val rules = body["rules"] ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "rules required")
        ))
        // Build a minimal user-settings blob that Burp accepts.
        val wrapped = mapOf(
            "user_options" to mapOf(
                "proxy" to mapOf("match_replace_rules" to rules)
            )
        )
        ctx.api.burpSuite().importUserOptionsFromJson(Json.encode(wrapped))
        Response(200, mapOf("ok" to true, "data" to mapOf("applied" to true)))
    }
}
```
If your Montoya version does not expose `exportUserOptionsAsJson`/`importUserOptionsFromJson`, return a `PRO_REQUIRED`-style `{"code":"INTERNAL","message":"match-replace not supported on this Burp build"}` and document in the MCP tool.

- [ ] **Step 2: Register, build, commit**

Add `registerMatchReplaceRoutes(router)`. Then:
```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle build -x test
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/
git commit -m "feat(burp-mcp): match-replace GET/POST via user-settings round-trip"
```

---

### Task 10: Build fat jar + manual Burp load smoke test

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/BUILD.md` (instructions reference)

- [ ] **Step 1: Write `BUILD.md`**

```markdown
# Building burp-mcp-bridge

```bash
cd MCPs/burp-mcp/burp-ext
gradle shadowJar
# Produces build/libs/burp-mcp-bridge.jar
```

Load in Burp: Extensions → Add → Extension type: Java → Extension file: `build/libs/burp-mcp-bridge.jar` → Next.

Verify: Burp → Extensions → Output shows `burp-mcp-bridge listening on 127.0.0.1:8775`.

Smoke test from host:
```bash
curl -s http://127.0.0.1:8775/meta | python -m json.tool
```

Expected: `{"ok": true, "data": {"edition": "COMMUNITY_EDITION", "version": "...", "bridge_version": "0.1.0"}}`.
```

- [ ] **Step 2: Build the jar**

```bash
cd /home/kali/Web-MCP/MCPs/burp-mcp/burp-ext
gradle shadowJar
ls -la build/libs/burp-mcp-bridge.jar
```
Expected: jar exists, size 10-50KB (no shaded deps beyond Kotlin stdlib).

- [ ] **Step 3: Manual Burp load**

1. Launch Burp Suite.
2. Extensions → Add → Java → select `build/libs/burp-mcp-bridge.jar`.
3. Check Output tab for `burp-mcp-bridge listening on 127.0.0.1:8775`.
4. From another shell: `curl -s http://127.0.0.1:8775/meta`.
5. Expected JSON response with edition + version.
6. Send some traffic through Burp proxy (set browser proxy to 127.0.0.1:8080, visit a site), then:
   ```bash
   curl -s 'http://127.0.0.1:8775/proxy/history?limit=5'
   ```
   Expected: entries appear.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add MCPs/burp-mcp/burp-ext/BUILD.md
git commit -m "docs(burp-mcp): extension build and manual smoke-test instructions"
```

---

### Task 11: `common/burp_client.py` — typed HTTP client with respx tests

**Files:**
- Create: `common/burp_client.py`
- Create: `tests/test_common_burp_client.py`

- [ ] **Step 1: Write the failing test**

`tests/test_common_burp_client.py`:
```python
import httpx
import pytest
import respx

from common.burp_client import (
    BurpBadInput,
    BurpClient,
    BurpProRequired,
    BurpUnavailable,
)


@pytest.mark.asyncio
async def test_meta_returns_edition_and_version():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/meta").mock(
            return_value=httpx.Response(
                200,
                json={"ok": True, "data": {
                    "edition": "COMMUNITY_EDITION", "version": "2026.2.4", "bridge_version": "0.1.0"
                }},
            )
        )
        async with BurpClient("http://127.0.0.1:8775") as c:
            meta = await c.meta()
        assert meta["edition"] == "COMMUNITY_EDITION"


@pytest.mark.asyncio
async def test_pro_required_maps_to_exception():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/scanner/scan").mock(
            return_value=httpx.Response(
                503,
                json={"ok": False, "error": {"code": "PRO_REQUIRED", "message": "needs pro"}},
            )
        )
        async with BurpClient("http://127.0.0.1:8775") as c:
            with pytest.raises(BurpProRequired):
                await c.scanner_scan(url="https://t.example", mode="active")


@pytest.mark.asyncio
async def test_connection_refused_maps_to_unavailable():
    async with BurpClient("http://127.0.0.1:59999") as c:
        with pytest.raises(BurpUnavailable):
            await c.meta()


@pytest.mark.asyncio
async def test_bad_input_maps():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/proxy/request/999").mock(
            return_value=httpx.Response(404, json={
                "ok": False, "error": {"code": "BAD_INPUT", "message": "out of range"}
            })
        )
        async with BurpClient("http://127.0.0.1:8775") as c:
            with pytest.raises(BurpBadInput):
                await c.proxy_request(999)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/kali/Web-MCP
source .venv/bin/activate
pytest tests/test_common_burp_client.py -v
```
Expected: FAIL — `common.burp_client` not importable.

- [ ] **Step 3: Implement `common/burp_client.py`**

```python
"""Typed HTTP client for the burp-mcp-bridge extension."""
from __future__ import annotations

from typing import Any

import httpx


class BurpClientError(RuntimeError):
    """Base class for bridge errors."""


class BurpUnavailable(BurpClientError):
    """Bridge/Burp not reachable."""


class BurpProRequired(BurpClientError):
    """Operation requires Burp Suite Professional."""


class BurpBadInput(BurpClientError):
    """Bridge rejected input."""


class BurpUpstreamError(BurpClientError):
    """Bridge returned a non-standard error body."""


def _raise_for_error(resp: httpx.Response) -> dict:
    try:
        payload = resp.json()
    except Exception:
        raise BurpUpstreamError(f"non-JSON response (status={resp.status_code}): {resp.text[:200]}")
    if payload.get("ok") is True:
        return payload.get("data", {})
    err = payload.get("error", {})
    code = err.get("code")
    msg = err.get("message", "unknown error")
    if code == "PRO_REQUIRED":
        raise BurpProRequired(msg)
    if code == "BAD_INPUT":
        raise BurpBadInput(msg)
    raise BurpUpstreamError(f"{code}: {msg}")


class BurpClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BurpClient":
        self._client = httpx.AsyncClient(base_url=self._base, timeout=self._timeout)
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        assert self._client is not None
        try:
            resp = await self._client.request(method, path, **kwargs)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            raise BurpUnavailable(
                f"cannot reach bridge at {self._base}: {e} "
                f"— ensure Burp is running with burp-mcp-bridge.jar loaded"
            )
        return _raise_for_error(resp)

    # --- Endpoints ---

    async def meta(self) -> dict:
        return await self._request("GET", "/meta")

    async def proxy_history(
        self,
        *,
        host: str | None = None,
        method: str | None = None,
        status: int | None = None,
        contains: str | None = None,
        cursor: int = 0,
        limit: int = 50,
    ) -> dict:
        params: dict[str, Any] = {"cursor": cursor, "limit": limit}
        if host: params["host"] = host
        if method: params["method"] = method
        if status is not None: params["status"] = status
        if contains: params["contains"] = contains
        return await self._request("GET", "/proxy/history", params=params)

    async def proxy_request(self, request_id: int) -> dict:
        return await self._request("GET", f"/proxy/request/{request_id}")

    async def repeater_send(
        self, *, raw_base64: str, host: str, port: int, secure: bool = True, tab_name: str | None = None,
    ) -> dict:
        body = {"raw_base64": raw_base64, "host": host, "port": port, "secure": secure}
        if tab_name:
            body["tab_name"] = tab_name
        return await self._request("POST", "/repeater/send", json=body)

    async def scope_check(self, urls: list[str]) -> dict:
        return await self._request("GET", "/scope", params={"test": ",".join(urls)})

    async def scope_modify(self, *, add: list[str] | None = None, remove: list[str] | None = None) -> dict:
        return await self._request("POST", "/scope", json={"add": add or [], "remove": remove or []})

    async def sitemap(
        self, *, prefix: str | None = None, cursor: int = 0, limit: int = 200
    ) -> dict:
        params: dict[str, Any] = {"cursor": cursor, "limit": limit}
        if prefix:
            params["prefix"] = prefix
        return await self._request("GET", "/sitemap", params=params)

    async def scanner_scan(self, *, url: str, mode: str = "active") -> dict:
        return await self._request("POST", "/scanner/scan", json={"url": url, "mode": mode})

    async def scanner_issues(self) -> dict:
        return await self._request("GET", "/scanner/issues")

    async def intruder_launch(
        self, *, raw_base64: str, host: str, port: int, secure: bool = True, tab_name: str | None = None,
    ) -> dict:
        body = {"raw_base64": raw_base64, "host": host, "port": port, "secure": secure}
        if tab_name:
            body["tab_name"] = tab_name
        return await self._request("POST", "/intruder/launch", json=body)

    async def match_replace_get(self) -> dict:
        return await self._request("GET", "/match-replace")

    async def match_replace_set(self, rules: Any) -> dict:
        return await self._request("POST", "/match-replace", json={"rules": rules})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_common_burp_client.py -v
```
Expected: PASS (four tests).

- [ ] **Step 5: Commit**

```bash
git add common/burp_client.py tests/test_common_burp_client.py
git commit -m "feat(common): typed BurpClient with error mapping + respx tests"
```

---

### Task 12: burp-mcp Python package skeleton + server scaffold

**Files:**
- Create: `MCPs/burp-mcp/pyproject.toml`
- Create: `MCPs/burp-mcp/burp_mcp/__init__.py`
- Create: `MCPs/burp-mcp/burp_mcp/server.py` (stub)
- Create: `MCPs/burp-mcp/burp_mcp/tool_handlers.py` (empty module)
- Create: `MCPs/burp-mcp/tests/__init__.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "burp-mcp"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["mcp>=1.0.0", "httpx>=0.27"]

[project.scripts]
burp-mcp = "burp_mcp.server:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["burp_mcp*"]
```

- [ ] **Step 2: Write stub modules**

`MCPs/burp-mcp/burp_mcp/__init__.py`: empty file.
`MCPs/burp-mcp/burp_mcp/server.py`:
```python
"""burp-mcp stdio entry point. Wired in Task 20."""
def main() -> None:
    raise NotImplementedError("see Task 20")
if __name__ == "__main__":
    main()
```
`MCPs/burp-mcp/burp_mcp/tool_handlers.py`: empty file.
`MCPs/burp-mcp/tests/__init__.py`: empty.

- [ ] **Step 3: Editable install + import check**

```bash
cd /home/kali/Web-MCP
source .venv/bin/activate
pip install -e MCPs/burp-mcp
python -c "import burp_mcp; print('ok')"
```
Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
git add MCPs/burp-mcp/pyproject.toml MCPs/burp-mcp/burp_mcp/ MCPs/burp-mcp/tests/__init__.py
git commit -m "chore(burp-mcp): Python package skeleton"
```

---

### Task 13: `burp_proxy_history` + `burp_proxy_request` tool handlers

**Files:**
- Modify: `MCPs/burp-mcp/burp_mcp/tool_handlers.py`
- Create: `MCPs/burp-mcp/tests/test_proxy_handlers.py`

- [ ] **Step 1: Write the failing test**

`MCPs/burp-mcp/tests/test_proxy_handlers.py`:
```python
import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle


@pytest.mark.asyncio
async def test_burp_proxy_history():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/proxy/history").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"entries": [{"id": 0}], "next_cursor": None, "total": 1}
            })
        )
        result = await handle(
            "burp_proxy_history", {"host": "x.com", "limit": 10},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["ok"] is True
        assert result["data"]["total"] == 1


@pytest.mark.asyncio
async def test_burp_proxy_request_bad_id():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/proxy/request/999").mock(
            return_value=httpx.Response(404, json={
                "ok": False, "error": {"code": "BAD_INPUT", "message": "out of range"}
            })
        )
        result = await handle(
            "burp_proxy_request", {"id": 999},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["ok"] is False
        assert result["error"]["code"] == "BAD_INPUT"


@pytest.mark.asyncio
async def test_burp_unreachable():
    result = await handle(
        "burp_proxy_history", {},
        bridge_url="http://127.0.0.1:59998",
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "BURP_UNAVAILABLE"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/burp-mcp/tests/test_proxy_handlers.py -v
```
Expected: FAIL.

- [ ] **Step 3: Implement `tool_handlers.py` dispatcher + proxy handlers**

```python
"""Tool dispatcher: map MCP tool name → BurpClient call → ok/error envelope."""
from __future__ import annotations

from typing import Any

from common.burp_client import (
    BurpBadInput,
    BurpClient,
    BurpClientError,
    BurpProRequired,
    BurpUnavailable,
    BurpUpstreamError,
)
from common.mcp_base import ErrorCode, error_envelope, ok_envelope


async def handle(tool: str, args: dict, *, bridge_url: str) -> dict:
    try:
        async with BurpClient(bridge_url) as c:
            if tool == "burp_meta":
                return ok_envelope(await c.meta())
            if tool == "burp_proxy_history":
                return ok_envelope(await c.proxy_history(
                    host=args.get("host"),
                    method=args.get("method"),
                    status=args.get("status"),
                    contains=args.get("contains"),
                    cursor=int(args.get("cursor", 0)),
                    limit=int(args.get("limit", 50)),
                ))
            if tool == "burp_proxy_request":
                return ok_envelope(await c.proxy_request(int(args["id"])))
            if tool == "burp_repeater_send":
                return ok_envelope(await c.repeater_send(
                    raw_base64=args["raw_base64"], host=args["host"], port=int(args["port"]),
                    secure=bool(args.get("secure", True)), tab_name=args.get("tab_name"),
                ))
            if tool == "burp_scope_check":
                return ok_envelope(await c.scope_check(list(args.get("urls", []))))
            if tool == "burp_scope_modify":
                return ok_envelope(await c.scope_modify(
                    add=list(args.get("add", [])), remove=list(args.get("remove", []))
                ))
            if tool == "burp_sitemap":
                return ok_envelope(await c.sitemap(
                    prefix=args.get("prefix"),
                    cursor=int(args.get("cursor", 0)),
                    limit=int(args.get("limit", 200)),
                ))
            if tool == "burp_scanner_scan":
                return ok_envelope(await c.scanner_scan(
                    url=args["url"], mode=args.get("mode", "active")
                ))
            if tool == "burp_scanner_issues":
                return ok_envelope(await c.scanner_issues())
            if tool == "burp_intruder_launch":
                return ok_envelope(await c.intruder_launch(
                    raw_base64=args["raw_base64"], host=args["host"], port=int(args["port"]),
                    secure=bool(args.get("secure", True)), tab_name=args.get("tab_name"),
                ))
            if tool == "burp_match_replace_get":
                return ok_envelope(await c.match_replace_get())
            if tool == "burp_match_replace_set":
                return ok_envelope(await c.match_replace_set(args["rules"]))
            return error_envelope(ErrorCode.BAD_INPUT, f"unknown tool: {tool}")
    except BurpProRequired as e:
        return error_envelope(ErrorCode.PRO_REQUIRED, str(e))
    except BurpBadInput as e:
        return error_envelope(ErrorCode.BAD_INPUT, str(e))
    except BurpUnavailable as e:
        return error_envelope(ErrorCode.BURP_UNAVAILABLE, str(e))
    except BurpUpstreamError as e:
        return error_envelope(ErrorCode.UPSTREAM_HTTP, str(e))
    except BurpClientError as e:
        return error_envelope(ErrorCode.UPSTREAM_HTTP, str(e))
    except Exception as e:
        return error_envelope(ErrorCode.INTERNAL, f"{type(e).__name__}: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/burp-mcp/tests/test_proxy_handlers.py -v
```
Expected: PASS (three tests).

- [ ] **Step 5: Commit**

```bash
git add MCPs/burp-mcp/burp_mcp/tool_handlers.py MCPs/burp-mcp/tests/test_proxy_handlers.py
git commit -m "feat(burp-mcp): tool_handlers dispatcher + proxy history/request tests"
```

---

### Task 14: Tests for repeater, scope, sitemap handlers

**Files:**
- Create: `MCPs/burp-mcp/tests/test_other_handlers.py`

- [ ] **Step 1: Write the test** (implementations already exist in Task 13)

`MCPs/burp-mcp/tests/test_other_handlers.py`:
```python
import base64

import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle


@pytest.mark.asyncio
async def test_repeater_send():
    raw = base64.b64encode(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n").decode()
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/repeater/send").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"tab": "t"}})
        )
        result = await handle(
            "burp_repeater_send",
            {"raw_base64": raw, "host": "x.com", "port": 443},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["ok"] is True
        assert result["data"]["tab"] == "t"


@pytest.mark.asyncio
async def test_scope_modify():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/scope").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"added": ["https://x.com"], "removed": []}
            })
        )
        result = await handle(
            "burp_scope_modify",
            {"add": ["https://x.com"]},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["data"]["added"] == ["https://x.com"]


@pytest.mark.asyncio
async def test_sitemap():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/sitemap").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"entries": [{"id": 0, "url": "https://x.com/"}],
                                     "next_cursor": None, "total": 1}
            })
        )
        result = await handle(
            "burp_sitemap", {"prefix": "https://x.com"},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["data"]["total"] == 1
```

- [ ] **Step 2: Run test**

```bash
pytest MCPs/burp-mcp/tests/test_other_handlers.py -v
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add MCPs/burp-mcp/tests/test_other_handlers.py
git commit -m "test(burp-mcp): repeater/scope/sitemap handler coverage"
```

---

### Task 15: Scanner + Intruder + match-replace handler tests

**Files:**
- Create: `MCPs/burp-mcp/tests/test_pro_handlers.py`

- [ ] **Step 1: Write the test**

```python
import base64

import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle


@pytest.mark.asyncio
async def test_scanner_scan_on_community_returns_pro_required():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/scanner/scan").mock(
            return_value=httpx.Response(503, json={
                "ok": False, "error": {"code": "PRO_REQUIRED", "message": "needs pro"}
            })
        )
        result = await handle(
            "burp_scanner_scan", {"url": "https://x.com"},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["error"]["code"] == "PRO_REQUIRED"


@pytest.mark.asyncio
async def test_scanner_issues_on_pro():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/scanner/issues").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"issues": [{"id": 0, "name": "Sec"}], "total": 1}
            })
        )
        result = await handle(
            "burp_scanner_issues", {}, bridge_url="http://127.0.0.1:8775",
        )
        assert result["data"]["total"] == 1


@pytest.mark.asyncio
async def test_intruder_launch_on_community():
    raw = base64.b64encode(b"GET /").decode()
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/intruder/launch").mock(
            return_value=httpx.Response(503, json={
                "ok": False, "error": {"code": "PRO_REQUIRED", "message": "needs pro"}
            })
        )
        result = await handle(
            "burp_intruder_launch",
            {"raw_base64": raw, "host": "x.com", "port": 443},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["error"]["code"] == "PRO_REQUIRED"


@pytest.mark.asyncio
async def test_match_replace_get_and_set():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/match-replace").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"rules": []}
            })
        )
        mock.post("/match-replace").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"applied": True}
            })
        )
        g = await handle("burp_match_replace_get", {}, bridge_url="http://127.0.0.1:8775")
        assert g["data"]["rules"] == []
        s = await handle(
            "burp_match_replace_set",
            {"rules": [{"enabled": True, "type": "request_header",
                        "match": "X-Test: old", "replace": "X-Test: new"}]},
            bridge_url="http://127.0.0.1:8775",
        )
        assert s["data"]["applied"] is True
```

- [ ] **Step 2: Run test**

```bash
pytest MCPs/burp-mcp/tests/test_pro_handlers.py -v
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add MCPs/burp-mcp/tests/test_pro_handlers.py
git commit -m "test(burp-mcp): scanner/intruder/match-replace handler coverage"
```

---

### Task 16: burp-mcp MCP stdio server entry point

**Files:**
- Modify: `MCPs/burp-mcp/burp_mcp/server.py`
- Modify: `claude_config.example.json` (add burp-mcp block)
- Create: `MCPs/burp-mcp/README.md`

- [ ] **Step 1: Implement `server.py`**

```python
"""burp-mcp stdio server: registers tools and dispatches via tool_handlers.handle."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from common.config import load_config
from common.logging import setup_logger

from .tool_handlers import handle


WORKSPACE = Path(__file__).resolve().parents[3]


def _tool_schemas() -> list[Tool]:
    return [
        Tool(name="burp_meta", description="Burp edition/version and bridge version.",
             inputSchema={"type": "object"}),
        Tool(
            name="burp_proxy_history",
            description="Paginated proxy history with optional filters (host/method/status/contains).",
            inputSchema={"type": "object", "properties": {
                "host": {"type": "string"}, "method": {"type": "string"},
                "status": {"type": "integer"}, "contains": {"type": "string"},
                "cursor": {"type": "integer"}, "limit": {"type": "integer"},
            }},
        ),
        Tool(
            name="burp_proxy_request",
            description="Full request + response for a given history id.",
            inputSchema={"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}},
        ),
        Tool(
            name="burp_repeater_send",
            description="Send a raw request to Repeater in a new tab.",
            inputSchema={"type": "object", "required": ["raw_base64", "host", "port"], "properties": {
                "raw_base64": {"type": "string"}, "host": {"type": "string"}, "port": {"type": "integer"},
                "secure": {"type": "boolean"}, "tab_name": {"type": "string"},
            }},
        ),
        Tool(
            name="burp_scope_check",
            description="Test whether URLs are in scope.",
            inputSchema={"type": "object", "required": ["urls"],
                         "properties": {"urls": {"type": "array", "items": {"type": "string"}}}},
        ),
        Tool(
            name="burp_scope_modify",
            description="Add and/or remove URLs from scope.",
            inputSchema={"type": "object", "properties": {
                "add": {"type": "array", "items": {"type": "string"}},
                "remove": {"type": "array", "items": {"type": "string"}},
            }},
        ),
        Tool(
            name="burp_sitemap",
            description="Site map entries, optionally filtered by URL prefix.",
            inputSchema={"type": "object", "properties": {
                "prefix": {"type": "string"}, "cursor": {"type": "integer"}, "limit": {"type": "integer"},
            }},
        ),
        Tool(
            name="burp_scanner_scan",
            description="Start an audit (Pro only). mode: active|passive.",
            inputSchema={"type": "object", "required": ["url"], "properties": {
                "url": {"type": "string"}, "mode": {"type": "string", "enum": ["active", "passive"]},
            }},
        ),
        Tool(name="burp_scanner_issues", description="List scan issues (Pro only).",
             inputSchema={"type": "object"}),
        Tool(
            name="burp_intruder_launch",
            description="Send a raw request to Intruder (Pro only).",
            inputSchema={"type": "object", "required": ["raw_base64", "host", "port"], "properties": {
                "raw_base64": {"type": "string"}, "host": {"type": "string"}, "port": {"type": "integer"},
                "secure": {"type": "boolean"}, "tab_name": {"type": "string"},
            }},
        ),
        Tool(name="burp_match_replace_get", description="Read match-and-replace rules.",
             inputSchema={"type": "object"}),
        Tool(
            name="burp_match_replace_set",
            description="Replace match-and-replace rules with the supplied array.",
            inputSchema={"type": "object", "required": ["rules"], "properties": {"rules": {}}},
        ),
    ]


async def _async_main() -> None:
    cfg = load_config(WORKSPACE / "config.toml")
    logger = setup_logger("burp-mcp", log_dir=WORKSPACE / cfg.logging.dir, level=cfg.logging.level)
    logger.info("startup", extra={"bridge": cfg.burp.bridge_url})

    server = Server("burp-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _tool_schemas()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        result = await handle(name, arguments or {}, bridge_url=cfg.burp.bridge_url)
        return [TextContent(type="text", text=json.dumps(result))]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add burp-mcp to `claude_config.example.json`**

Replace `claude_config.example.json` with:
```json
{
  "mcpServers": {
    "browser-mcp": {
      "command": "/home/kali/Web-MCP/.venv/bin/python",
      "args": ["-m", "browser_mcp.server"]
    },
    "burp-mcp": {
      "command": "/home/kali/Web-MCP/.venv/bin/python",
      "args": ["-m", "burp_mcp.server"]
    }
  }
}
```

- [ ] **Step 3: Write `MCPs/burp-mcp/README.md`**

```markdown
# burp-mcp

MCP server wrapping Burp Suite via the `burp-mcp-bridge` Kotlin extension.

## Setup
1. Build the Kotlin extension (see `burp-ext/BUILD.md`).
2. Load the jar in Burp (Extensions → Add → Java).
3. Verify: `curl -s http://127.0.0.1:8775/meta`.
4. Register this MCP in Claude Code (see top-level `claude_config.example.json`).

## Tools
- Read: `burp_meta`, `burp_proxy_history`, `burp_proxy_request`, `burp_sitemap`, `burp_match_replace_get`, `burp_scope_check`.
- Write (active testing): `burp_repeater_send`, `burp_scope_modify`, `burp_match_replace_set`.
- Pro-only: `burp_scanner_scan`, `burp_scanner_issues`, `burp_intruder_launch`. On Community these return `PRO_REQUIRED`.
```

- [ ] **Step 4: Run full test suite**

```bash
cd /home/kali/Web-MCP
source .venv/bin/activate
pytest -v
```
Expected: all tests pass across `common/`, `browser-mcp`, `burp-mcp`.

- [ ] **Step 5: Commit**

```bash
git add MCPs/burp-mcp/burp_mcp/server.py claude_config.example.json MCPs/burp-mcp/README.md
git commit -m "feat(burp-mcp): stdio MCP server entry point + Claude config block"
```

---

## Plan-end verification

- [ ] `gradle shadowJar` in `burp-ext/` produces a working jar.
- [ ] Jar loads in Burp without errors; `curl http://127.0.0.1:8775/meta` succeeds.
- [ ] Full pytest run passes on `common/`, `browser-mcp`, `burp-mcp`.
- [ ] Claude Code `/mcp` lists both `browser-mcp` and `burp-mcp` as connected.
- [ ] Manual prompt: "use browser_navigate through port 8080 to httpbin.org/get, then query burp_proxy_history for that request" — end-to-end confirmation.
