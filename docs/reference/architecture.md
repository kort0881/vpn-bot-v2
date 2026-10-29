# Architecture

## Layers (text diagram)
Update -> Middlewares -> Handlers -> Services -> UnitOfWork -> Repositories -> Database

## Patterns
Repository keeps queries near models.
```python
class UserRepository(AbstractRepository[UserOrm, int]):
    model = UserOrm
```
Unit of Work scopes one transaction per request.
```python
async with self._uow:
    user = await self._uow.users.get(user_id)
```
Dependency Injection wires services and utilities.
```python
@aiogram_inject
async def start(message: Message, user_service: FromDishka[UserService]) -> None:
    await user_service.register_user(message.from_user.id)
```

## Data flow
`update -> router -> handler -> service -> uow -> repository -> db -> handler -> response`

## Directory structure rationale
- `source/telegram/` holds edge-layer input/output (handlers, filters, keyboards).
- `source/services/` keeps business logic and orchestration.
- `source/database/` contains models, repositories, and UoW.
- `source/factory/` wires bot, dispatcher, app, and DI container.
