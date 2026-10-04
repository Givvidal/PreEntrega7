import asyncio
import json
import traceback

from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from redis.asyncio import Redis

REDIS_URL = "redis://localhost:6379"
QUEUE_NAME = "tasks_queue"
STATUS_PREFIX = "task:"


async def guardar_estado(redis: Redis, job_id: str, estado: dict):
    await redis.set(
        f"{STATUS_PREFIX}{job_id}",
        json.dumps(estado),
    )


async def worker(app: FastAPI):
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    graph = app.state.graph

    while True:
        job_id = await redis.lpop(QUEUE_NAME)

        if job_id is None:
            await asyncio.sleep(0.5)
            continue

        datos = await redis.get(f"{STATUS_PREFIX}{job_id}")

        if datos is None:
            continue

        tarea = json.loads(datos)

        await guardar_estado(
            redis,
            job_id,
            {
                **tarea,
                "status": "RUNNING",
            },
        )

        try:
            resultado_grafo = await graph.ainvoke(
                {
                    "messages": [HumanMessage(content=tarea["query"])],
                    "requires_approval": tarea.get("requires_approval", False),
                },
                config={"configurable": {"thread_id": job_id}},
            )

            interrupciones = resultado_grafo.get("__interrupt__")

            if interrupciones:
                await guardar_estado(
                    redis,
                    job_id,
                    {**tarea, "status": "WAITING_APPROVAL"},
                )
                continue

            await guardar_estado(
                redis,
                job_id,
                {
                    **tarea,
                    "status": "DONE",
                    "result": resultado_grafo["messages"][-1].content,
                },
            )

        except Exception as e:
            traceback.print_exc()

            await guardar_estado(
                redis,
                job_id,
                {
                    **tarea,
                    "status": "FAILED",
                    "error": str(e),
                },
            )