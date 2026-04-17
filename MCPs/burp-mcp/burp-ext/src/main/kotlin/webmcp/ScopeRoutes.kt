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
