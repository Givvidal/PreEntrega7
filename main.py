import uuid
import asyncio
import json
from contextlib import asynccontextmanager
from langgraph.types import Command
from fastapi import FastAPI, HTTPException
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from pydantic import BaseModel
from redis.asyncio import Redis
from app.observability import configurar_phoenix
from app.graph import crear_app
from app.worker import (
    REDIS_URL,
    QUEUE_NAME,
    STATUS_PREFIX,
    guardar_estado,
    worker,
)



class TaskRequest(BaseModel):
    query: str
    requires_approval: bool = False



@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )

    async with AsyncRedisSaver.from_conn_string(REDIS_URL) as checkpointer:

        await checkpointer.asetup()

        app.state.redis = redis
        app.state.checkpointer = checkpointer
        app.state.graph = crear_app(checkpointer)

        worker_task = asyncio.create_task(worker(app))
        print("WORKER CREADO:", not worker_task.done())

        yield

        worker_task.cancel()

        try:
            await worker_task
        except asyncio.CancelledError:
            pass

        await redis.aclose()


configurar_phoenix()

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def inicio():
    return {"estado": "API funcionando"}


@app.post("/tasks")
async def crear_tarea(task: TaskRequest):
    job_id = str(uuid.uuid4())

    estado = {
        "job_id": job_id,
        "status": "PENDING",
        "query": task.query,
        "requires_approval": task.requires_approval,
    }

    await guardar_estado(app.state.redis, job_id, estado)
    await app.state.redis.rpush(QUEUE_NAME, job_id)

    return {"job_id": job_id, "status": "PENDING"}


@app.get("/tasks/{job_id}")
async def consultar_tarea(job_id: str):

    datos = await app.state.redis.get(f"{STATUS_PREFIX}{job_id}")

    if datos is None:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada",
        )

    return json.loads(datos)


@app.post("/tasks/{job_id}/approve")
async def aprobar_tarea(job_id: str):
    datos = await app.state.redis.get(f"{STATUS_PREFIX}{job_id}")

    if datos is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    tarea = json.loads(datos)

    if tarea["status"] != "WAITING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail="La tarea no está esperando aprobación",
        )

    resultado_grafo = await app.state.graph.ainvoke(
        Command(resume=True),
        config={"configurable": {"thread_id": job_id}},
    )

    await guardar_estado(
        app.state.redis,
        job_id,
        {
            **tarea,
            "status": "DONE",
            "result": resultado_grafo["messages"][-1].content,
        },
    )

    return {"job_id": job_id, "status": "DONE"}
