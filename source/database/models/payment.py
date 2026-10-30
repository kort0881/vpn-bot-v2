from sqlalchemy import BigInteger
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ..tools import TableNameMixin
from .base import Base


class PaymentOrm(Base, TableNameMixin):
    """Платёж (СБП и прочие способы). Перенесено из старой таблицы payments."""

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    username: Mapped[str] = mapped_column(String(64), default="", server_default="")
    full_name: Mapped[str] = mapped_column(String(128), default="", server_default="")
    amount: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="Сумма, руб."
    )
    method: Mapped[str] = mapped_column(String(32), default="sbp", server_default="sbp")
    status: Mapped[str] = mapped_column(
        String(16),
        default="claimed",
        server_default="claimed",
        comment="claimed/confirmed/rejected",
    )
    created_at: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", comment="ms epoch"
    )
    confirmed_at: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", comment="ms epoch"
    )
