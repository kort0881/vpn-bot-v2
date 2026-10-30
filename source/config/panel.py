"""Настройки VPN-панели (3x-UI) и каналов выдачи.

Имена переменных сохранены от прежнего config.py, поэтому старый .env подходит
без правок. Значения читаются через pydantic-settings и раздаются модулю
как обычные константы (panel_client.py импортирует их напрямую).
"""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class _PanelEnv(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=True
    )

    # --- 3x-UI: основной узел (DE/финка, каскадные каналы) ---
    PANEL_URL: str = ""
    PANEL_API_TOKEN: str = ""
    INBOUND_IDS: str = "1,5,4,6"

    # --- 3x-UI: RU-вход (персональные ключи) ---
    PANEL_RU_URL: str = ""
    PANEL_RU_API_TOKEN: str = ""
    RU_INBOUND_IDS: str = "1"

    # --- вход каскада ---
    CASCADE_HOST: str = "203.0.113.10"
    CASCADE_PORT: int = 2087
    CASCADE_SNI: str = ""
    CASCADE_PATH: str = "/ws"
    CASCADE_SECURITY: str = "none"
    CASCADE_HIDDEN_HOST: str = "ru.dostupnety.website"
    CASCADE_HIDDEN_PORT: int = 443
    CASCADE_HIDDEN_PATH: str = "/ws-hidden"

    # --- XHTTP через nginx (self-steal, с 28-10-2026) ---
    XHTTP_ENABLED: bool = True
    XHTTP_INBOUND_ID: int = 14
    XHTTP_HOST: str = "ru.dostupnety.website"
    XHTTP_PORT: int = 443
    XHTTP_PATH: str = "/assets/stream"
    XHTTP_MODE: str = "auto"
    XHTTP_SNI: str = "ru.dostupnety.website"
    XHTTP_TOTAL_BYTES: int = 300 * 1024 * 1024 * 1024

    # --- канал/подписка/донат ---
    CHANNEL_ID: str = ""
    SUB_URL: str = "https://cdn.dostupnety.website/sub/{user_id}"
    DONATE_URL: str = ""
    RESUBSCRIBE_BAN_DAYS: int = 7
    RENEW_INTERVAL_MINUTES: int = 60
    RENEW_THRESHOLD_DAYS: int = 3
    RENEWAL_ENABLED: bool = False

    # --- лимиты ---
    LIMIT_IP: int = 2
    TOTAL_GB: int = 300
    EXPIRE_DAYS: int = 30

    # --- VIP-канал (закрытый канал) ---
    VIP_CHANNEL_ID: str = ""
    VIP_INVITE_URL: str = ""
    VIP_INBOUND_ID: int = 7
    VIP_PORT: int = 2053
    VIP_PATH: str = "/ws-cf"
    VIP_SECURITY: str = "tls"
    VIP_HOST: str = "cdn.dostupnety.website"
    VIP_SNI: str = "cdn.dostupnety.website"
    VIP_SERVER: str = "203.0.113.10"
    VIP_TOTAL_GB: int = 300

    # --- Selectel ---
    SEL_ENABLED: bool = False
    SEL_PANEL_URL: str = ""
    SEL_API_TOKEN: str = ""
    SEL_INBOUND_ID: int = 12
    SEL_SERVER: str = "p.rwr-2.top"
    SEL_PORT: int = 443
    SEL_PATH: str = "/ws-hidden"
    SEL_SNI: str = "p.rwr-2.top"
    SEL_TOTAL_GB: int = 300
    SEL_ISSUE_URL: str = "https://127.0.0.1:18090"

    # --- TrustTunnel ---
    TT_ENABLED: bool = True
    TT_PANEL_URL: str = ""
    TT_API_TOKEN: str = ""
    TT_INBOUND_ID: int = 9
    TT_PANEL_BASE: str = ""
    TT_PANEL_USER: str = ""
    TT_PANEL_PASS: str = ""
    TT_VIDEO_FILE_ID: str = ""
    TT_SERVICE_LINK: str = ""
    AWG_SERVICE_LINK: str = ""


_env = _PanelEnv()

PANEL_URL: str = _env.PANEL_URL.rstrip("/")
PANEL_API_TOKEN: str = _env.PANEL_API_TOKEN
INBOUND_IDS: list[int] = [
    int(x) for x in _env.INBOUND_IDS.split(",") if x.strip().isdigit()
]

