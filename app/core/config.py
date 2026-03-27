from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "phoenixdb"
    postgres_user: str = "phoenix"
    postgres_password: str = ""
    postgres_min_pool: int = 2
    postgres_max_pool: int = 10
    postgres_ssl: bool = False   # FortiSIEM 내부 DB는 기본적으로 SSL 없음

    # ClickHouse
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_db: str = "default"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_secure: bool = False

    # Adapter server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    log_level: str = "INFO"

    # Redis (job queue + result store)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_queue_name: str = "fsm_events"
    redis_result_ttl: int = 3600   # job 결과 보관 시간 (초)
    redis_failure_ttl: int = 300   # 실패 job 보관 시간 (초)

    # API Basic Auth (이 서버로 들어오는 요청에 대한 인증)
    # FortiSIEM 표준 형식: Basic base64(<org>/<username>:<password>)
    # FortiSOAR connector의 organization/username/password와 동일하게 설정
    api_org: str = "super"
    api_username: str = "admin"
    api_password: str = "changeme"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
