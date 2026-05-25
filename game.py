import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from slot_machine import SlotMachine


SAVE_FILE = Path("savegame.json")


@dataclass
class GameStats:
    spins: int = 0
    total_wagered: int = 0
    total_won: int = 0
    biggest_win: int = 0
    jackpots: int = 0
    winning_spins: int = 0
    free_spins_won: int = 0
    free_spins_used: int = 0

    def record_spin(self, result):
        self.spins += 1
        self.total_wagered += result.total_bet
        self.total_won += result.total_winnings
        self.biggest_win = max(self.biggest_win, result.total_winnings)
        self.free_spins_won += result.free_spins_awarded

        if result.free_spin_used:
            self.free_spins_used += 1
        if result.total_winnings > 0:
            self.winning_spins += 1
        if result.jackpot_hit:
            self.jackpots += 1

    @property
    def net(self):
        return self.total_won - self.total_wagered

    @property
    def win_rate(self):
        if self.spins == 0:
            return 0
        return self.winning_spins / self.spins


@dataclass
class Player:
    name: str
    balance: int
    free_spins: int = 0
    stats: GameStats = field(default_factory=GameStats)
    history: list[dict] = field(default_factory=list)

    def can_afford(self, total_bet):
        return self.free_spins > 0 or self.balance >= total_bet

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        stats = GameStats(**data.get("stats", {}))
        return cls(
            name=data.get("name", "Player"),
            balance=int(data.get("balance", 0)),
            free_spins=int(data.get("free_spins", 0)),
            stats=stats,
            history=list(data.get("history", [])),
        )

    def save(self, path=SAVE_FILE):
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path=SAVE_FILE):
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


class SlotGame:
    def __init__(self, slot_machine=None):
        self.slot_machine = slot_machine or SlotMachine()

    def spin(self, player, active_payline_count, bet):
        self.validate_spin(player, active_payline_count, bet)

        free_spin_used = player.free_spins > 0
        if free_spin_used:
            player.free_spins -= 1

        result = self.slot_machine.spin(active_payline_count, bet, free_spin_used)

        if not free_spin_used:
            player.balance -= result.total_bet

        player.balance += result.total_winnings
        player.free_spins += result.free_spins_awarded
        player.stats.record_spin(result)
        player.history.append(self.build_history_record(result, player.balance))

        return result

    def validate_spin(self, player, active_payline_count, bet):
        if not 1 <= active_payline_count <= self.slot_machine.max_paylines:
            raise ValueError("Choose a valid number of paylines.")

        if not self.slot_machine.min_bet <= bet <= self.slot_machine.max_bet:
            raise ValueError(
                f"Bet must be between ${self.slot_machine.min_bet} and ${self.slot_machine.max_bet}."
            )

        total_bet = active_payline_count * bet
        if not player.can_afford(total_bet):
            raise ValueError(f"{player.name} does not have enough balance.")

    def build_history_record(self, result, balance_after):
        return {
            "time": datetime.now().isoformat(timespec="seconds"),
            "bet": result.bet,
            "paylines": result.active_paylines,
            "total_bet": result.total_bet,
            "won": result.total_winnings,
            "net": result.net,
            "balance_after": balance_after,
            "jackpot": result.jackpot_hit,
            "free_spin": result.free_spin_used,
            "free_spins_awarded": result.free_spins_awarded,
            "bonus_multiplier": result.bonus_multiplier,
            "near_misses": result.near_misses,
        }
