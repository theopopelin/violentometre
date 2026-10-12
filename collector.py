import json
import logging
from pathlib import Path

from riot_api import get_match_ids, get_match


DARK_HARVEST_ID = 8128

DATA_FILE = Path("/app/data/players.json")


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
        logging.info(
            "%s : aucune nouvelle partie.",
            player["username"]
        )
        return False

    # L'API renvoie les parties de la plus récente à la plus ancienne.
    # On les traite dans l'ordre chronologique.
    match_ids.reverse()

    for match_id in match_ids:
        match = get_match(match_id)
        info = match["info"]

        queue_id = info.get("queueId")

        # Solo/Duo : 420 ; Flex : 440.
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
                logging.info(
                    "Données sauvegardées dans %s.",
                    DATA_FILE
                )

        except Exception:
            # Préserve les modifications effectuées avant une erreur.
            save_data(data)

            logging.exception(
                "Erreur de collecte pour %s",
                player.get("username", puuid)
            )
