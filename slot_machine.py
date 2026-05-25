import random
from dataclasses import dataclass, field

from symbols import PAYLINE_CONFIG, SLOT_CONFIG


@dataclass(frozen=True)
class Payline:
    name: str
    positions: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class PaylineWin:
    name: str
    symbols: tuple[str, ...]
    matched_symbol: str
    amount: int
    jackpot_hit: bool = False


@dataclass
class SpinEvaluation:
    columns: list[list[str]]
    line_wins: list[PaylineWin]
    total_winnings: int
    active_paylines: int
    bet: int
    total_bet: int
    free_spin_used: bool = False
    scatter_count: int = 0
    scatter_bonus: int = 0
    free_spins_awarded: int = 0
    bonus_multiplier: int = 1
    near_misses: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    @property
    def jackpot_hit(self):
        return any(line.jackpot_hit for line in self.line_wins)

    @property
    def net(self):
        return self.total_winnings - self.total_bet


class PayTable:
    def __init__(self, config=None):
        self.config = config or SLOT_CONFIG
        self.symbols = self.config["symbols"]

    def label_for(self, symbol):
        return self.symbols[symbol]["label"]

    def payout_for(self, symbol):
        return self.symbols[symbol]["payout"]

    def weight_for(self, symbol):
        return self.symbols[symbol]["weight"]

    def color_for(self, symbol):
        return self.symbols[symbol].get("color", "white")

    def labels_for_line(self, symbols):
        return [self.label_for(symbol) for symbol in symbols]

    def symbol_rows(self):
        rows = []
        for symbol, details in self.symbols.items():
            rows.append(
                {
                    "symbol": symbol,
                    "label": details["label"],
                    "weight": details["weight"],
                    "payout": details["payout"],
                }
            )
        return rows


