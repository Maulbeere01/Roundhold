"""Network module for client-server communication."""

from .event_router import NetworkEventRouter
from .network import NetworkClient

__all__ = ["NetworkClient", "NetworkEventRouter"]
