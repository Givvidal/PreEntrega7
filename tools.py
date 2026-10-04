import ast
import operator as op
from langchain_core.tools import tool
from rag_system import RAGSystem

rag_system = RAGSystem()

@tool
async def buscar_en_rag(pregunta: str) -> str:
    """Busca información en los documentos almacenados en el sistema RAG.
    Usar cuando se necesite obtener datos concretos de las fuentes disponibles."""
    resultados = await rag_system.obtener_top_k(pregunta)
    if not resultados:
        return "No se encontró información relevante en el RAG."
    return "\n\n".join(f"[Fuente: {r['fuente']}] {r['contenido']}" for r in resultados)



_OPERADORES = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg,
}


def _evaluar_nodo(nodo):
    if isinstance(nodo, ast.Constant):
        return nodo.value
    if isinstance(nodo, ast.BinOp):
        return _OPERADORES[type(nodo.op)](_evaluar_nodo(nodo.left), _evaluar_nodo(nodo.right))
    if isinstance(nodo, ast.UnaryOp):
        return _OPERADORES[type(nodo.op)](_evaluar_nodo(nodo.operand))
    raise ValueError("Expresión no permitida")


@tool
def calculadora(expresion: str) -> str:
    """Evalúa una expresión matemática (+, -, *, /, **, paréntesis). Ejemplo: '5*14 + 5*21 + 2*28'."""
    try:
        resultado = _evaluar_nodo(ast.parse(expresion, mode="eval").body)
        return f"Resultado: {resultado}"
    except Exception as e:
        return f"Error al calcular '{expresion}': {e}"