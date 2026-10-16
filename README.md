# Le Violentomètre

A lightweight **Souls tracker** focused on Dark Harvest rune activations in League of Legends ranked games.

- Tracks Dark Harvest activations across Solo/Duo and Flex games.
- Stores player statistics in JSON.
- Automatically collects match data every 5 minutes for tracked players.
- Uploads the JSON data to a Cloudflare R2 bucket for public access.

API limitations might require you to tweak the cron activation frequency according to the amount of players you're tracking, this can be changed in the cron in `main.py`

Base version works for EUW, this can be changed in `riot_api.py`

## Setup

1. Create a `.env` file with your Riot API key:

```env
RIOT_API_KEY=your_riot_api_key
```

Alternatively, provide the API key through the `RIOT_API_KEY` environment variable.

2. Configure Cloudflare R2 (optional)

To enable JSON uploads, configure the following environment variables in your `.env` file:

   ```env
   R2_ACCOUNT_ID=your_account_id
   R2_ACCESS_KEY_ID=your_r2_access_key_id
   R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
   R2_BUCKET_NAME=your_bucket_name
   R2_ENDPOINT_URL=https://your_account_id.r2.cloudflarestorage.com
   ```

Create an R2 bucket on Cloudflare, generate your keys, replace the placeholder values with your creds.
This bucket must be configured for public access if you need/want it to be public, by default it's not.
Account ID isn't currently used but might be useful for future features. (perhaps).

Disabling Cloudflare R2

If you don't need remote JSON hosting, you can remove the upload functionality by modifying `collector.py` and getting rid of the `upload_to_r2()` method. The collector will continue to store player statistics locally in `data/players.json`.

Obviously don't commit your `.env` file or expose your R2 credentials.

3. Kickstart with Docker Compose:

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