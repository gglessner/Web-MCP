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
                "edition" to edition,
                "version" to version,
                "bridge_version" to "0.1.0",
            ),
        ))
    }
}
