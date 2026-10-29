# Database

## Create model
Define ORM models under `source/database/models/`.
`source/database/models/user.py`:
```python
from sqlalchemy import BigInteger
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..tools import TableNameMixin
from .base import Base

class UserOrm(Base, TableNameMixin):
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    language_code: Mapped[str | None] = mapped_column(String(2), default="en")
```

## Create repository
Repositories wrap queries and sit in `source/database/repositories/`.
`source/database/repositories/user.py`:
```python
from source.database.models import UserOrm
from source.database.repositories.base import AbstractRepository

class UserRepository(AbstractRepository[UserOrm, int]):
    model = UserOrm
```

## Add to UnitOfWork
Expose repositories from the UoW for transactional use.
`source/database/tools/uow.py`:
```python
from source.database.repositories import UserRepository

async def __aenter__(self) -> Self:
    self._session = self._session_factory()
    self._transaction = await self._session.begin()
    self.users = UserRepository(self._session)
    return self
```

## Use in service
Services orchestrate business logic with the UoW.
`source/services/user_service.py`:
```python
async def add_user(self, data: dict[str, object]) -> UserOrm:
    async with self._uow:
        return await self._uow.users.add(data)
```

## Migrations
Generate and apply schema changes with Alembic.
```bash
uv run alembic revision --autogenerate -m "add users"
uv run alembic upgrade head
```