class SlotMachine:
    def __init__(self, config=None, paylines=None, rng=None):
        self.config = config or SLOT_CONFIG
        self.pay_table = PayTable(self.config)
        self.paylines = [
            Payline(line["name"], tuple(line["positions"]))
            for line in (paylines or PAYLINE_CONFIG)
        ]
        self.rng = rng or random.Random()

    @property
    def rows(self):
        return self.config["rows"]

    @property
    def cols(self):
        return self.config["cols"]

    @property
    def min_bet(self):
        return self.config["min_bet"]

    @property
    def max_bet(self):
        return self.config["max_bet"]

    @property
    def max_paylines(self):
        return len(self.paylines)

    def build_symbol_pool(self):
        pool = []
        for symbol, details in self.config["symbols"].items():
            pool.extend([symbol] * details["weight"])
        return pool

    def spin_reels(self):
        symbol_pool = self.build_symbol_pool()
        columns = []

        for _ in range(self.cols):
            current_symbols = symbol_pool[:]
            column = []

            for _ in range(self.rows):
                value = self.rng.choice(current_symbols)
                current_symbols.remove(value)
                column.append(value)

            columns.append(column)

        return columns

    def spin(self, active_payline_count, bet, free_spin_used=False):
        columns = self.spin_reels()
        return self.evaluate(columns, active_payline_count, bet, free_spin_used)

    def evaluate(self, columns, active_payline_count, bet, free_spin_used=False):
        active_paylines = self.paylines[:active_payline_count]
        line_wins = []
        scatter_count = self.count_symbol(columns, self.config["scatter_symbol"])
        free_spins_awarded = 0
        scatter_bonus = 0
        bonus_multiplier = 1
        messages = []

        if scatter_count >= 3:
            free_spins_awarded = self.config["free_spins_award"]
            bonus_multiplier = self.rng.choice(self.config["bonus_multipliers"])
            scatter_bonus = (
                bet
                * self.config["scatter_bonus_multiplier"]
                * scatter_count
                * bonus_multiplier
            )
            messages.append(
                f"Scatter bonus: {free_spins_awarded} free spins and a {bonus_multiplier}x multiplier."
            )

        for payline in active_paylines:
            line_symbols = tuple(self.symbols_for_payline(columns, payline))
            matched_symbol = self.get_line_match(line_symbols)

            if matched_symbol is None:
                continue

            amount, jackpot_hit = self.calculate_line_payout(
                matched_symbol,
                line_symbols,
                bet,
            )
            amount *= bonus_multiplier

            if amount > 0:
                line_wins.append(
                    PaylineWin(
                        payline.name,
                        line_symbols,
                        matched_symbol,
                        amount,
                        jackpot_hit,
                    )
                )

        near_misses = self.detect_near_misses(columns, active_paylines)
        if near_misses:
            messages.extend([f"Near miss: {near_miss}" for near_miss in near_misses])

        total_winnings = sum(line.amount for line in line_wins) + scatter_bonus
        total_bet = 0 if free_spin_used else active_payline_count * bet

        return SpinEvaluation(
            columns=columns,
            line_wins=line_wins,
            total_winnings=total_winnings,
            active_paylines=active_payline_count,
            bet=bet,
            total_bet=total_bet,
            free_spin_used=free_spin_used,
            scatter_count=scatter_count,
            scatter_bonus=scatter_bonus,
            free_spins_awarded=free_spins_awarded,
            bonus_multiplier=bonus_multiplier,
            near_misses=near_misses,
            messages=messages,
        )

    def symbols_for_payline(self, columns, payline):
        return [
            columns[column_index][row_index]
            for column_index, row_index in payline.positions
        ]

    def get_line_match(self, line_symbols):
        wild_symbol = self.config["wild_symbol"]
        scatter_symbol = self.config["scatter_symbol"]

        if scatter_symbol in line_symbols:
            return None

        non_wild_symbols = [
            symbol for symbol in line_symbols if symbol != wild_symbol
        ]

        if not non_wild_symbols:
            return wild_symbol

        first_symbol = non_wild_symbols[0]
        if all(symbol == first_symbol for symbol in non_wild_symbols):
            return first_symbol

        return None

    def calculate_line_payout(self, matched_symbol, line_symbols, bet):
        wild_symbol = self.config["wild_symbol"]
        jackpot_multiplier = self.config["jackpots"].get(matched_symbol, 0)
        jackpot_hit = False

        if matched_symbol == wild_symbol:
            return bet * self.config["wild_payout"], jackpot_hit

        amount = self.pay_table.payout_for(matched_symbol) * bet

        if jackpot_multiplier and wild_symbol not in line_symbols:
            amount += bet * jackpot_multiplier
            jackpot_hit = True

        return amount, jackpot_hit

    def detect_near_misses(self, columns, active_paylines):
        near_misses = []
        rare_symbols = set(self.config["jackpots"])

        for payline in active_paylines:
            line_symbols = self.symbols_for_payline(columns, payline)
            if self.get_line_match(line_symbols):
                continue

            for rare_symbol in rare_symbols:
                if line_symbols.count(rare_symbol) == 2:
                    label = self.pay_table.label_for(rare_symbol)
                    near_misses.append(f"{payline.name} almost hit {label}")

        return near_misses

    @staticmethod
    def count_symbol(columns, symbol):
        return sum(column.count(symbol) for column in columns)


def get_slot_machine_spin(rows, cols, symbols):
    config = {
        **SLOT_CONFIG,
        "rows": rows,
        "cols": cols,
        "symbols": {
            symbol: {"label": symbol, "weight": count, "payout": 0}
            for symbol, count in symbols.items()
        },
    }
    return SlotMachine(config=config).spin_reels()


def check_winnings(columns, active_paylines, bet, values):
    symbols = {
        symbol: {"label": symbol, "weight": 1, "payout": payout}
        for symbol, payout in values.items()
    }
    config = {**SLOT_CONFIG, "symbols": symbols}
    paylines = [
        {"name": name, "positions": positions}
        for name, positions in active_paylines
    ]
    result = SlotMachine(config=config, paylines=paylines).evaluate(
        columns,
        len(active_paylines),
        bet,
    )
    winning_lines = [
        f"{line.name} ({' '.join(line.symbols)}) pays ${line.amount}"
        for line in result.line_wins
    ]
    return result.total_winnings, winning_lines, result.jackpot_hit
