import os
import json
import sys
from pathlib import Path
from urllib.parse import quote

import requests


API_KEY = os.environ["RIOT_API_KEY"]
DATA_FILE = Path("/app/data/players.json")


def riot_request(url):
    response = requests.get(
        url,
        headers={"X-Riot-Token": API_KEY},
        timeout=20
    )
    response.raise_for_status()
    return response.json()


def add_player(riot_id):
    if "#" not in riot_id:
        raise ValueError("Format : Pseudo#TAG")

    game_name, tag_line = riot_id.rsplit("#", 1)

    if not game_name or not tag_line:
        raise ValueError("Format : Pseudo#TAG")

    url = (
        "https://europe.api.riotgames.com"
        "/riot/account/v1/accounts/by-riot-id/"
        f"{quote(game_name, safe='')}/{quote(tag_line, safe='')}"
    )

    account = riot_request(url)

    puuid = account["puuid"]
    username = f"{account['gameName']}#{account['tagLine']}"

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = {"players": {}}

    if puuid in data["players"]:
        print(f"{username} is already tracked.")
        return

    data["players"][puuid] = {
        "username": username,
        "games_with_dark_harvest": 0,
        "total_dark_harvest_procs": 0,
        "last_game_end": None,
        "last_game_id": None,
        "personal_record": {
            "match_id": None,
            "procs": 0
        }
    }

    temporary_file = DATA_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    temporary_file.replace(DATA_FILE)

    print(f"Joueur ajouté : {username}")
    print(f"PUUID : {puuid}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage : python add_player.py "Pseudo#TAG"')
        sys.exit(1)

    try:
        add_player(sys.argv[1])
    except (requests.RequestException, ValueError, KeyError) as error:
        print(f"Erreur : {error}")
        sys.exit(1)
