import os
import json
import asyncio
import logging
from pathlib import Path
from threading import Lock

import requests
import aiocron


API_KEY = os.environ["RIOT_API_KEY"]

REGION = "europe"
PLATFORM = "euw1"
DARK_HARVEST_ID = 8128

DATA_FILE = Path("/app/data/players.json")
MATCH_COUNT = 100
INITIAL_MATCH_COUNT = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info("Violentometre : extractor on.")

collection_lock = asyncio.Lock()


def load_data():
    if not DATA_FILE.exists():
        return {"players": {}}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = DATA_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    temporary_file.replace(DATA_FILE)


def riot_request(url, params=None):
    response = requests.get(
        url,
        headers={"X-Riot-Token": API_KEY},
        params=params,
        timeout=20
    )

    response.raise_for_status()
    return response.json()


def get_match_ids(puuid, last_game_id):
    url = (
        f"https://{REGION}.api.riotgames.com"
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
    )

    if not last_game_id:
        return riot_request(
            url,
            params={"start": 0, "count": INITIAL_MATCH_COUNT}
        )

    match_ids = []
    start = 0

    while True:
        page = riot_request(
            url,
            params={"start": start, "count": MATCH_COUNT}
        )

        if not page:
            break

        if last_game_id in page:
            match_ids.extend(page[:page.index(last_game_id)])
            break

        match_ids.extend(page)

        if len(page) < MATCH_COUNT:
            break

        start += len(page)

    return match_ids



def get_match(match_id):
    url = (
        f"https://{REGION}.api.riotgames.com"
        f"/lol/match/v5/matches/{match_id}"
    )

    return riot_request(url)


def get_dark_harvest_procs(participant):
    perks = participant.get("perks", {})

    for style in perks.get("styles", []):
        for selection in style.get("selections", []):
            if selection.get("perk") == DARK_HARVEST_ID:
                return selection.get("var2", 0)

    return 0


def process_player(puuid, player):
    last_game_id = player.get("last_game_id")
    match_ids = get_match_ids(puuid, last_game_id)

    if not match_ids:
        logging.info("%s : aucune nouvelle partie.", player["username"])
        return False

    match_ids.reverse()

    for match_id in match_ids:
        match = get_match(match_id)
        info = match["info"]

        queue_id = info.get("queueId")
        if queue_id not in (420, 440):
            player["last_game_end"] = info.get("gameEndTimestamp")
            player["last_game_id"] = match_id

            logging.info(
                "%s | %s | Partie ignorée (queueId=%s)",
                player["username"],
                match_id,
                queue_id
            )
            continue

        participant = next(
            (
                participant
                for participant in info["participants"]
                if participant["puuid"] == puuid
            ),
            None
        )

        if participant is None:
            raise ValueError(
                f"Participant {puuid} introuvable dans {match_id}"
            )

        procs = get_dark_harvest_procs(participant)

        if procs > 0:
            player["games_with_dark_harvest"] += 1
            player["total_dark_harvest_procs"] += procs

            record = player["personal_record"]

            if procs > record["procs"]:
                player["personal_record"] = {
                    "match_id": match_id,
                    "procs": procs
                }

        player["last_game_end"] = info.get("gameEndTimestamp")
        player["last_game_id"] = match_id

        logging.info(
            "%s | %s | Dark Harvest : %s procs",
            player["username"],
            match_id,
            procs
        )

    return True


def collect_all():
    data = load_data()

    for puuid, player in data["players"].items():
        try:
            if process_player(puuid, player):
                save_data(data)
                logging.info("Données sauvegardées dans %s.", DATA_FILE)

        except Exception:
            # Sauvegarde aussi les modifications déjà faites
            # avant l'erreur.
            save_data(data)
            logging.exception(
                "Erreur de collecte pour %s",
                player.get("username", puuid)
            )


async def scheduled_collection():
    async with collection_lock:
        logging.info("Début de la collecte.")
        await asyncio.to_thread(collect_all)
        logging.info("Fin de la collecte.")

@aiocron.crontab("*/5 * * * *")
async def cron_collection():
    logging.info("Déclenchement du cron.")
    await scheduled_collection()

async def main():
    logging.info("Configuration Riot Games chargée.")

    # Collecte immédiate au démarrage.
    await scheduled_collection()

    # Laisse aiocron déclencher les collectes suivantes.
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
