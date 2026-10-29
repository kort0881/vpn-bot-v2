# API Reference

## UserService
Use the service in handlers or other services via DI.
```python
user = await user_service.register_user(message.from_user.id)
user = await user_service.get_user(message.from_user.id)
await user_service.update_user(message.from_user.id, {"language_code": "en"})
```

## CacheService
Cache small user-specific values like language.
```python
lang = await cache_service.get_user_language(user_id)
await cache_service.set_user_language(user_id, "en", ttl=3600)
await cache_service.invalidate_user_language(user_id)
```

## UserRepository
Use from the UoW for direct data access.
```python
user = await uow.users.get_by_filters(user_id=user_id)
users = await uow.users.list_by_filters(language_code="en")
```
