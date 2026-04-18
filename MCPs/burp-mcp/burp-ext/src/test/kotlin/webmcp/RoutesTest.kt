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
    fun `http send route registered and validates body`() {
        val router = Router(api = FakeApi())
        registerHttpSendRoutes(router)
        val r = router.dispatch("POST", "/http/send", emptyMap(), "{}")
        assertEquals(400, r.status)
        assertTrue(r.body().contains("BAD_INPUT"))
    }

    @Test
    fun `http send rejects invalid base64`() {
        val router = Router(api = FakeApi())
        registerHttpSendRoutes(router)
        val r = router.dispatch("POST", "/http/send", emptyMap(),
            """{"raw_base64":"!!!not-b64","host":"x","port":80}""")
        assertEquals(400, r.status)
        assertTrue(r.body().contains("BAD_INPUT"))
    }

    @Test
    fun `json roundtrip`() {
        val payload = mapOf("ok" to true, "data" to listOf(1, "two", mapOf("k" to null)))
        val encoded = Json.encode(payload)
        val decoded = Json.decode(encoded) as Map<*, *>
        assertEquals(true, decoded["ok"])
    }
}

class FakeApi(private val burp: burp.api.montoya.burpsuite.BurpSuite? = null) : burp.api.montoya.MontoyaApi {
    override fun burpSuite(): burp.api.montoya.burpsuite.BurpSuite = burp ?: throw NotImplementedError()
    override fun collaborator(): burp.api.montoya.collaborator.Collaborator = throw NotImplementedError()
    override fun comparer(): burp.api.montoya.comparer.Comparer = throw NotImplementedError()
    override fun decoder(): burp.api.montoya.decoder.Decoder = throw NotImplementedError()
    override fun extension(): burp.api.montoya.extension.Extension = throw NotImplementedError()
    override fun http(): burp.api.montoya.http.Http = throw NotImplementedError()
    override fun intruder(): burp.api.montoya.intruder.Intruder = throw NotImplementedError()
    override fun logging(): burp.api.montoya.logging.Logging = throw NotImplementedError()
    override fun organizer(): burp.api.montoya.organizer.Organizer = throw NotImplementedError()
    override fun persistence(): burp.api.montoya.persistence.Persistence = throw NotImplementedError()
    override fun project(): burp.api.montoya.project.Project = throw NotImplementedError()
    override fun proxy(): burp.api.montoya.proxy.Proxy = throw NotImplementedError()
    override fun repeater(): burp.api.montoya.repeater.Repeater = throw NotImplementedError()
    override fun scanner(): burp.api.montoya.scanner.Scanner = throw NotImplementedError()
    override fun scope(): burp.api.montoya.scope.Scope = throw NotImplementedError()
    override fun siteMap(): burp.api.montoya.sitemap.SiteMap = throw NotImplementedError()
    override fun userInterface(): burp.api.montoya.ui.UserInterface = throw NotImplementedError()
    override fun utilities(): burp.api.montoya.utilities.Utilities = throw NotImplementedError()
    override fun websockets(): burp.api.montoya.websocket.WebSockets = throw NotImplementedError()
}

class FakeBurpSuite : burp.api.montoya.burpsuite.BurpSuite {
    var importedProjectJson: String? = null
    var exportedProjectPaths: List<String>? = null
    var projectOptionsFixture: String = """{"proxy":{"match_replace_rules":[{"enabled":true}]}}"""

    override fun exportProjectOptionsAsJson(vararg paths: String): String {
        exportedProjectPaths = paths.toList()
        return projectOptionsFixture
    }
    override fun importProjectOptionsFromJson(json: String) { importedProjectJson = json }
    override fun exportUserOptionsAsJson(vararg paths: String): String =
        error("match-replace must use project options, not user options")
    override fun importUserOptionsFromJson(json: String): Unit =
        error("match-replace must use project options, not user options")
    override fun version(): burp.api.montoya.core.Version = throw NotImplementedError()
    override fun commandLineArguments(): List<String> = throw NotImplementedError()
    override fun shutdown(vararg options: burp.api.montoya.burpsuite.ShutdownOptions): Unit = throw NotImplementedError()
    override fun taskExecutionEngine(): burp.api.montoya.burpsuite.TaskExecutionEngine = throw NotImplementedError()
}

class MatchReplaceRoutesTest {
    @Test
    fun `GET reads project options at proxy match_replace_rules`() {
        val burp = FakeBurpSuite()
        val router = Router(api = FakeApi(burp))
        registerMatchReplaceRoutes(router)

        val r = router.dispatch("GET", "/match-replace", emptyMap(), null)
        assertEquals(200, r.status)
        assertEquals(listOf("proxy.match_replace_rules"), burp.exportedProjectPaths)
        assertTrue(r.body().contains("\"enabled\":true"), "rules should round-trip from project options, got: ${r.body()}")
    }

    @Test
    fun `POST writes project options without user_options wrapper`() {
        val burp = FakeBurpSuite()
        val router = Router(api = FakeApi(burp))
        registerMatchReplaceRoutes(router)

        val r = router.dispatch("POST", "/match-replace", emptyMap(),
            """{"rules":[{"enabled":true,"rule_type":"request_header","string_match":"X: a","string_replace":"X: b"}]}""")
        assertEquals(200, r.status)
        val sent = requireNotNull(burp.importedProjectJson) { "importProjectOptionsFromJson was never called" }
        val decoded = Json.decode(sent) as Map<*, *>
        assertTrue(decoded.containsKey("proxy"), "expected top-level 'proxy' key, got: $sent")
        assertTrue(!decoded.containsKey("user_options"), "must not wrap in user_options, got: $sent")
        val rules = (decoded["proxy"] as Map<*, *>)["match_replace_rules"] as List<*>
        assertEquals(1, rules.size)
    }
}
