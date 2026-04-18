package webmcp

import burp.api.montoya.proxy.ProxyHttpRequestResponse
import java.util.Base64

fun registerProxyRoutes(router: Router) {
    router.register("GET", "/proxy/history") { ctx ->
        val host = ctx.query["host"]
        val method = ctx.query["method"]
        val status = ctx.query["status"]?.toIntOrNull()
        val contains = ctx.query["contains"]
        val limit = (ctx.query["limit"]?.toIntOrNull() ?: 50).coerceAtMost(500)
        val cursor = ctx.query["cursor"]?.toIntOrNull() ?: 0

        val all: List<ProxyHttpRequestResponse> = ctx.api.proxy().history()
        val filtered = all.asSequence()
            .filter { host == null || it.finalRequest().httpService().host() == host }
            .filter { method == null || it.finalRequest().method().equals(method, ignoreCase = true) }
            .filter { status == null || (it.originalResponse()?.statusCode()?.toInt() ?: -1) == status }
            .filter { contains == null || it.contains(contains, false) }
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
        "status" to resp?.statusCode()?.toInt(),
        "mime" to resp?.statedMimeType()?.toString(),
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
        "response" to resp?.let {
            mapOf(
                "status" to it.statusCode().toInt(),
                "raw_base64" to Base64.getEncoder().encodeToString(it.toByteArray().bytes),
            )
        },
    )
}
