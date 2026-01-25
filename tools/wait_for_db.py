import os
import time

import psycopg2


def main() -> None:
    host = os.getenv("POSTGRES_HOST", "db")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "narrator")
    password = os.getenv("POSTGRES_PASSWORD", "narrator")
    dbname = os.getenv("POSTGRES_DB", "narrator")
    timeout = int(os.getenv("POSTGRES_WAIT_TIMEOUT", "60"))

    start = time.monotonic()
    while True:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
            )
            conn.close()
            print("Database is ready")
            return
        except Exception:
            if time.monotonic() - start > timeout:
                raise SystemExit("Database not ready in time")
            time.sleep(1)


if __name__ == "__main__":
    main()
