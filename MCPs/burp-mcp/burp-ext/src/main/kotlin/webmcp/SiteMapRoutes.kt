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
                "status" to h.response()?.statusCode()?.toInt(),
            )
        }
        val nextCursor = if (cursor + limit < entries.size) cursor + limit else null
        Response(200, mapOf("ok" to true, "data" to mapOf(
            "entries" to list, "next_cursor" to nextCursor, "total" to entries.size
        )))
    }
}
