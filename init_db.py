"""Initialize or safely upgrade the BizForge database."""

from database.db import DB, init_db


def init_database():
    init_db()
    print(f"BizForge database is ready: {DB}")


if __name__ == "__main__":
    init_database()
