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
        val rawBytes = runCatching { Base64.getDecoder().decode(rawB64) }.getOrElse {
            return@register Response(400, mapOf("ok" to false, "error" to mapOf(
                "code" to "BAD_INPUT", "message" to "raw_base64 is not valid base64")))
        }
        val service = HttpService.httpService(host, port, secure)
        val req = HttpRequest.httpRequest(service, MByteArray.byteArray(*rawBytes))
        ctx.api.repeater().sendToRepeater(req, tabName)
        Response(200, mapOf("ok" to true, "data" to mapOf("tab" to tabName)))
    }
}
