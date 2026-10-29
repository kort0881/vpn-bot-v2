# Services

## BaseService inheritance
BaseService provides UoW access and logging helpers.
`source/services/base.py`:
```python
class BaseService(ABC, Generic[ModelType]):
    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow: AbstractUnitOfWork = uow
```

## Create a new service
Extend BaseService and type it with your model.
`source/services/user_service.py`:
```python
from source.database import UserOrm
from source.services.base import BaseService

class UserService(BaseService[UserOrm]):
    def __init__(self, uow: AbstractUnitOfWork) -> None:
        super().__init__(uow)
```

## Use UnitOfWork
Wrap DB changes in `async with` blocks.
`source/services/user_service.py`:
```python
async def update_user(self, user_id: int, data: dict[str, object]) -> UserOrm | None:
    async with self._uow:
        return await self._uow.users.update(user_id, data)
```

## Add to DI (Dishka)
Register providers in the AppProvider.
`source/factory/container.py`:
```python
from dishka import provide, Scope
from source.database import AbstractUnitOfWork
from source.services import UserService

@provide(scope=Scope.REQUEST)
def provide_user_service(self, uow: AbstractUnitOfWork) -> UserService:
    return UserService(uow=uow)
```
