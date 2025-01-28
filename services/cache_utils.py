# services/cache_utils.py
from aiocache import Cache
from aiocache.serializers import JsonSerializer

class CacheManager:
    def __init__(self, cache_type=Cache.MEMORY, **kwargs):
        self.cache = Cache(cache_type, serializer=JsonSerializer(), **kwargs)

    async def get(self, key):
        """
        Получить данные из кеша по ключу.
        """
        return await self.cache.get(key)

    async def add(self, key, value, ttl=None):
        """
        Добавить данные в кеш. Если ключ уже существует, не делать ничего.
        ttl - время жизни в секундах.
        """
        return await self.cache.add(key, value, ttl=ttl)

    async def set(self, key, value, ttl=None):
        """
        Обновить данные в кеше по ключу. Если ключа нет, он будет создан.
        ttl - время жизни в секундах.
        """
        return await self.cache.set(key, value, ttl=ttl)

    async def delete(self, key):
        """
        Удалить данные из кеша по ключу.
        """
        return await self.cache.delete(key)
    
    # ----------------------------------------------------------------------------------------- #
    
    async def get_user_data(self, user_id):
        """
        Get user-specific data from the cache.
        """
        return await self.get(f'user_data_{user_id}')


    async def set_user_data(self, user_id, user_data, ttl=None):
        """
        Set user-specific data in the cache.
        """
        return await self.set(f'user_data_{user_id}', user_data, ttl=ttl)

    
    async def update_user_page(self, user_id, page):
        """
        Update the user's current page number in the cache.
        """
        user_data = await self.get_user_data(user_id) or {}
        user_data['page'] = page
        await self.set_user_data(user_id, user_data)

    
    async def add_user_bookmark(self, user_id, page):
        """
        Add a bookmark for the user in the cache.
        """
        user_data = await self.get_user_data(user_id) or {'bookmarks': []}
        bookmarks = set(user_data.get('bookmarks', []))
        bookmarks.add(page)
        user_data['bookmarks'] = list(bookmarks)  # Convert set to list to be JSON serializable
        await self.set_user_data(user_id, user_data)


    async def remove_user_bookmark(self, user_id, page):
        user_data = await self.get_user_data(user_id)
        if user_data:
            bookmarks = set(user_data.get('bookmarks', []))
            if str(page) in bookmarks:  # Убедитесь, что page преобразован в строку
                print(f"Before removal: {bookmarks}")  # Логирование до удаления
                bookmarks.remove(str(page))
                print(f"After removal: {bookmarks}")  # Логирование после удаления
                user_data['bookmarks'] = list(bookmarks)
                await self.set_user_data(user_id, user_data)

