# Supercharged Slot Machine

A competitive slot machine game with a reusable Python engine, offline terminal mode, and a Redis-ready browser room economy.

## Implementation Steps

1. Keep the slot engine pure in `slot_machine.py`.
2. Keep offline terminal saves in local JSON through `game.py`.
3. Move online player balances and rooms into `online_store.py`.
4. Use Redis for web persistence when `REDIS_URL` is set.
5. Fall back to memory for local development and tests when Redis is unavailable.
6. Give every online player a fixed starting balance of 50,000 coins.
7. Deduct a fixed room stake when players create or join a room.
8. Hold all room stakes in a shared pot.
9. Track room score separately from global coin balance.
10. Award the pot plus a victory bonus when a room ends.
11. Treat mid-room leaving as a forfeit and deduct a leave penalty.
12. Award daily rewards, achievements, rank gifts, and league points through the online store.
13. Render room state, leaderboard, gifts, achievements, and league status in the browser UI.
14. Let players pause/save and resume later with a private save code.
15. Award welcome-back rewards after 7+ days away.
16. Keep public friend codes separate from private save codes.
17. Add a themed browser cabinet with left-to-right reel suspense, lever motion, sound controls, chat, and jackpot confetti.

## Features

- 3x3 slot grid
- Cherries, bells, sevens, diamonds, wilds, scatters, bars, and lemons
- 5 paylines: top, middle, bottom, and both diagonals
- Wild substitutions
- Rare-symbol jackpots for natural sevens and diamonds
- Scatter bonus with free spins and random multipliers
- Near-miss messages
- Offline JSON save/load for terminal players
- Online Redis-backed profiles, balances, room pots, rewards, achievements, and leagues
- Fixed 50,000 starting coins for online players
- Staked multiplayer rooms with forfeits and pot payouts
- Pause/save and resume with a private save code
- Public friend codes for adding other players without sharing resume access
- First 7+ day welcome-back reward: 25,000 coins and 7 free spins
- Later 7+ day return rewards: 250 coins and 2 free spins
- Rank 1-5 cosmetic gifts shown on the leaderboard
- Burgundy-led responsive browser theme with sage, teal, ivory, and gold accents
- Illustrated slot cabinet, animated lever pull, left-to-right reel stops, jackpot confetti, generated sound effects, soft music toggle, in-room chat, and emoji reactions

## Project Layout

- `symbols.py` stores symbol weights, payouts, jackpot settings, and paylines.
- `slot_machine.py` contains `SlotMachine` and `PayTable`.
- `game.py` contains offline `Player`, `GameStats`, JSON save/load, and session rules.
- `online_store.py` contains Redis/memory-backed online profiles, rooms, rewards, achievements, friends, chat, and leagues.
- `main.py` runs the terminal game.
- `web_app.py` runs the browser room server.
- `web/` contains the browser UI.
- `test_slot_machine.py` covers spin generation, payouts, bonuses, save/load, room economy, rewards, gifts, friends, and chat.

## Install

```bash
python -m pip install -r requirements.txt
```

## Run Redis Locally

With Docker:

```bash
docker compose up -d redis
```

PowerShell:

```powershell
$env:REDIS_URL="redis://localhost:6379/0"
python web_app.py
```

If `REDIS_URL` is not set, the browser server uses an in-memory store for local testing.

## Terminal Mode

```bash
python main.py
```

## Browser Room Mode

Do not open `web/index.html` with VS Code Live Server for multiplayer mode. Live Server only serves static files; it does not run the Python room API.

```bash
python web_app.py
```

Then open:

```text
http://127.0.0.1:8000
```

Create a room, choose the room stake, share the six-character code, and friends can join the same staked room while the server is running.

## Deploy on Render

This repo includes `render.yaml`, which provisions:

- `slot-machine-web`: the Python web service
- `slot-machine-redis`: a Render Key Value instance used through `REDIS_URL`

Render deploys from a pushed Git repository, so commit and push `render.yaml` before opening the Blueprint:

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

Then open:

```text
https://dashboard.render.com/blueprint/new?repo=https://github.com/EzekielGitura/SlotMachine
```

Review the resources and click **Apply**. The web service start command is:

```bash
python web_app.py --host 0.0.0.0 --port $PORT
```

Render will inject `REDIS_URL` from the Key Value service and the app will require Redis in production with `SLOT_REQUIRE_REDIS=1`.

## Test

```bash
python -B -m unittest -v
```
