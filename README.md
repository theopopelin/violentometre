# Le Violentomètre

A lightweight **Dark Harvest tracker** focused on rune activations in League of Legends ranked games.

- Tracks Dark Harvest activations across Solo/Duo and Flex games.
- Stores player statistics in JSON.
- Automatically collects match data every 5 minutes for tracked players.

## Setup

1. Create a `.env` file with your Riot API key:

   ```env
   RIOT_API_KEY=your_riot_api_key
   ```

   Alternatively, provide the API key through the `RIOT_API_KEY` environment variable.

2. Start the collector with Docker Compose:

   ```bash
   docker compose up -d --build
   ```

## Legal boilerplate

This product isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.