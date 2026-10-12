import os
import requests


API_KEY = os.environ["RIOT_API_KEY"]

REGION = "europe"

MATCH_COUNT = 100
INITIAL_MATCH_COUNT = 5


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

    # Première collecte : récupérer les 5 dernières parties.
    if not last_game_id:
        return riot_request(
            url,
            params={"start": 0, "count": INITIAL_MATCH_COUNT}
        )

    # Collectes suivantes : récupérer les parties jusqu'à
    # retrouver la dernière partie déjà traitée.
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
