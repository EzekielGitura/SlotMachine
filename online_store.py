import json
import os
import secrets
import string
import threading
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from game import GameStats, Player, SlotGame
from slot_machine import SlotMachine


STARTING_COINS = 50000
DEFAULT_ROOM_STAKE = 500
MIN_ROOM_STAKE = 100
MAX_ROOM_STAKE = 5000
LEAVE_PENALTY = 100
DAILY_REWARD = 750
ROOM_VICTORY_BONUS = 250
AWAY_REWARD_DAYS = 7
FIRST_AWAY_REWARD_COINS = 25000
FIRST_AWAY_REWARD_FREE_SPINS = 7
RETURN_AWAY_REWARD_COINS = 250
RETURN_AWAY_REWARD_FREE_SPINS = 2

RANK_GIFTS = {
    1: {"name": "Ruby Crown", "description": "Top table aura", "accent": "ruby"},
    2: {"name": "Gold Vault", "description": "Steady challenger", "accent": "gold"},
    3: {"name": "Sage Charm", "description": "Cool streak token", "accent": "sage"},
    4: {"name": "Silver Spark", "description": "Momentum badge", "accent": "silver"},
    5: {"name": "Velvet Token", "description": "Table presence", "accent": "velvet"},
}

ACHIEVEMENTS = {
    "first_spin": {
        "name": "First Pull",
        "description": "Spin once in an online room.",
        "coins": 100,
        "league_points": 25,
    },
    "first_win": {
        "name": "First Win",
        "description": "Win coins from a spin.",
        "coins": 250,
        "league_points": 60,
    },
    "jackpot_hunter": {
        "name": "Jackpot Hunter",
        "description": "Trigger a jackpot line.",
        "coins": 1000,
        "league_points": 250,
    },
    "free_spin_finder": {
        "name": "Free Spin Finder",
        "description": "Trigger free spins with scatters.",
        "coins": 500,
        "league_points": 120,
    },
    "room_winner": {
        "name": "Room Victor",
        "description": "Win a staked multiplayer room.",
        "coins": 1500,
        "league_points": 400,
    },
    "high_roller": {
        "name": "High Roller",
        "description": "Enter a room with a stake of 1,000 coins or more.",
        "coins": 300,
        "league_points": 100,
    },
}

LEAGUES = [
    {"name": "Ruby", "min_points": 7000},
    {"name": "Gold", "min_points": 3000},
    {"name": "Silver", "min_points": 1000},
    {"name": "Bronze", "min_points": 0},
]


def utc_now():
    return datetime.now(timezone.utc)


def today_key():
    return utc_now().date().isoformat()


def iso_now():
    return utc_now().isoformat(timespec="seconds")


def make_id():
    return secrets.token_urlsafe(12)


def make_save_code():
    alphabet = string.ascii_uppercase + string.digits
    return "-".join(
        "".join(secrets.choice(alphabet) for _ in range(4))
        for _ in range(3)
    )


def make_room_code(existing):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if not existing(code):
            return code


def league_for(points):
    for league in LEAGUES:
        if points >= league["min_points"]:
            return dict(league)
    return dict(LEAGUES[-1])


def parse_iso(value):
    if not value:
        return utc_now()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class MemoryBackend:
    def __init__(self):
        self.profiles = {}
        self.rooms = {}
        self.save_codes = {}

    def get_profile(self, player_id):
        profile = self.profiles.get(player_id)
        return deepcopy(profile) if profile else None

    def save_profile(self, profile):
        self.profiles[profile["id"]] = deepcopy(profile)
        if profile.get("save_code"):
            self.save_codes[profile["save_code"].upper()] = profile["id"]

    def get_profile_by_save_code(self, save_code):
        player_id = self.save_codes.get(save_code.upper())
        return self.get_profile(player_id) if player_id else None

    def list_profiles(self):
        return [deepcopy(profile) for profile in self.profiles.values()]

    def get_room(self, code):
        room = self.rooms.get(code.upper())
        return deepcopy(room) if room else None

    def save_room(self, room):
        self.rooms[room["code"]] = deepcopy(room)

    def room_exists(self, code):
        return code.upper() in self.rooms


