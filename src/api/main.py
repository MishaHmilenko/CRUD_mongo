from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka as setup_dishka_fastapi
from dishka.integrations.taskiq import setup_dishka as setup_dishka_taskiq
from fastapi import FastAPI

from src.api.controllers.main import setup_controllers
from src.crypto_api.binance_websocket import get_binance_websocket
from src.db.main import get_db, initialize_beanie, DBConfig
from src.dishka.container import container
from src.smtp.main import get_smtp_server
from src.taskiq.main import broker


@asynccontextmanager
async def lifespan(app: FastAPI):

    await initialize_beanie(get_db(DBConfig()).db)

    await broker.startup()

    app.state.smtp = get_smtp_server()

    ws = await get_binance_websocket()

    await ws.connect_to_trade_websocket()

    yield

    await broker.shutdown()

    await container.close()

    await ws.stop_connection()


def build_app() -> FastAPI:
    app = FastAPI(title='CRUD_mongo', lifespan=lifespan)

    setup_controllers(app)

    # setup di
    setup_dishka_taskiq(container, broker)
    setup_dishka_fastapi(container, app)

    return app
