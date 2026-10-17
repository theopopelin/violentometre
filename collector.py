import json
import logging
import os
from pathlib import Path
import boto3
from botocore.config import Config

from riot_api import RiotAPI


DARK_HARVEST_ID = 8128

DATA_FILE = Path("/app/data/players.json")

riot = RiotAPI("europe")

def load_data():
    if not DATA_FILE.exists():
        return {"players": {}}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


# Temp file update to avoid corrupting data on error
def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = DATA_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    temporary_file.replace(DATA_FILE)


def upload_to_r2():
    client = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )

    client.upload_file(
        str(DATA_FILE),
        os.environ["R2_BUCKET_NAME"],
        "players.json",
        ExtraArgs={"ContentType": "application/json"},
    )

    logging.info("players.json uploaded to Cloudflare R2.")


def get_dark_harvest_procs(participant):
    perks = participant.get("perks", {})

    for style in perks.get("styles", []):
        for selection in style.get("selections", []):
            if selection.get("perk") == DARK_HARVEST_ID:
                return selection.get("var2", 0)

    return 0


def process_player(puuid, player):
    last_game_id = player.get("last_game_id")
    match_ids = riot.get_match_ids(puuid, last_game_id)

    if not match_ids:
        logging.info(
            "%s : no new matches.",
            player["username"]
        )
        return False

    # API sends latest matches in chronological order
    match_ids.reverse()

    for match_id in match_ids:
        match = riot.get_match(match_id)
        info = match["info"]

        queue_id = info.get("queueId")

        # Solo/Duo : 420, Flex : 440
        if queue_id not in (420, 440):
            player["last_game_end"] = info.get("gameEndTimestamp")
            player["last_game_id"] = match_id

            logging.info(
                "%s | %s | Match ignored (queueId=%s)",
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
                f"Player {puuid} not found in {match_id}"
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
                logging.info(
                    "Data saved in %s.",
                    DATA_FILE
                )

        except Exception:
            # Saves modifications before error
            save_data(data)

            logging.exception(
                "Erreur de collecte pour %s",
                player.get("username", puuid)
            )

    # Upload the latest local JSON after processing all players
    try:
        upload_to_r2()
        logging.info("Uploaded players.json to Cloudflare R2.")
    except Exception:
        logging.exception(
            "Failed to upload players.json to Cloudflare R2."
        )