class RedisBackend:
    def __init__(self, redis_url):
        try:
            import redis
        except ImportError as error:
            raise RuntimeError("Install redis with `python -m pip install redis`.") from error

        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.redis.ping()

    def profile_key(self, player_id):
        return f"slot:profile:{player_id}"

    def save_code_key(self, save_code):
        return f"slot:savecode:{save_code.upper()}"

    def room_key(self, code):
        return f"slot:room:{code.upper()}"

    def get_profile(self, player_id):
        raw = self.redis.get(self.profile_key(player_id))
        return json.loads(raw) if raw else None

    def save_profile(self, profile):
        player_id = profile["id"]
        payload = json.dumps(profile)
        pipe = self.redis.pipeline()
        pipe.set(self.profile_key(player_id), payload)
        if profile.get("save_code"):
            pipe.set(self.save_code_key(profile["save_code"]), player_id)
        pipe.sadd("slot:profiles", player_id)
        pipe.zadd("slot:leaderboard:coins", {player_id: profile["balance"]})
        pipe.zadd("slot:leaderboard:league", {player_id: profile["league_points"]})
        pipe.execute()

    def get_profile_by_save_code(self, save_code):
        player_id = self.redis.get(self.save_code_key(save_code))
        return self.get_profile(player_id) if player_id else None

    def list_profiles(self):
        player_ids = self.redis.smembers("slot:profiles")
        profiles = []
        for player_id in player_ids:
            profile = self.get_profile(player_id)
            if profile:
                profiles.append(profile)
        return profiles

    def get_room(self, code):
        raw = self.redis.get(self.room_key(code))
        return json.loads(raw) if raw else None

    def save_room(self, room):
        code = room["code"]
        pipe = self.redis.pipeline()
        pipe.set(self.room_key(code), json.dumps(room))
        pipe.sadd("slot:rooms", code)
        pipe.execute()

    def room_exists(self, code):
        return bool(self.redis.exists(self.room_key(code)))


