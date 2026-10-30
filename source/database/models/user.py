from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from source.enums import UserRole

from ..tools import TableNameMixin
from .base import Base


class UserOrm(Base, TableNameMixin):
    id: Mapped[int] = mapped_column(primary_key=True, comment="PK записи")
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        unique=True,
        comment="Внешний ID пользователя (Telegram ID)",
    )
    username: Mapped[str] = mapped_column(
        String(64),
        default="",
        server_default="",
        comment="Telegram username без @",
    )
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole),
        default=UserRole.user,
        server_default="user",
        nullable=False,
        comment="Роль пользователя в системе",
    )
    language_code: Mapped[str | None] = mapped_column(
        String(2),
        default="ru",
        server_default="ru",
        comment="Язык ('ru', 'en' и т.д.)",
    )

    # ---------------------------------------------------------------- VPN-поля
    email: Mapped[str | None] = mapped_column(
        String(64),
        index=True,
        comment="Email клиента в панели (tg_<telegram_id>)",
    )
    client_uuid: Mapped[str | None] = mapped_column(
        String(64),
        comment="UUID клиента в 3x-ui",
    )
    vless_link: Mapped[str | None] = mapped_column(
        Text,
        comment="Основная ссылка подключения",
    )
    links: Mapped[list | None] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        comment="Все ссылки по каналам",
    )
    total_bytes: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", comment="Лимит трафика, байт"
    )
    used_bytes: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", comment="Израсходовано, байт"
    )
    expiry_at: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default="0",
        comment="Окончание подписки, ms epoch",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", comment="Подписка активна"
    )
    banned: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", comment="Забанен"
    )
    unsubscribed_at: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default="0",
        comment="Когда отключился от канала, ms epoch",
    )
    channel_step: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="Шаг выдачи ключа"
    )
    chosen_channel: Mapped[int] = mapped_column(
        Integer,
        default=-1,
        server_default="-1",
        comment="Подтверждённый канал (-1 = нет)",
    )
    ban_reason: Mapped[str] = mapped_column(
        Text, default="", server_default="", comment="Причина бана"
    )
    ban_at: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", comment="Когда забанен, ms epoch"
    )
    balance: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="Баланс, копейки"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        comment="Когда зарегистрировался",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Когда профиль в последний раз обновлялся",
    )
