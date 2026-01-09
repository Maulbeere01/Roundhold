from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NetworkListener(Protocol):
    """
    Interface for screens that handle network events from the game server.
    """

    def on_round_start(self, round_start_pb: Any) -> None: ...

    def on_round_result(self, round_result_pb: Any) -> None: ...

    def on_tower_placed(self, tower_placed_pb: Any) -> None: ...
