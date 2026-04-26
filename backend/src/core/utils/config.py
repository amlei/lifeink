from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


_SMTP_PRESETS: dict[str, dict] = {
    "qq": {"host": "smtp.qq.com", "port": 465, "use_tls": False, "use_ssl": True},
    "outlook": {"host": "smtp-mail.outlook.com", "port": 587, "use_tls": True, "use_ssl": False},
    "163": {"host": "smtp.163.com", "port": 465, "use_tls": False, "use_ssl": True},
    "126": {"host": "smtp.126.com", "port": 465, "use_tls": False, "use_ssl": True},
    "yeah": {"host": "smtp.yeah.net", "port": 465, "use_tls": False, "use_ssl": True},
}


class SmtpConfig(BaseModel):
    provider: str = "qq"
    host: str = ""
    port: int = 0
    use_tls: bool = False
    use_ssl: bool = False
    username: str = ""
    password: str = ""
    from_email: str = ""

    def resolved(self) -> dict:
        preset = _SMTP_PRESETS.get(self.provider, {})
        return {
            "host": self.host or preset.get("host", ""),
            "port": self.port or preset.get("port", 0),
            "use_tls": self.use_tls or preset.get("use_tls", False),
            "use_ssl": self.use_ssl or preset.get("use_ssl", False),
            "username": self.username,
            "password": self.password,
            "from_email": self.from_email or self.username,
        }


class Config(BaseModel):
    smtp: SmtpConfig = SmtpConfig()


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is not None:
        return _config
    path = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        _config = Config(**data)
    else:
        _config = Config()
    return _config
