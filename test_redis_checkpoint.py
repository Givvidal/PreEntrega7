import asyncio

from langgraph.checkpoint.redis.aio import AsyncRedisSaver


async def main():
    async with AsyncRedisSaver.from_conn_string(
        "redis://localhost:6379"
    ) as checkpointer:

        await checkpointer.asetup()

        print("Redis checkpointer configurado correctamente")


asyncio.run(main())