class OnlineStore:
    def __init__(self, backend=None, redis_url=None, slot_game=None):
        self.backend = backend or self.build_backend(redis_url)
        self.slot_game = slot_game or SlotGame(SlotMachine())
        self.lock = threading.RLock()

    @staticmethod
    def build_backend(redis_url=None):
        redis_url = redis_url if redis_url is not None else os.getenv("REDIS_URL")
        if redis_url:
            try:
                return RedisBackend(redis_url)
            except RuntimeError:
                if os.getenv("SLOT_REQUIRE_REDIS") == "1":
                    raise
                print("Redis client is not installed, using memory store. Run `python -m pip install -r requirements.txt` to enable Redis.")
            except Exception as error:
                if os.getenv("SLOT_REQUIRE_REDIS") == "1":
                    raise
                print(f"Redis unavailable, using memory store: {error}")
        return MemoryBackend()

    @property
    def backend_name(self):
        return self.backend.__class__.__name__.replace("Backend", "").lower()

    def create_profile(self, name, player_id=None):
        player_id = player_id or make_id()
        profile = self.backend.get_profile(player_id)
        if profile:
            profile["name"] = self.clean_name(name)
            self.backend.save_profile(profile)
            return profile

        profile = {
            "id": player_id,
            "save_code": self.generate_save_code(),
            "name": self.clean_name(name),
            "balance": STARTING_COINS,
            "free_spins": 0,
            "stats": asdict(GameStats()),
            "history": [],
            "achievements": [],
            "daily_claimed": None,
            "league_points": 0,
            "wins": 0,
            "losses": 0,
            "forfeits": 0,
            "paused": False,
            "current_room_code": None,
            "last_seen_at": iso_now(),
            "last_paused_at": None,
            "away_reward_count": 0,
            "last_away_reward_at": None,
            "created_at": iso_now(),
            "updated_at": iso_now(),
        }
        self.backend.save_profile(profile)
        return profile

    def generate_save_code(self):
        for _ in range(20):
            save_code = make_save_code()
            if not self.backend.get_profile_by_save_code(save_code):
                return save_code
        return make_id().upper()

    def ensure_profile(self, player_id=None, name="Player"):
        if player_id:
            profile = self.backend.get_profile(player_id)
            if profile:
                self.normalize_profile(profile)
                if name:
                    profile["name"] = self.clean_name(name)
                    profile["paused"] = False
                    profile["updated_at"] = iso_now()
                    self.backend.save_profile(profile)
                return profile
        return self.create_profile(name, player_id)

    def resume_profile(self, save_code, name=None):
        with self.lock:
            profile = self.backend.get_profile_by_save_code(self.clean_save_code(save_code))
            if not profile:
                raise ValueError("Save code not found.")

            self.normalize_profile(profile)
            if name:
                profile["name"] = self.clean_name(name)

            reward = self.apply_away_reward(profile)
            profile["paused"] = False
            profile["last_seen_at"] = iso_now()
            profile["updated_at"] = iso_now()
            self.backend.save_profile(profile)

            room_code = profile.get("current_room_code")
            room_state = None
            if room_code and self.backend.get_room(room_code):
                room_state = self.room_state(room_code, profile["id"])

            return {
                "playerId": profile["id"],
                "profile": self.profile_state(
                    profile,
                    include_save_code=True,
                    include_player_id=True,
                ),
                "roomCode": room_code,
                "state": room_state,
                "reward": reward,
            }

    def pause_profile(self, player_id):
        with self.lock:
            profile = self.require_profile(player_id)
            self.normalize_profile(profile)
            profile["paused"] = True
            profile["last_seen_at"] = iso_now()
            profile["last_paused_at"] = iso_now()
            profile["updated_at"] = iso_now()
            self.backend.save_profile(profile)
            return self.profile_state(
                profile,
                include_save_code=True,
                include_player_id=True,
            )

    def create_room(self, name, player_id=None, stake=DEFAULT_ROOM_STAKE):
        with self.lock:
            stake = self.validate_stake(stake)
            profile = self.ensure_profile(player_id, name)
            code = make_room_code(self.backend.room_exists)
            room = {
                "code": code,
                "host_id": profile["id"],
                "stake": stake,
                "pot": 0,
                "status": "waiting",
                "players": [],
                "forfeited": [],
                "scores": {},
                "spins": {},
                "winner_id": None,
                "victory_bonus": ROOM_VICTORY_BONUS,
                "created_at": iso_now(),
                "completed_at": None,
                "events": [],
            }
            self.join_room_data(room, profile)
            self.backend.save_room(room)
            return code, profile["id"], self.room_state(code, profile["id"])

    def join_room(self, code, name, player_id=None):
        with self.lock:
            room = self.require_room(code)
            if room["status"] == "completed":
                raise ValueError("This room has already ended.")

            profile = self.ensure_profile(player_id, name)
            if profile["id"] not in room["players"]:
                self.join_room_data(room, profile)
            else:
                self.add_event(room, f"{profile['name']} is already in the room.")

            self.backend.save_room(room)
            return profile["id"], self.room_state(room["code"], profile["id"])

    def join_room_data(self, room, profile):
        stake = room["stake"]
        if profile["balance"] < stake:
            raise ValueError(f"{profile['name']} needs {stake} coins to enter this room.")

        profile["balance"] -= stake
        profile["current_room_code"] = room["code"]
        profile["paused"] = False
        profile["last_seen_at"] = iso_now()
        profile["updated_at"] = iso_now()
        room["players"].append(profile["id"])
        room["scores"][profile["id"]] = 0
        room["spins"][profile["id"]] = 0
        room["pot"] += stake
        if len(room["players"]) >= 2:
            room["status"] = "active"

        awards = []
        if stake >= 1000:
            awards = self.award_achievement(profile, "high_roller")

        self.backend.save_profile(profile)
        self.add_event(room, f"{profile['name']} entered with a {stake}-coin stake.")
        for award in awards:
            self.add_event(room, f"{profile['name']} earned {award['name']} (+{award['coins']} coins).")

    def leave_room(self, code, player_id):
        with self.lock:
            room = self.require_room(code)
            if room["status"] == "completed":
                raise ValueError("This room has already ended.")
            if player_id not in room["players"]:
                raise ValueError("Player is not in this room.")
            if player_id in room["forfeited"]:
                raise ValueError("Player already forfeited this room.")

            profile = self.require_profile(player_id)
            self.normalize_profile(profile)
            penalty = min(profile["balance"], LEAVE_PENALTY)
            profile["balance"] -= penalty
            profile["forfeits"] += 1
            profile["current_room_code"] = None
            profile["last_seen_at"] = iso_now()
            profile["updated_at"] = iso_now()
            room["forfeited"].append(player_id)
            room["scores"][player_id] = room["scores"].get(player_id, 0) - penalty
            self.add_event(
                room,
                f"{profile['name']} left early, forfeited their stake, and paid {penalty} coins.",
            )
            self.backend.save_profile(profile)
            self.backend.save_room(room)
            return self.room_state(room["code"], player_id)

    def spin(self, code, player_id, lines, bet):
        with self.lock:
            room = self.require_room(code)
            if room["status"] == "completed":
                raise ValueError("This room has already ended.")
            if player_id not in room["players"]:
                raise ValueError("Player is not in this room.")
            if player_id in room["forfeited"]:
                raise ValueError("Forfeited players cannot spin in this room.")

            profile = self.require_profile(player_id)
            self.normalize_profile(profile)
            player = self.profile_to_player(profile)
            result = self.slot_game.spin(player, int(lines), int(bet))
            self.player_to_profile(player, profile)
            room["scores"][player_id] = room["scores"].get(player_id, 0) + result.net
            room["spins"][player_id] = room["spins"].get(player_id, 0) + 1

            awards = self.awards_for_spin(profile, result)
            profile["league_points"] += max(result.net, 0) // 10
            profile["paused"] = False
            profile["last_seen_at"] = iso_now()
            profile["updated_at"] = iso_now()
            self.backend.save_profile(profile)

            verb = "won" if result.total_winnings else "spun"
            self.add_event(
                room,
                f"{profile['name']} {verb} {result.total_winnings} coins; room score {room['scores'][player_id]}.",
            )
            for award in awards:
                self.add_event(room, f"{profile['name']} earned {award['name']} (+{award['coins']} coins).")

            self.backend.save_room(room)
            return result, self.room_state(room["code"], player_id), awards

    def finish_room(self, code, player_id):
        with self.lock:
            room = self.require_room(code)
            if room["status"] == "completed":
                raise ValueError("This room has already ended.")
            if player_id not in room["players"]:
                raise ValueError("Only room players can end this room.")

            eligible_players = [
                player for player in room["players"]
                if player not in room["forfeited"]
            ]
            if not eligible_players:
                raise ValueError("No eligible players remain in this room.")

            winner_id = max(
                eligible_players,
                key=lambda candidate: (
                    room["scores"].get(candidate, 0),
                    self.require_profile(candidate)["balance"],
                ),
            )
            winner = self.require_profile(winner_id)
            self.normalize_profile(winner)
            payout = room["pot"] + room["victory_bonus"]
            winner["balance"] += payout
            winner["wins"] += 1
            winner["league_points"] += max(room["pot"] // 10, 0) + 100
            awards = self.award_achievement(winner, "room_winner")
            winner["current_room_code"] = None
            winner["last_seen_at"] = iso_now()
            winner["updated_at"] = iso_now()
            self.backend.save_profile(winner)

            for loser_id in room["players"]:
                if loser_id == winner_id:
                    continue
                loser = self.backend.get_profile(loser_id)
                if loser:
                    self.normalize_profile(loser)
                    loser["losses"] += 1
                    loser["current_room_code"] = None
                    loser["last_seen_at"] = iso_now()
                    loser["updated_at"] = iso_now()
                    self.backend.save_profile(loser)

            room["winner_id"] = winner_id
            room["status"] = "completed"
            room["completed_at"] = iso_now()
            room["pot"] = 0
            self.add_event(
                room,
                f"{winner['name']} won the room and claimed {payout} coins.",
            )
            for award in awards:
                self.add_event(room, f"{winner['name']} earned {award['name']} (+{award['coins']} coins).")
            self.backend.save_room(room)
            return self.room_state(room["code"], player_id)

    def claim_daily_reward(self, player_id, name="Player"):
        with self.lock:
            profile = self.ensure_profile(player_id, name)
            self.normalize_profile(profile)
            today = today_key()
            if profile.get("daily_claimed") == today:
                raise ValueError("Daily reward already claimed today.")

            profile["daily_claimed"] = today
            profile["balance"] += DAILY_REWARD
            profile["league_points"] += 50
            profile["last_seen_at"] = iso_now()
            profile["updated_at"] = iso_now()
            self.backend.save_profile(profile)
            return {
                "amount": DAILY_REWARD,
                "profile": self.profile_state(
                    profile,
                    include_save_code=True,
                    include_player_id=True,
                ),
            }

    def room_state(self, code, viewer_id=None):
        room = self.require_room(code)
        players = []
        for player_id in room["players"]:
            player = self.profile_state(
                self.require_profile(player_id),
                room,
                include_save_code=player_id == viewer_id,
                include_player_id=player_id == viewer_id,
            )
            player["isYou"] = player_id == viewer_id
            player["isWinner"] = player_id == room["winner_id"]
            players.append(player)

        players.sort(
            key=lambda item: (
                item["roomScore"],
                item["balance"],
            ),
            reverse=True,
        )
        for index, player in enumerate(players, start=1):
            player["rank"] = index
            player["gift"] = RANK_GIFTS.get(index)

        viewer = next((player for player in players if player["isYou"]), None)
        return {
            "store": self.backend_name,
            "roomCode": room["code"],
            "viewerId": viewer_id,
            "you": viewer,
            "room": self.public_room_state(room),
            "players": players,
            "rankGifts": [
                {"rank": rank, **gift}
                for rank, gift in RANK_GIFTS.items()
            ],
            "leaderboard": self.global_leaderboard(),
            "leagues": LEAGUES,
            "achievements": list(ACHIEVEMENTS.values()),
            "events": list(reversed(room["events"])),
            "config": {
                "startingCoins": STARTING_COINS,
                "awayRewardDays": AWAY_REWARD_DAYS,
                "firstAwayRewardCoins": FIRST_AWAY_REWARD_COINS,
                "firstAwayRewardFreeSpins": FIRST_AWAY_REWARD_FREE_SPINS,
                "returnAwayRewardCoins": RETURN_AWAY_REWARD_COINS,
                "returnAwayRewardFreeSpins": RETURN_AWAY_REWARD_FREE_SPINS,
                "defaultStake": DEFAULT_ROOM_STAKE,
                "minStake": MIN_ROOM_STAKE,
                "maxStake": MAX_ROOM_STAKE,
                "leavePenalty": LEAVE_PENALTY,
                "dailyReward": DAILY_REWARD,
                "victoryBonus": ROOM_VICTORY_BONUS,
                "minBet": self.slot_game.slot_machine.min_bet,
                "maxBet": self.slot_game.slot_machine.max_bet,
                "maxPaylines": self.slot_game.slot_machine.max_paylines,
            },
        }

    def profile_state(self, profile, room=None, include_save_code=False, include_player_id=False):
        self.normalize_profile(profile)
        stats = deepcopy(profile["stats"])
        total_wagered = stats.get("total_wagered", 0)
        total_won = stats.get("total_won", 0)
        spins = stats.get("spins", 0)
        winning_spins = stats.get("winning_spins", 0)
        stats["net"] = total_won - total_wagered
        stats["winRate"] = winning_spins / spins if spins else 0
        room_score = room["scores"].get(profile["id"], 0) if room else 0

        state = {
            "name": profile["name"],
            "balance": profile["balance"],
            "freeSpins": profile["free_spins"],
            "stats": stats,
            "achievements": [
                {"id": achievement_id, **ACHIEVEMENTS[achievement_id]}
                for achievement_id in profile["achievements"]
                if achievement_id in ACHIEVEMENTS
            ],
            "dailyClaimed": profile.get("daily_claimed"),
            "dailyAvailable": profile.get("daily_claimed") != today_key(),
            "leaguePoints": profile["league_points"],
            "league": league_for(profile["league_points"]),
            "wins": profile["wins"],
            "losses": profile["losses"],
            "forfeits": profile["forfeits"],
            "paused": profile["paused"],
            "currentRoomCode": profile["current_room_code"],
            "lastSeenAt": profile["last_seen_at"],
            "lastPausedAt": profile["last_paused_at"],
            "awayRewardCount": profile["away_reward_count"],
            "lastAwayRewardAt": profile["last_away_reward_at"],
            "roomScore": room_score,
            "roomSpins": room["spins"].get(profile["id"], 0) if room else 0,
            "forfeited": profile["id"] in room["forfeited"] if room else False,
        }
        if include_player_id:
            state["id"] = profile["id"]
        if include_save_code:
            state["saveCode"] = profile["save_code"]
        return state

    def public_room_state(self, room):
        return {
            "code": room["code"],
            "stake": room["stake"],
            "pot": room["pot"],
            "status": room["status"],
            "victoryBonus": room["victory_bonus"],
            "winnerId": room["winner_id"],
            "playerCount": len(room["players"]),
            "activeCount": len([
                player for player in room["players"]
                if player not in room["forfeited"]
            ]),
        }

    def global_leaderboard(self, limit=10):
        profiles = self.backend.list_profiles()
        profiles.sort(
            key=lambda profile: (profile["league_points"], profile["balance"]),
            reverse=True,
        )
        leaders = []
        for rank, profile in enumerate(profiles[:limit], start=1):
            state = self.profile_state(profile)
            state["globalRank"] = rank
            leaders.append(state)
        return leaders

    def awards_for_spin(self, profile, result):
        awards = []
        awards.extend(self.award_achievement(profile, "first_spin"))
        if result.total_winnings > 0:
            awards.extend(self.award_achievement(profile, "first_win"))
        if result.jackpot_hit:
            awards.extend(self.award_achievement(profile, "jackpot_hunter"))
        if result.free_spins_awarded:
            awards.extend(self.award_achievement(profile, "free_spin_finder"))
        return awards

    def award_achievement(self, profile, achievement_id):
        if achievement_id in profile["achievements"]:
            return []
        achievement = ACHIEVEMENTS[achievement_id]
        profile["achievements"].append(achievement_id)
        profile["balance"] += achievement["coins"]
        profile["league_points"] += achievement["league_points"]
        return [{"id": achievement_id, **achievement}]

    def apply_away_reward(self, profile):
        self.normalize_profile(profile)
        last_seen = parse_iso(profile["last_seen_at"])
        away_time = utc_now() - last_seen
        if away_time < timedelta(days=AWAY_REWARD_DAYS):
            return None

        if profile["away_reward_count"] == 0:
            coins = FIRST_AWAY_REWARD_COINS
            free_spins = FIRST_AWAY_REWARD_FREE_SPINS
            label = "Welcome Back Reward"
        else:
            coins = RETURN_AWAY_REWARD_COINS
            free_spins = RETURN_AWAY_REWARD_FREE_SPINS
            label = "Return Reward"

        profile["balance"] += coins
        profile["free_spins"] += free_spins
        profile["away_reward_count"] += 1
        profile["last_away_reward_at"] = iso_now()
        return {
            "name": label,
            "coins": coins,
            "freeSpins": free_spins,
            "awayDays": away_time.days,
        }

    @staticmethod
    def normalize_profile(profile):
        profile.setdefault("save_code", make_save_code())
        profile.setdefault("paused", False)
        profile.setdefault("current_room_code", None)
        profile.setdefault("last_seen_at", profile.get("updated_at") or iso_now())
        profile.setdefault("last_paused_at", None)
        profile.setdefault("away_reward_count", 0)
        profile.setdefault("last_away_reward_at", None)
        profile.setdefault("free_spins", 0)
        profile.setdefault("history", [])
        profile.setdefault("achievements", [])
        profile.setdefault("daily_claimed", None)
        profile.setdefault("league_points", 0)
        profile.setdefault("wins", 0)
        profile.setdefault("losses", 0)
        profile.setdefault("forfeits", 0)
        profile.setdefault("stats", asdict(GameStats()))

    @staticmethod
    def add_event(room, message):
        room["events"].append(message)
        room["events"] = room["events"][-20:]

    def profile_to_player(self, profile):
        stats = GameStats(**profile["stats"])
        return Player(
            name=profile["name"],
            balance=profile["balance"],
            free_spins=profile["free_spins"],
            stats=stats,
            history=list(profile["history"]),
        )

    @staticmethod
    def player_to_profile(player, profile):
        profile["balance"] = player.balance
        profile["free_spins"] = player.free_spins
        profile["stats"] = asdict(player.stats)
        profile["history"] = player.history[-50:]

    def require_room(self, code):
        room = self.backend.get_room(code.upper())
        if not room:
            raise ValueError("Room code not found.")
        return room

    def require_profile(self, player_id):
        profile = self.backend.get_profile(player_id)
        if not profile:
            raise ValueError("Player profile not found.")
        return profile

    @staticmethod
    def clean_name(name):
        return str(name or "Player").strip()[:24] or "Player"

    @staticmethod
    def clean_save_code(save_code):
        return str(save_code or "").strip().upper()

    @staticmethod
    def validate_stake(stake):
        stake = int(stake)
        if not MIN_ROOM_STAKE <= stake <= MAX_ROOM_STAKE:
            raise ValueError(
                f"Room stake must be between {MIN_ROOM_STAKE} and {MAX_ROOM_STAKE} coins."
            )
        return stake
