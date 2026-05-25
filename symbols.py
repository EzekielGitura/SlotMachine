SLOT_CONFIG = {
    "rows": 3,
    "cols": 3,
    "min_bet": 1,
    "max_bet": 100,
    "wild_symbol": "WILD",
    "scatter_symbol": "SCATTER",
    "wild_payout": 15,
    "free_spins_award": 3,
    "scatter_bonus_multiplier": 5,
    "bonus_multipliers": [2, 3, 5],
    "jackpots": {
        "SEVEN": 25,
        "DIAMOND": 15,
    },
    "symbols": {
        "SEVEN": {
            "label": "7",
            "weight": 2,
            "payout": 20,
            "color": "bright_red",
        },
        "DIAMOND": {
            "label": "DMD",
            "weight": 3,
            "payout": 14,
            "color": "bright_cyan",
        },
        "BELL": {
            "label": "BELL",
            "weight": 5,
            "payout": 8,
            "color": "yellow",
        },
        "CHERRY": {
            "label": "CHRY",
            "weight": 7,
            "payout": 5,
            "color": "red",
        },
        "BAR": {
            "label": "BAR",
            "weight": 8,
            "payout": 4,
            "color": "white",
        },
        "LEMON": {
            "label": "LEMN",
            "weight": 10,
            "payout": 2,
            "color": "green",
        },
        "WILD": {
            "label": "WILD",
            "weight": 3,
            "payout": 0,
            "color": "magenta",
        },
        "SCATTER": {
            "label": "SCAT",
            "weight": 3,
            "payout": 0,
            "color": "bright_blue",
        },
    },
}

PAYLINE_CONFIG = [
    {"name": "Top row", "positions": [(0, 0), (1, 0), (2, 0)]},
    {"name": "Middle row", "positions": [(0, 1), (1, 1), (2, 1)]},
    {"name": "Bottom row", "positions": [(0, 2), (1, 2), (2, 2)]},
    {"name": "Down diagonal", "positions": [(0, 0), (1, 1), (2, 2)]},
    {"name": "Up diagonal", "positions": [(0, 2), (1, 1), (2, 0)]},
]
