from __future__ import annotations

from td_shared.game import RoundResultData


class EconomyManager:
    """Tracks player lives and gold, and applies economic operations"""

    def __init__(self, initial_lives: int, initial_gold: int) -> None:
        # Preconditions
        assert initial_lives > 0, f"initial_lives must be > 0, not {initial_lives}"
        assert initial_gold >= 0, f"initial_gold must be >= 0, not {initial_gold}"

        self._lives = {"A": int(initial_lives), "B": int(initial_lives)}
        self._gold = {"A": int(initial_gold), "B": int(initial_gold)}

        # Postconditions (invariants)
        assert self._lives["A"] == int(
            initial_lives
        ), "Player A lives not initialized correctly"
        assert self._lives["B"] == int(
            initial_lives
        ), "Player B lives not initialized correctly"
        assert self._gold["A"] == int(
            initial_gold
        ), "Player A gold not initialized correctly"
        assert self._gold["B"] == int(
            initial_gold
        ), "Player B gold not initialized correctly"
        assert self._lives["A"] > 0, "Player A lives must be > 0 after initialization"
        assert self._lives["B"] > 0, "Player B lives must be > 0 after initialization"
        assert self._gold["A"] >= 0, "Player A gold must be >= 0 after initialization"
        assert self._gold["B"] >= 0, "Player B gold must be >= 0 after initialization"

    def get_lives(self, player_id: str) -> int:
        return self._lives[player_id]

    def lose_lives(self, player_id: str, amount: int) -> None:
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert amount >= 0, f"amount must not be negative: {amount}"

        old_lives = self._lives[player_id]
        self._lives[player_id] = max(0, self._lives[player_id] - int(amount))

        # Postcondition
        assert self._lives[player_id] == max(
            0, old_lives - int(amount)
        ), "Lives were not correctly reduced"

    def get_gold(self, player_id: str) -> int:
        return self._gold[player_id]

    def can_spend(self, player_id: str, amount: int) -> bool:
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert amount >= 0, f"amount must not be negative: {amount}"

        return self._gold[player_id] >= int(amount)

    def spend_gold(self, player_id: str, amount: int) -> bool:
        """Try to spend gold; return True on success."""
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert amount >= 0, f"amount must not be negative: {amount}"

        amount = int(amount)
        old_gold = self._gold[player_id]

        if not self.can_spend(player_id, amount):
            # Postcondition for error case: gold unchanged
            assert (
                self._gold[player_id] == old_gold
            ), "Gold should remain unchanged on error"
            return False

        self._gold[player_id] -= amount

        # Postcondition for success case
        assert (
            self._gold[player_id] == old_gold - amount
        ), f"Gold was not correctly deducted: expected {old_gold - amount}, got {self._gold[player_id]}"
        assert self._gold[player_id] >= 0, "Gold must not be negative"
        return True

    def add_gold(self, player_id: str, amount: int) -> None:
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert amount >= 0, f"amount must not be negative: {amount}"

        old_gold = self._gold[player_id]
        self._gold[player_id] += int(amount)

        # Postcondition
        assert (
            self._gold[player_id] == old_gold + int(amount)
        ), f"Gold was not correctly increased: expected {old_gold + int(amount)}, got {self._gold[player_id]}"

    def apply_round_result(self, result: RoundResultData) -> None:
        """Update lives/gold according to authoritative round result."""
        # Preconditions
        assert isinstance(result, dict), "result must be a dict"
        assert "lives_lost_player_A" in result, "Missing lives_lost_player_A in result"
        assert "lives_lost_player_B" in result, "Missing lives_lost_player_B in result"
        assert (
            "gold_earned_player_A" in result
        ), "Missing gold_earned_player_A in result"
        assert (
            "gold_earned_player_B" in result
        ), "Missing gold_earned_player_B in result"
        assert (
            result["lives_lost_player_A"] >= 0
        ), f"lives_lost_player_A must be >= 0, not {result['lives_lost_player_A']}"
        assert (
            result["lives_lost_player_B"] >= 0
        ), f"lives_lost_player_B must be >= 0, not {result['lives_lost_player_B']}"
        assert (
            result["gold_earned_player_A"] >= 0
        ), f"gold_earned_player_A must be >= 0, not {result['gold_earned_player_A']}"
        assert (
            result["gold_earned_player_B"] >= 0
        ), f"gold_earned_player_B must be >= 0, not {result['gold_earned_player_B']}"

        # Track state before operations
        old_lives_A = self.get_lives("A")
        old_lives_B = self.get_lives("B")
        old_gold_A = self.get_gold("A")
        old_gold_B = self.get_gold("B")

        # Apply operations using functional mapping
        operations = [
            (self.lose_lives, "A", result["lives_lost_player_A"]),
            (self.lose_lives, "B", result["lives_lost_player_B"]),
            (self.add_gold, "A", result["gold_earned_player_A"]),
            (self.add_gold, "B", result["gold_earned_player_B"]),
        ]
        list(map(lambda op: op[0](op[1], op[2]), operations))

        # Postconditions
        assert (
            self.get_lives("A") == max(0, old_lives_A - result["lives_lost_player_A"])
        ), f"Player A lives not correctly updated: expected {max(0, old_lives_A - result['lives_lost_player_A'])}, got {self.get_lives('A')}"
        assert (
            self.get_lives("B") == max(0, old_lives_B - result["lives_lost_player_B"])
        ), f"Player B lives not correctly updated: expected {max(0, old_lives_B - result['lives_lost_player_B'])}, got {self.get_lives('B')}"
        assert (
            self.get_gold("A") == old_gold_A + result["gold_earned_player_A"]
        ), f"Player A gold not correctly updated: expected {old_gold_A + result['gold_earned_player_A']}, got {self.get_gold('A')}"
        assert (
            self.get_gold("B") == old_gold_B + result["gold_earned_player_B"]
        ), f"Player B gold not correctly updated: expected {old_gold_B + result['gold_earned_player_B']}, got {self.get_gold('B')}"
