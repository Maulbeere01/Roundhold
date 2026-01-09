from __future__ import annotations

from td_shared.game import RoundResultData


class EconomyManager:
    """Tracks player lives and gold, and applies economic operations"""

    def __init__(self, initial_lives: int, initial_gold: int) -> None:
        self._lives = {"A": int(initial_lives), "B": int(initial_lives)}
        self._gold = {"A": int(initial_gold), "B": int(initial_gold)}

    def get_lives(self, player_id: str) -> int:
        return self._lives[player_id]

    def lose_lives(self, player_id: str, amount: int) -> None:
        self._lives[player_id] = max(0, self._lives[player_id] - int(amount))

    def get_gold(self, player_id: str) -> int:
        return self._gold[player_id]

    def can_spend(self, player_id: str, amount: int) -> bool:
        return self._gold[player_id] >= int(amount)

    def spend_gold(self, player_id: str, amount: int) -> bool:
        """Try to spend gold; return True on success."""
        amount = int(amount)
        if not self.can_spend(player_id, amount):
            return False
        self._gold[player_id] -= amount
        return True

    def add_gold(self, player_id: str, amount: int) -> None:
        self._gold[player_id] += int(amount)

    def apply_round_result(self, result: RoundResultData) -> None:
        """Update lives/gold according to authoritative round result."""
        # Apply operations using functional mapping
        operations = [
            (self.lose_lives, "A", result["lives_lost_player_A"]),
            (self.lose_lives, "B", result["lives_lost_player_B"]),
            (self.add_gold, "A", result["gold_earned_player_A"]),
            (self.add_gold, "B", result["gold_earned_player_B"]),
        ]
        list(map(lambda op: op[0](op[1], op[2]), operations))

