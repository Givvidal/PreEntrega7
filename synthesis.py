from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from state import AgentState


llm_sintesis = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)


async def nodo_sintesis(state: AgentState) -> dict:
    contribuciones_texto = "\n".join(
        f"- [{c['agente']}] {c['aporte']}"
        for c in state.get("contribuciones", [])
    )

    pregunta_original = state["messages"][0].content

    prompt = (
        f"Pregunta original: {pregunta_original}\n\n"
        f"Aportes del equipo:\n{contribuciones_texto}\n\n"
        "Redactá una respuesta final clara y breve combinando estos aportes."
    )

    respuesta_final = await llm_sintesis.ainvoke(prompt)

    return {
        "messages": [
            AIMessage(
                content=respuesta_final.content,
                name="supervisor",
            )
        ]
    }