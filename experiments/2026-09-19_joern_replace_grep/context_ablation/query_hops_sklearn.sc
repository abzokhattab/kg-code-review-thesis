importCpg("/Users/akhattab/ai/experiments/2026-07-05_injection_exp2/out/joern/cpg_sklearn.bin")
import upickle.default._

val symbols = List("BaseEstimator", "LinearClassifierMixin", "LinearModel", "LinearModelLoss", "TransformerMixin", "_fit_context", "_preprocess_data", "clone", "k_means", "sag_solver")
val MAX_HOPS = 3

def bfsCallers(startSym: String): List[Map[String,String]] = {
  var frontier = cpg.method.nameExact(startSym).l
  var visited = frontier.map(_.fullName).toSet
  var allEdges: List[Map[String,String]] = List()

  for (hop <- 1 to MAX_HOPS) {
    var nextFrontier: List[io.shiftleft.codepropertygraph.generated.nodes.Method] = List()
    for (m <- frontier) {
      val callers = m.callIn.l.flatMap { call =>
        val cm = call.method
        if (!visited.contains(cm.fullName)) {
          visited = visited + cm.fullName
          nextFrontier = cm :: nextFrontier
          Some(Map(
            "callee" -> m.name,
            "callee_file" -> m.filename,
            "caller" -> cm.name,
            "caller_file" -> cm.filename,
            "line" -> call.lineNumber.getOrElse(-1).toString,
            "hop" -> hop.toString,
            "root_symbol" -> startSym
          ))
        } else None
      }
      allEdges = allEdges ++ callers
    }
    frontier = nextFrontier.distinct
  }
  allEdges
}

val result = symbols.map(s => (s, bfsCallers(s))).toMap
val pw = new java.io.PrintWriter("/Users/akhattab/ai/experiments/2026-09-19_joern_replace_grep/context_ablation/hops_sklearn.json")
pw.write(write(result, indent=2))
pw.close()
println("JOERN_MULTIHOP_DONE")
