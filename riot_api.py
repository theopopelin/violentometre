import os
import requests


MATCH_COUNT = 100
INITIAL_MATCH_COUNT = 5


class RiotAPI:
    def __init__(self, region):
        self.api_key = os.environ["RIOT_API_KEY"]
        self.region = region
        self.session = requests.Session()

    def riot_request(self, url, params=None):
        response = self.session.get(
            url,
            headers={"X-Riot-Token": self.api_key},
            params=params,
            timeout=20
        )

        response.raise_for_status()
        return response.json()

    def get_match_ids(self, puuid, last_game_id):
        url = (
            f"https://{self.region}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )

        # First extraction
        if not last_game_id:
            return self.riot_request(
                url,
                params={"start": 0, "count": INITIAL_MATCH_COUNT}
            )

        # Next extractions : verify matches up to the last update
        match_ids = []
        start = 0

        while True:
            page = self.riot_request(
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

    def get_match(self, match_id):
        url = (
            f"https://{self.region}.api.riotgames.com"
            f"/lol/match/v5/matches/{match_id}"
        )

        return self.riot_request(url)
