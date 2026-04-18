package webmcp

fun registerMatchReplaceRoutes(router: Router) {
    router.register("GET", "/match-replace") { ctx ->
        val settings = ctx.api.burpSuite().exportProjectOptionsAsJson("proxy.match_replace_rules")
        val parsed = Json.decode(settings) as? Map<*, *>
        val rules = (parsed?.get("proxy") as? Map<*, *>)?.get("match_replace_rules")
        Response(200, mapOf("ok" to true, "data" to mapOf("rules" to rules)))
    }

    router.register("POST", "/match-replace") { ctx ->
        val body = ctx.bodyJson ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "JSON body required")
        ))
        val rules = body["rules"] ?: return@register Response(400, mapOf(
            "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to "rules required")
        ))
        val wrapped = mapOf("proxy" to mapOf("match_replace_rules" to rules))
        ctx.api.burpSuite().importProjectOptionsFromJson(Json.encode(wrapped))
        Response(200, mapOf("ok" to true, "data" to mapOf("applied" to true)))
    }
}
