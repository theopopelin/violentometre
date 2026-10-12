# Le Violentomètre

A lightweight **Souls tracker** focused on Dark Harvest rune activations in League of Legends ranked games.

- Tracks Dark Harvest activations across Solo/Duo and Flex games.
- Stores player statistics in JSON.
- Automatically collects match data every 5 minutes for tracked players.

## Setup

1. Create a `.env` file with your Riot API key:

   ```env
   RIOT_API_KEY=your_riot_api_key
   ```

   Alternatively, provide the API key through the `RIOT_API_KEY` environment variable.

2. Kickstart with Docker Compose:

   ```bash
   docker compose up -d --build
   ```

## Usage

### Add a player

Add a League of Legends account using its Riot ID:

```bash
docker compose exec extractor python add_player.py "Summoner#TAG"
```

Replace `Summoner#TAG` with the player's Riot ID.

### View logs

Follow the collector logs in real time:

```bash
docker compose logs -f extractor
```

Display the last 100 lines of logs:

```bash
docker compose logs --tail=100 extractor
```

## Legal boilerplate

This product isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.