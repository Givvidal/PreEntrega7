from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor


def configurar_phoenix():
    tracer_provider = register(
        project_name="PreEntrega7",
        endpoint="http://localhost:6006/v1/traces",
    )

    LangChainInstrumentor().instrument(
        tracer_provider=tracer_provider
    )