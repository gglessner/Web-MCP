package webmcp

import burp.api.montoya.http.message.requests.HttpRequest
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
        // Montoya Audit has no addUrl(); use addRequest() with a URL-derived request instead.
        task.addRequest(HttpRequest.httpRequestFromUrl(url))
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
