package webmcp

/** Dependency-free JSON writer/reader sufficient for the bridge's flat payloads. */
object Json {
    fun encode(value: Any?): String {
        val sb = StringBuilder()
        write(sb, value)
        return sb.toString()
    }

    private fun write(sb: StringBuilder, value: Any?) {
        when (value) {
            null -> sb.append("null")
            is Boolean -> sb.append(value)
            is Number -> sb.append(value)
            is String -> encodeString(sb, value)
            is Map<*, *> -> {
                sb.append('{')
                value.entries.forEachIndexed { i, (k, v) ->
                    if (i > 0) sb.append(',')
                    encodeString(sb, k.toString())
                    sb.append(':')
                    write(sb, v)
                }
                sb.append('}')
            }
            is Iterable<*> -> {
                sb.append('[')
                value.forEachIndexed { i, v ->
                    if (i > 0) sb.append(',')
                    write(sb, v)
                }
                sb.append(']')
            }
            else -> encodeString(sb, value.toString())
        }
    }

    private fun encodeString(sb: StringBuilder, s: String) {
        sb.append('"')
        for (c in s) {
            when (c) {
                '"' -> sb.append("\\\"")
                '\\' -> sb.append("\\\\")
                '\n' -> sb.append("\\n")
                '\r' -> sb.append("\\r")
                '\t' -> sb.append("\\t")
                '\b' -> sb.append("\\b")
                '\u000C' -> sb.append("\\f")
                else -> if (c.code < 0x20) sb.append("\\u%04x".format(c.code)) else sb.append(c)
            }
        }
        sb.append('"')
    }

    /** Minimal JSON parser — handles objects/arrays/strings/numbers/bool/null. */
    fun decode(s: String): Any? = Parser(s).parseValue().also { Parser(s).skipTrailing() }

    private class Parser(val src: String) {
        var i = 0
        fun parseValue(): Any? {
            skipWs()
            if (i >= src.length) error("empty")
            return when (src[i]) {
                '{' -> parseObject()
                '[' -> parseArray()
                '"' -> parseString()
                't', 'f' -> parseBool()
                'n' -> parseNull()
                else -> parseNumber()
            }
        }
        fun parseObject(): LinkedHashMap<String, Any?> {
            expect('{'); val out = LinkedHashMap<String, Any?>()
            skipWs(); if (peek() == '}') { i++; return out }
            while (true) {
                skipWs(); val k = parseString(); skipWs(); expect(':')
                out[k] = parseValue(); skipWs()
                if (peek() == ',') { i++; continue }
                expect('}'); return out
            }
        }
        fun parseArray(): ArrayList<Any?> {
            expect('['); val out = ArrayList<Any?>()
            skipWs(); if (peek() == ']') { i++; return out }
            while (true) {
                out.add(parseValue()); skipWs()
                if (peek() == ',') { i++; continue }
                expect(']'); return out
            }
        }
        fun parseString(): String {
            expect('"'); val sb = StringBuilder()
            while (i < src.length) {
                val c = src[i++]
                if (c == '"') return sb.toString()
                if (c == '\\') {
                    val esc = src[i++]
                    sb.append(when (esc) {
                        '"' -> '"'; '\\' -> '\\'; '/' -> '/'
                        'n' -> '\n'; 'r' -> '\r'; 't' -> '\t'
                        'b' -> '\b'; 'f' -> '\u000C'
                        'u' -> { val hex = src.substring(i, i + 4); i += 4; hex.toInt(16).toChar() }
                        else -> error("bad escape: $esc")
                    })
                } else sb.append(c)
            }
            error("unterminated string")
        }
        fun parseNumber(): Number {
            val start = i
            if (peek() == '-') i++
            while (i < src.length && (src[i].isDigit() || src[i] == '.' || src[i] == 'e' || src[i] == 'E' || src[i] == '+' || src[i] == '-')) i++
            val tok = src.substring(start, i)
            return if (tok.contains('.') || tok.contains('e') || tok.contains('E')) tok.toDouble() else tok.toLong()
        }
        fun parseBool(): Boolean =
            if (src.startsWith("true", i)) { i += 4; true }
            else if (src.startsWith("false", i)) { i += 5; false }
            else error("bad bool")
        fun parseNull(): Any? = if (src.startsWith("null", i)) { i += 4; null } else error("bad null")
        fun skipWs() { while (i < src.length && src[i].isWhitespace()) i++ }
        fun skipTrailing() { skipWs() }
        fun peek(): Char? = if (i < src.length) src[i] else null
        fun expect(c: Char) { if (peek() != c) error("expected '$c' at $i") ; i++ }
    }
}
