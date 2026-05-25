import random
import tempfile
import unittest
from pathlib import Path

from game import Player, SlotGame
from online_store import (
    DAILY_REWARD,
    LEAVE_PENALTY,
    ROOM_VICTORY_BONUS,
    RANK_GIFTS,
    STARTING_COINS,
    MemoryBackend,
    OnlineStore,
)
from slot_machine import SlotMachine


class FixedRng:
    def choice(self, values):
        return values[0]


class SlotMachineTests(unittest.TestCase):
    def test_spin_returns_requested_grid_size(self):
        machine = SlotMachine(rng=random.Random(7))

        columns = machine.spin_reels()

        self.assertEqual(len(columns), machine.cols)
        self.assertTrue(all(len(column) == machine.rows for column in columns))

    def test_matching_payline_pays_once_with_jackpot(self):
        machine = SlotMachine()
        columns = [
            ["SEVEN", "LEMON", "CHERRY"],
            ["SEVEN", "BAR", "BELL"],
            ["SEVEN", "CHERRY", "LEMON"],
        ]

        result = machine.evaluate(columns, active_payline_count=1, bet=2)

        expected = (20 * 2) + (25 * 2)
        self.assertEqual(result.total_winnings, expected)
        self.assertEqual(len(result.line_wins), 1)
        self.assertTrue(result.jackpot_hit)

    def test_wilds_complete_a_line(self):
        machine = SlotMachine()
        columns = [
            ["BAR", "LEMON", "CHERRY"],
            ["WILD", "BAR", "BELL"],
            ["BAR", "CHERRY", "LEMON"],
        ]

        result = machine.evaluate(columns, active_payline_count=1, bet=5)

        self.assertEqual(result.total_winnings, machine.pay_table.payout_for("BAR") * 5)
        self.assertEqual(len(result.line_wins), 1)
        self.assertFalse(result.jackpot_hit)

    def test_all_wilds_pay_special_wild_value(self):
        machine = SlotMachine()
        columns = [
            ["WILD", "LEMON", "CHERRY"],
            ["WILD", "BAR", "BELL"],
            ["WILD", "CHERRY", "LEMON"],
        ]

        result = machine.evaluate(columns, active_payline_count=1, bet=3)

        self.assertEqual(result.total_winnings, 45)
        self.assertEqual(len(result.line_wins), 1)

    def test_diagonal_payline_can_win(self):
        machine = SlotMachine()
        columns = [
            ["LEMON", "BAR", "DIAMOND"],
            ["BELL", "DIAMOND", "CHERRY"],
            ["DIAMOND", "LEMON", "BAR"],
        ]

        result = machine.evaluate(columns, active_payline_count=5, bet=4)

        expected = (14 * 4) + (15 * 4)
        self.assertEqual(result.total_winnings, expected)
        self.assertEqual(result.line_wins[0].name, "Up diagonal")
        self.assertTrue(result.jackpot_hit)

    def test_scatters_award_bonus_free_spins_and_multiplier(self):
        machine = SlotMachine(rng=FixedRng())
        columns = [
            ["SCATTER", "LEMON", "CHERRY"],
            ["BELL", "SCATTER", "BAR"],
            ["DIAMOND", "LEMON", "SCATTER"],
        ]

        result = machine.evaluate(columns, active_payline_count=5, bet=2)

        self.assertEqual(result.free_spins_awarded, 3)
        self.assertEqual(result.bonus_multiplier, 2)
        self.assertEqual(result.scatter_bonus, 60)

    def test_slot_game_updates_balance_stats_and_history(self):
        game = SlotGame(slot_machine=SlotMachine(rng=random.Random(4)))
        player = Player(name="Ada", balance=100)

        result = game.spin(player, active_payline_count=3, bet=5)

        self.assertEqual(player.balance, 100 - result.total_bet + result.total_winnings)
        self.assertEqual(player.stats.spins, 1)
        self.assertEqual(len(player.history), 1)

    def test_player_can_save_and_load_balance_and_history(self):
        player = Player(name="Ada", balance=125)
        player.history.append({"won": 25, "balance_after": 125})

        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "savegame.json"
            player.save(save_path)
            loaded = Player.load(save_path)

        self.assertEqual(loaded.name, "Ada")
        self.assertEqual(loaded.balance, 125)
        self.assertEqual(loaded.history[0]["won"], 25)

    def test_online_profiles_start_with_fixed_coins_and_room_stake_is_held(self):
        store = OnlineStore(backend=MemoryBackend())

        code, player_id, state = store.create_room("Ada", stake=500)

        self.assertEqual(state["you"]["balance"], STARTING_COINS - 500)
        self.assertEqual(state["room"]["pot"], 500)
        self.assertEqual(state["room"]["stake"], 500)
        self.assertEqual(code, state["roomCode"])
        self.assertEqual(player_id, state["viewerId"])

    def test_joining_room_deducts_same_stake_and_updates_pot(self):
        store = OnlineStore(backend=MemoryBackend())
        code, _, _ = store.create_room("Ada", stake=500)

        _, state = store.join_room(code, "Ben")

        self.assertEqual(state["room"]["pot"], 1000)
        self.assertEqual(state["room"]["status"], "active")
        self.assertEqual(state["you"]["balance"], STARTING_COINS - 500)

    def test_leaving_room_forfeits_stake_and_deducts_penalty(self):
        store = OnlineStore(backend=MemoryBackend())
        code, _, _ = store.create_room("Ada", stake=500)
        ben_id, _ = store.join_room(code, "Ben")

        state = store.leave_room(code, ben_id)

        self.assertTrue(state["you"]["forfeited"])
        self.assertEqual(state["you"]["balance"], STARTING_COINS - 500 - LEAVE_PENALTY)
        self.assertEqual(state["room"]["pot"], 1000)

    def test_finishing_room_awards_pot_and_victory_bonus_to_winner(self):
        store = OnlineStore(backend=MemoryBackend())
        code, ada_id, _ = store.create_room("Ada", stake=500)
        store.join_room(code, "Ben")

        state = store.finish_room(code, ada_id)

        winner = next(player for player in state["players"] if player["id"] == ada_id)
        self.assertEqual(state["room"]["status"], "completed")
        self.assertEqual(state["room"]["pot"], 0)
        self.assertEqual(winner["balance"], STARTING_COINS - 500 + 1000 + ROOM_VICTORY_BONUS + 1500)
        self.assertEqual(winner["wins"], 1)

    def test_daily_reward_can_only_be_claimed_once_per_day(self):
        store = OnlineStore(backend=MemoryBackend())
        profile = store.create_profile("Ada")

        reward = store.claim_daily_reward(profile["id"])

        self.assertEqual(reward["amount"], DAILY_REWARD)
        self.assertEqual(reward["profile"]["balance"], STARTING_COINS + DAILY_REWARD)
        with self.assertRaises(ValueError):
            store.claim_daily_reward(profile["id"])

    def test_room_state_assigns_rank_gifts_to_top_five(self):
        store = OnlineStore(backend=MemoryBackend())
        code, first_id, _ = store.create_room("Ada", stake=500)
        store.join_room(code, "Ben")
        store.join_room(code, "Cy")
        store.join_room(code, "Dee")
        store.join_room(code, "Eli")
        store.join_room(code, "Fay")

        state = store.room_state(code, first_id)

        self.assertEqual(len(state["rankGifts"]), len(RANK_GIFTS))
        self.assertEqual(state["players"][0]["gift"]["name"], RANK_GIFTS[1]["name"])
        self.assertEqual(state["players"][4]["gift"]["name"], RANK_GIFTS[5]["name"])
        self.assertIsNone(state["players"][5]["gift"])


if __name__ == "__main__":
    unittest.main()
