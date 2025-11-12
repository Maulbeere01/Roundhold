"""Network layer: gRPC server and RPC handlers."""

from .rpc_server import GameRpcServer, serve

__all__ = [
    "GameRpcServer",
    "serve",
]

