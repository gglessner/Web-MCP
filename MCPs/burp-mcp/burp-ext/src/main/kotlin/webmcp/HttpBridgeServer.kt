package webmcp

import burp.api.montoya.MontoyaApi
import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.nio.charset.StandardCharsets
import java.util.concurrent.Executors

class HttpBridgeServer(private val api: MontoyaApi, private val port: Int) {
    private val server: HttpServer = HttpServer.create(InetSocketAddress("127.0.0.1", port), 0)
    private val router = Router(api)

    init {
        registerMetaRoute(router)
        registerProxyRoutes(router)
        registerRepeaterRoutes(router)
        registerScopeRoutes(router)
        registerSiteMapRoutes(router)
        registerScannerRoutes(router)
        registerIntruderRoutes(router)
        registerMatchReplaceRoutes(router)
        server.executor = Executors.newFixedThreadPool(4)
        server.createContext("/") { exchange -> handle(exchange) }
    }

    fun routerInstance(): Router = router

    fun start() { server.start() }

    fun stop() { server.stop(0) }

    private fun handle(exchange: HttpExchange) {
        try {
            val method = exchange.requestMethod
            val uri = exchange.requestURI
            val path = uri.rawPath ?: "/"
            val query = (uri.rawQuery ?: "").split("&").filter { it.isNotBlank() }.associate {
                val eq = it.indexOf('=')
                if (eq < 0) it to "" else java.net.URLDecoder.decode(it.substring(0, eq), "UTF-8") to
                    java.net.URLDecoder.decode(it.substring(eq + 1), "UTF-8")
            }
            val body = exchange.requestBody.readBytes().toString(StandardCharsets.UTF_8)

            val resp = router.dispatch(method, path, query, body)
            val bytes = resp.body().toByteArray(StandardCharsets.UTF_8)
            exchange.responseHeaders.add("Content-Type", "application/json")
            exchange.sendResponseHeaders(resp.status, bytes.size.toLong())
            exchange.responseBody.use { it.write(bytes) }
        } catch (t: Throwable) {
            val err = Json.encode(mapOf("ok" to false, "error" to mapOf(
                "code" to "INTERNAL", "message" to (t.message ?: t::class.simpleName)
            ))).toByteArray()
            exchange.sendResponseHeaders(500, err.size.toLong())
            exchange.responseBody.use { it.write(err) }
        } finally {
            exchange.close()
        }
    }
}
