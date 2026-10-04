import asyncio
import time
import httpx


URL = "http://127.0.0.1:8000/tasks"

CONSULTAS = [
    "¿Qué es la entropía?",
    "¿Qué es un videojuego?",
    "¿Qué es una consola?",
    "¿Qué es un RPG?",
    "¿Qué es un motor gráfico?",
]


async def enviar_tarea(client, consulta):
    inicio = time.perf_counter()

    response = await client.post(
        URL,
        json={"query": consulta},
    )

    datos = response.json()
    job_id = datos["job_id"]

    while True:
        response = await client.get(
            f"http://127.0.0.1:8000/tasks/{job_id}"
        )

        estado = response.json()

        if estado["status"] in ["DONE", "FAILED"]:
            break

        await asyncio.sleep(0.5)

    fin = time.perf_counter()

    return {
        "job_id": job_id,
        "status": estado["status"],
        "tiempo": fin - inicio,
    }


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        inicio_total = time.perf_counter()

        resultados = await asyncio.gather(
            *(enviar_tarea(client, consulta) for consulta in CONSULTAS)
        )

        fin_total = time.perf_counter()

    print("\nRESULTADOS:")
    for resultado in resultados:
        print(resultado)

    tiempos = sorted(resultado["tiempo"] for resultado in resultados)

    posicion = int(0.95 * len(tiempos)) - 1
    posicion = max(0, min(posicion, len(tiempos) - 1))

    p95 = tiempos[posicion]

    print(f"\nTiempo total: {fin_total - inicio_total:.2f}s")
    print(f"P95: {p95:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())