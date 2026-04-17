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
