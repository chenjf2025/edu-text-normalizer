"""配置文件"""
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import yaml


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    cache_ttl: int = 3600


class LogConfig(BaseModel):
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 18005
    workers: int = 4
    reload: bool = False


class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.BASE_DIR = Path(__file__).parent.parent
        self.RULES_DIR = self.BASE_DIR / "app" / "rules"
        self.REDIS = RedisConfig()
        self.LOG = LogConfig()
        self.APP = AppConfig()
        self._rules_cache = {}

    def load_rule(self, rule_name: str) -> dict:
        if rule_name in self._rules_cache:
            return self._rules_cache[rule_name]
        rule_path = self.RULES_DIR / f"{rule_name}.yaml"
        if not rule_path.exists():
            return {}
        with open(rule_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._rules_cache[rule_name] = data
        return data


config = Config()