from sqlalchemy import BigInteger
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ..tools import TableNameMixin
from .base import Base


class PollAnswerOrm(Base, TableNameMixin):
    """Ответ на опрос в канале. Перенесено из старой таблицы poll_answers."""

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[str | None] = mapped_column(String(64), index=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    username: Mapped[str | None] = mapped_column(String(128))
    full_name: Mapped[str | None] = mapped_column(String(256))
    option_ids: Mapped[str | None] = mapped_column(
        Text, comment="JSON-массив выбранных вариантов"
    )
