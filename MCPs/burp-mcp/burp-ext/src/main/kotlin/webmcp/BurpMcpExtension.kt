package webmcp

import burp.api.montoya.BurpExtension
import burp.api.montoya.MontoyaApi

class BurpMcpExtension : BurpExtension {
    private var server: HttpBridgeServer? = null

    override fun initialize(api: MontoyaApi) {
        api.extension().setName("burp-mcp-bridge")
        val port = 8775
        server = HttpBridgeServer(api, port).also { it.start() }
        api.logging().logToOutput("burp-mcp-bridge listening on 127.0.0.1:$port")
        api.extension().registerUnloadingHandler {
            server?.stop()
            api.logging().logToOutput("burp-mcp-bridge stopped")
        }
    }
}
