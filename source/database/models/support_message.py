from sqlalchemy import BigInteger
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ..tools import TableNameMixin
from .base import Base


class SupportMessageOrm(Base, TableNameMixin):
    """Обращение в поддержку. Перенесено из старой таблицы support_messages."""

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str | None] = mapped_column(String(128))
    text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", comment="ms epoch"
    )
    status: Mapped[str] = mapped_column(String(16), default="new", server_default="new")


class StatOrm(Base, TableNameMixin):
    """Счётчики (перенесено из таблицы stats: key/value)."""

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
