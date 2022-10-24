import click
import asyncio
from typing import Any
from uvicorn import Config, Server

from yente import settings
from yente.app import create_app
from yente.logs import configure_logging, get_logger
from yente.search.base import get_es
from yente.search.indexer import update_index


log = get_logger("yente")


@click.group(help="yente API server")
def cli() -> None:
    pass


@cli.command("serve", help="Run uvicorn and serve requests")
def serve() -> None:
    app = create_app()
    server = Server(
        Config(
            app,
            host="0.0.0.0",
            port=settings.PORT,
            proxy_headers=True,
            reload=settings.DEBUG,
            # reload_dirs=[code_dir],
            # debug=settings.DEBUG,
            log_level=settings.LOG_LEVEL,
            server_header=False,
        ),
    )
    configure_logging()
    server.run()


async def _reindex(force: bool = False) -> None:
    await update_index(force=force)


@cli.command("reindex", help="Re-index the data if newer data is available")
@click.option("-f", "--force", is_flag=True, default=False)
def reindex(force: bool) -> None:
    configure_logging()
    asyncio.run(_reindex(force=force))


async def _clear_index() -> None:
    es = await get_es()
    indices: Any = await es.cat.indices(format="json")
    for index in indices:
        index_name: str = index.get("index")
        log.info("Delete index", index=index_name)
        await es.indices.delete(index=index_name)
    await es.close()


@cli.command("clear-index", help="Delete everything in ElasticSearch")
def clear_index() -> None:
    configure_logging()
    asyncio.run(_clear_index())


if __name__ == "__main__":
    cli()
