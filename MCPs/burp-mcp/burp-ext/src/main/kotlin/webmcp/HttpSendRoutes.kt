package webmcp

import burp.api.montoya.core.ByteArray as MByteArray
import burp.api.montoya.http.HttpService
import burp.api.montoya.http.message.requests.HttpRequest
import java.util.Base64

private fun badInput(msg: String) = mapOf(
    "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to msg)
)

fun registerHttpSendRoutes(router: Router) {
    router.register("POST", "/http/send") { ctx ->
        val body = ctx.bodyJson
            ?: return@register Response(400, badInput("JSON body required"))
        val rawB64 = body["raw_base64"] as? String
        val host = body["host"] as? String
        val port = (body["port"] as? Number)?.toInt()
        val secure = body["secure"] as? Boolean ?: true
        if (rawB64 == null || host == null || port == null) {
            return@register Response(400, badInput("raw_base64, host, port required"))
        }
        val rawBytes = runCatching { Base64.getDecoder().decode(rawB64) }.getOrElse {
            return@register Response(400, badInput("raw_base64 is not valid base64"))
        }
        val service = HttpService.httpService(host, port, secure)
        val req = HttpRequest.httpRequest(service, MByteArray.byteArray(*rawBytes))
        val t0 = System.nanoTime()
        val rr = ctx.api.http().sendRequest(req)
        val ms = (System.nanoTime() - t0) / 1_000_000
        val resp = rr.response()
        Response(200, mapOf(
            "ok" to true,
            "data" to mapOf(
                "status" to resp?.statusCode()?.toInt(),
                "headers" to resp?.headers()?.map {
                    mapOf("name" to it.name(), "value" to it.value())
                },
                "body_base64" to resp?.body()?.let {
                    Base64.getEncoder().encodeToString(it.bytes)
                },
                "body_len" to (resp?.body()?.length() ?: 0),
                "request_base64" to Base64.getEncoder()
                    .encodeToString(req.toByteArray().bytes),
                "time_ms" to ms,
            ),
        ))
    }
}
