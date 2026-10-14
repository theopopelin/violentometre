import asyncio
import logging

import aiocron

from collector import collect_all


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info("Violentometre Reqviem : they all sang along")

collection_lock = asyncio.Lock()


async def scheduled_collection():
    async with collection_lock:
        logging.info("Start extraction.")

        try:
            await asyncio.to_thread(collect_all)
        except Exception:
            logging.exception("Error during extraction.")
        finally:
            logging.info("End extraction.")


async def cron_collection():
    logging.info("Cron start")
    await scheduled_collection()


async def main():
    logging.info("Riot games config in.")

    # Uses current running asyncio 
    cron = aiocron.crontab(
        "*/5 * * * *",
        func=cron_collection,
        loop=asyncio.get_running_loop()
    )

    # Extraction at process start
    await scheduled_collection()

    # Keeps it up and so should you
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
