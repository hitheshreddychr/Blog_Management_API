from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "blog.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def run_database_migrations():
    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    with engine.begin() as connection:
        if "auth_provider" not in existing_columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN auth_provider
                    VARCHAR(30)
                    NOT NULL
                    DEFAULT 'local'
                    """
                )
            )

        if "auth0_user_id" not in existing_columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN auth0_user_id
                    VARCHAR(255)
                    """
                )
            )

        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                ix_users_auth0_user_id
                ON users(auth0_user_id)
                WHERE auth0_user_id IS NOT NULL
                """
            )
        )


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()