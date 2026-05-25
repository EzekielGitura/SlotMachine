import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from mimetypes import guess_type
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from online_store import OnlineStore


WEB_ROOT = Path(__file__).parent / "web"
STORE = OnlineStore()


def result_state(store, result, awards):
    pay_table = store.slot_game.slot_machine.pay_table
    return {
        "columns": [
            [
                {
                    "symbol": symbol,
                    "label": pay_table.label_for(symbol),
                    "color": pay_table.color_for(symbol),
                }
                for symbol in column
            ]
            for column in result.columns
        ],
        "totalBet": result.total_bet,
        "totalWinnings": result.total_winnings,
        "net": result.net,
        "freeSpinUsed": result.free_spin_used,
        "freeSpinsAwarded": result.free_spins_awarded,
        "scatterBonus": result.scatter_bonus,
        "bonusMultiplier": result.bonus_multiplier,
        "jackpotHit": result.jackpot_hit,
        "nearMisses": result.near_misses,
        "messages": result.messages,
        "awards": awards,
        "lineWins": [
            {
                "name": line.name,
                "symbols": [pay_table.label_for(symbol) for symbol in line.symbols],
                "amount": line.amount,
                "jackpot": line.jackpot_hit,
            }
            for line in result.line_wins
        ],
    }


class SlotRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")

        try:
            if path == "/health":
                self.send_json(200, {"status": "ok", "store": STORE.backend_name})
                return

            if path == "/api/config":
                self.send_json(200, {"config": STORE.config_state()})
                return

            if len(parts) == 4 and parts[:2] == ["api", "rooms"] and parts[3] == "state":
                self.handle_room_state(parts[2])
                return

            self.serve_static(path)
        except ValueError as error:
            self.send_json(400, {"error": str(error)})

    def do_POST(self):
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")

        try:
            if path == "/api/rooms":
                self.handle_create_room()
                return

            if len(parts) == 4 and parts[:2] == ["api", "rooms"] and parts[3] == "join":
                self.handle_join_room(parts[2])
                return

            if len(parts) == 4 and parts[:2] == ["api", "rooms"] and parts[3] == "spin":
                self.handle_spin(parts[2])
                return

            if len(parts) == 4 and parts[:2] == ["api", "rooms"] and parts[3] == "leave":
                self.handle_leave_room(parts[2])
                return

            if len(parts) == 4 and parts[:2] == ["api", "rooms"] and parts[3] == "finish":
                self.handle_finish_room(parts[2])
                return

            if len(parts) == 4 and parts[:2] == ["api", "rooms"] and parts[3] == "chat":
                self.handle_room_chat(parts[2])
                return

            if path == "/api/friends/add":
                self.handle_add_friend()
                return

            if path == "/api/rewards/daily":
                self.handle_daily_reward()
                return

            if path == "/api/profile/resume":
                self.handle_resume_profile()
                return

            if path == "/api/profile":
                self.handle_create_profile()
                return

            if path == "/api/profile/pause":
                self.handle_pause_profile()
                return

            self.send_json(404, {"error": "Not found"})
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body."})

    def handle_create_room(self):
        data = self.read_json()
        name = str(data.get("name", "Player")).strip() or "Player"
        player_id = str(data.get("playerId", "")).strip() or None
        stake = int(data.get("stake", 500))

        room_code, player_id, state = STORE.create_room(name, player_id, stake)
        self.send_json(201, {"roomCode": room_code, "playerId": player_id, "state": state})

    def handle_join_room(self, code):
        data = self.read_json()
        name = str(data.get("name", "Player")).strip() or "Player"
        player_id = str(data.get("playerId", "")).strip() or None

        player_id, state = STORE.join_room(code, name, player_id)
        self.send_json(200, {"roomCode": state["roomCode"], "playerId": player_id, "state": state})

    def handle_spin(self, code):
        data = self.read_json()
        player_id = str(data.get("playerId", ""))
        lines = int(data.get("lines", 1))
        bet = int(data.get("bet", 1))

        result, state, awards = STORE.spin(code, player_id, lines, bet)
        spin = result_state(STORE, result, awards)
        self.send_json(200, {"state": state, "spin": spin})

    def handle_leave_room(self, code):
        data = self.read_json()
        player_id = str(data.get("playerId", ""))
        state = STORE.leave_room(code, player_id)
        self.send_json(200, {"state": state})

    def handle_finish_room(self, code):
        data = self.read_json()
        player_id = str(data.get("playerId", ""))
        state = STORE.finish_room(code, player_id)
        self.send_json(200, {"state": state})

    def handle_room_chat(self, code):
        data = self.read_json()
        player_id = str(data.get("playerId", "")).strip()
        message = str(data.get("message", ""))
        kind = str(data.get("kind", "text"))
        state = STORE.add_chat_message(code, player_id, message, kind)
        self.send_json(200, {"state": state})

    def handle_add_friend(self):
        data = self.read_json()
        player_id = str(data.get("playerId", "")).strip()
        friend_code = str(data.get("friendCode", "")).strip()
        profile = STORE.add_friend(player_id, friend_code)
        self.send_json(200, {"profile": profile})

    def handle_daily_reward(self):
        data = self.read_json()
        player_id = str(data.get("playerId", "")).strip() or None
        name = str(data.get("name", "Player")).strip() or "Player"
        reward = STORE.claim_daily_reward(player_id, name)
        self.send_json(200, {"reward": reward})

    def handle_resume_profile(self):
        data = self.read_json()
        save_code = str(data.get("saveCode", "")).strip()
        name = str(data.get("name", "")).strip() or None
        resumed = STORE.resume_profile(save_code, name)
        self.send_json(200, resumed)

    def handle_create_profile(self):
        data = self.read_json()
        name = str(data.get("name", "Player")).strip() or "Player"
        profile = STORE.create_profile(name)
        self.send_json(
            201,
            {
                "profile": STORE.profile_state(
                    profile,
                    include_save_code=True,
                    include_player_id=True,
                )
            },
        )

    def handle_pause_profile(self):
        data = self.read_json()
        player_id = str(data.get("playerId", "")).strip()
        profile = STORE.pause_profile(player_id)
        self.send_json(200, {"profile": profile})

    def handle_room_state(self, code):
        query = parse_qs(urlparse(self.path).query)
        player_id = query.get("playerId", [""])[0]
        state = STORE.room_state(code, player_id)
        self.send_json(200, {"state": state})

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, path):
        if path == "/":
            path = "/index.html"

        requested = (WEB_ROOT / path.lstrip("/")).resolve()
        root = WEB_ROOT.resolve()

        if root not in requested.parents and requested != root:
            self.send_error(403)
            return

        if not requested.exists() or requested.is_dir():
            self.send_error(404)
            return

        body = requested.read_bytes()
        content_type = guess_type(str(requested))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def run(host="127.0.0.1", port=8000):
    server = ThreadingHTTPServer((host, port), SlotRequestHandler)
    print(f"Slot room server running at http://{host}:{port} using {STORE.backend_name} store")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the slot room web server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    run(args.host, args.port)
