import asyncio
import logging

import aiocron

from collector import collect_all


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info("Violentometre : extractor on.")

collection_lock = asyncio.Lock()


async def scheduled_collection():
    async with collection_lock:
        logging.info("Début de la collecte.")

        try:
            await asyncio.to_thread(collect_all)
        except Exception:
            logging.exception("Erreur générale pendant la collecte.")
        finally:
            logging.info("Fin de la collecte.")


async def cron_collection():
    logging.info("Déclenchement du cron.")
    await scheduled_collection()


async def main():
    logging.info("Configuration Riot Games chargée.")

    # Utilise la boucle asyncio actuellement active.
    cron = aiocron.crontab(
        "*/5 * * * *",
        func=cron_collection,
        loop=asyncio.get_running_loop()
    )

    # Collecte immédiate au démarrage.
    await scheduled_collection()

    # Garde l'application en fonctionnement.
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
