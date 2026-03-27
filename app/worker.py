"""
Worker process entry point.

Usage:
    # 워커 1개
    python -m app.worker

    # 워커 N개 (단일 명령으로 N개 서브프로세스 생성)
    python -m app.worker --workers 4
"""

from __future__ import annotations

import argparse
import logging
import multiprocessing
import os
import signal
import sys

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s [pid:%(process)d]: %(message)s",
)

logger = logging.getLogger("fsmapi.worker")


def _run_worker() -> None:
    """Single worker process body — called in each subprocess."""
    from rq import Queue, Worker
    from app.core.config import get_settings
    from app.queue.redis_client import get_redis

    settings = get_settings()
    redis_conn = get_redis()
    queue_name = settings.redis_queue_name

    worker = Worker([Queue(queue_name, connection=redis_conn)], connection=redis_conn)
    logger.info("Worker started — queue: %s", queue_name)

    def _shutdown(signum, frame):
        logger.info("Shutdown signal, stopping worker…")
        worker.stop_executing_jobs()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    worker.work(with_scheduler=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="fsmapi rq worker")
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=1,
        help="Number of worker processes to spawn (default: 1)",
    )
    args = parser.parse_args()
    n = max(1, args.workers)

    if n == 1:
        # 단일 워커는 현재 프로세스에서 직접 실행
        _run_worker()
    else:
        logger.info("Spawning %d worker processes…", n)
        processes: list[multiprocessing.Process] = []

        for _ in range(n):
            p = multiprocessing.Process(target=_run_worker, daemon=True)
            p.start()
            processes.append(p)

        logger.info("All %d workers running (PIDs: %s)", n, [p.pid for p in processes])

        def _shutdown_all(signum, frame):
            logger.info("Shutdown signal received, terminating all workers…")
            for p in processes:
                p.terminate()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _shutdown_all)
        signal.signal(signal.SIGINT, _shutdown_all)

        # 메인 프로세스는 자식 프로세스 감시
        for p in processes:
            p.join()


if __name__ == "__main__":
    main()
