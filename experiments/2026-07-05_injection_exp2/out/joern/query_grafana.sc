importCpg("/Users/akhattab/ai/experiments/2026-07-05_injection_exp2/out/joern/cpg_grafana.bin")
import upickle.default._

val symbols = List("BusEventWithPayload", "GrafanaPlugin", "MutableDataFrame", "Registry", "createDataFrame", "createTheme", "getDisplayProcessor", "getFieldDisplayName", "toDataFrame", "transformDataFrame")

def edgesFor(sym: String): List[Map[String,String]] = {
  val mc = cpg.method.nameExact(sym).flatMap { m =>
    m.callIn.l.map { call =>
      val cm = call.method
      Map("callee"->m.name, "callee_file"->m.filename, "caller"->cm.name,
          "caller_file"->cm.filename, "line"->call.lineNumber.getOrElse(-1).toString,
          "kind"->"method_callIn")
    }
  }.l
  val cs = cpg.call.nameExact(sym).l.map { call =>
    val cm = call.method
    Map("callee"->sym, "callee_file"->"", "caller"->cm.name,
        "caller_file"->cm.filename, "line"->call.lineNumber.getOrElse(-1).toString,
        "kind"->"call_site")
  }
  val tc = cpg.typeDecl.nameExact(sym).flatMap { t =>
    t.method.flatMap { m =>
      m.callIn.l.map { call =>
        val cm = call.method
        Map("callee"->(sym+"."+m.name), "callee_file"->m.filename, "caller"->cm.name,
            "caller_file"->cm.filename, "line"->call.lineNumber.getOrElse(-1).toString,
            "kind"->"type_method_callIn")
      }
    }
  }.l
  (mc ++ cs ++ tc).distinct
}

val result = symbols.map(s => (s, edgesFor(s))).toMap
val pw = new java.io.PrintWriter("/Users/akhattab/ai/experiments/2026-07-05_injection_exp2/out/joern/edges_grafana.json")
pw.write(write(result, indent=2))
pw.close()
println("JOERN_QUERY_DONE")
