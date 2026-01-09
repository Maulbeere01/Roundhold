from __future__ import annotations

import logging
import signal
import time

from .network.rpc_server import serve


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    server = serve()

    stop = False

    def _handle_sigint(sig, frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _handle_sigint)
    signal.signal(signal.SIGTERM, _handle_sigint)

    try:
        while not stop:
            time.sleep(0.5)
    finally:
        server.stop(grace=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


