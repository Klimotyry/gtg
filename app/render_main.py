import asyncio
import os

from aiogram import Bot, Dispatcher

from app.db import init_db
from app.main import config, router


async def handle_healthcheck(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        await reader.read(4096)
        body = b"Byte Shop bot is running\n"
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: close\r\n\r\n"
            + body
        )
        writer.write(response)
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def main() -> None:
    init_db()

    port = int(os.getenv("PORT", "10000"))
    server = await asyncio.start_server(handle_healthcheck, "0.0.0.0", port)
    print(f"Render health server listening on 0.0.0.0:{port}")

    bot = Bot(config.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        server.close()
        await server.wait_closed()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