PANEL_RU_URL: str = _env.PANEL_RU_URL.rstrip("/")
PANEL_RU_API_TOKEN: str = _env.PANEL_RU_API_TOKEN
RU_INBOUND_IDS: list[int] = [
    int(x) for x in _env.RU_INBOUND_IDS.split(",") if x.strip().isdigit()
]

CASCADE_HOST: str = _env.CASCADE_HOST
CASCADE_PORT: int = _env.CASCADE_PORT
CASCADE_SNI: str = _env.CASCADE_SNI
CASCADE_PATH: str = _env.CASCADE_PATH
CASCADE_SECURITY: str = _env.CASCADE_SECURITY
CASCADE_HIDDEN_HOST: str = _env.CASCADE_HIDDEN_HOST
CASCADE_HIDDEN_PORT: int = _env.CASCADE_HIDDEN_PORT
CASCADE_HIDDEN_PATH: str = _env.CASCADE_HIDDEN_PATH

XHTTP_ENABLED: bool = _env.XHTTP_ENABLED
XHTTP_INBOUND_ID: int = _env.XHTTP_INBOUND_ID
XHTTP_HOST: str = _env.XHTTP_HOST
XHTTP_PORT: int = _env.XHTTP_PORT
XHTTP_PATH: str = _env.XHTTP_PATH
XHTTP_MODE: str = _env.XHTTP_MODE
XHTTP_SNI: str = _env.XHTTP_SNI
XHTTP_TOTAL_BYTES: int = _env.XHTTP_TOTAL_BYTES

LIMIT_IP: int = _env.LIMIT_IP
CHANNEL_ID: str = _env.CHANNEL_ID
SUB_URL: str = _env.SUB_URL
DONATE_URL: str = _env.DONATE_URL
RESUBSCRIBE_BAN_DAYS: int = _env.RESUBSCRIBE_BAN_DAYS
RENEW_INTERVAL_MINUTES: int = _env.RENEW_INTERVAL_MINUTES
RENEW_THRESHOLD_DAYS: int = _env.RENEW_THRESHOLD_DAYS
RENEWAL_ENABLED: bool = _env.RENEWAL_ENABLED
TOTAL_GB: int = _env.TOTAL_GB
EXPIRE_DAYS: int = _env.EXPIRE_DAYS
TOTAL_BYTES: int = TOTAL_GB * 1024 * 1024 * 1024
EXPIRE_MS: int = EXPIRE_DAYS * 24 * 60 * 60 * 1000

VIP_CHANNEL_ID: str = _env.VIP_CHANNEL_ID
VIP_INVITE_URL: str = _env.VIP_INVITE_URL
VIP_INBOUND_ID: int = _env.VIP_INBOUND_ID
VIP_PORT: int = _env.VIP_PORT
VIP_PATH: str = _env.VIP_PATH
VIP_SECURITY: str = _env.VIP_SECURITY
VIP_HOST: str = _env.VIP_HOST
VIP_SNI: str = _env.VIP_SNI
VIP_SERVER: str = _env.VIP_SERVER
VIP_TOTAL_BYTES: int = _env.VIP_TOTAL_GB * 1024 * 1024 * 1024

SEL_ENABLED: bool = _env.SEL_ENABLED
SEL_PANEL_URL: str = _env.SEL_PANEL_URL
SEL_API_TOKEN: str = _env.SEL_API_TOKEN
SEL_INBOUND_ID: int = _env.SEL_INBOUND_ID
SEL_SERVER: str = _env.SEL_SERVER
SEL_PORT: int = _env.SEL_PORT
SEL_PATH: str = _env.SEL_PATH
SEL_SNI: str = _env.SEL_SNI
SEL_TOTAL_BYTES: int = _env.SEL_TOTAL_GB * 1024 * 1024 * 1024
SEL_ISSUE_URL: str = _env.SEL_ISSUE_URL

TT_ENABLED: bool = _env.TT_ENABLED
TT_PANEL_URL: str = _env.TT_PANEL_URL or PANEL_URL
TT_API_TOKEN: str = _env.TT_API_TOKEN or PANEL_API_TOKEN
TT_INBOUND_ID: int = _env.TT_INBOUND_ID
TT_PANEL_BASE: str = _env.TT_PANEL_BASE
TT_PANEL_USER: str = _env.TT_PANEL_USER
TT_PANEL_PASS: str = _env.TT_PANEL_PASS
TT_VIDEO_FILE_ID: str = _env.TT_VIDEO_FILE_ID
TT_SERVICE_LINK: str = _env.TT_SERVICE_LINK
AWG_SERVICE_LINK: str = _env.AWG_SERVICE_LINK

__all__ = [name for name in dir() if name.isupper()]
