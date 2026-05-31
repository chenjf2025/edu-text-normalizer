"""缓存服务"""
import hashlib
from typing import Optional, Any
import json
import time
from app.utils.logger import logger

# 简单的内存缓存实现（可替换为Redis）
class CacheService:
    """缓存服务 - 内存实现，可扩展为Redis"""

    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        """
        初始化缓存服务

        Args:
            max_size: 最大缓存条目数
            ttl: 过期时间(秒)
        """
        self._cache = {}
        self._expiry = {}
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None

        # 检查过期
        if time.time() > self._expiry.get(key, 0):
            self.delete(key)
            return None

        logger.debug(f"缓存命中: {key[:50]}...")
        return self._cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        # 清理过期缓存
        self._cleanup()

        # 检查大小限制
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        self._cache[key] = value
        self._expiry[key] = time.time() + (ttl or self.ttl)
        logger.debug(f"缓存设置: {key[:50]}...")

    def delete(self, key: str) -> None:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._expiry.clear()

    def _cleanup(self) -> None:
        """清理过期缓存"""
        now = time.time()
        expired_keys = [k for k, exp in self._expiry.items() if now > exp]
        for key in expired_keys:
            self.delete(key)

    def _evict_oldest(self) -> None:
        """驱逐最老的缓存"""
        if not self._expiry:
            return
        oldest_key = min(self._expiry.items(), key=lambda x: x[1])[0]
        self.delete(oldest_key)

    @staticmethod
    def make_key(text: str, subject: Optional[str] = None) -> str:
        """生成缓存key"""
        content = f"{subject or 'auto'}:{text}"
        return hashlib.md5(content.encode()).hexdigest()


class RedisCacheService:
    """Redis缓存服务(需要Redis服务器)"""

    def __init__(self, host: str = "localhost", port: int = 6379,
                 db: int = 0, password: Optional[str] = None,
                 ttl: int = 3600):
        """
        初始化Redis缓存

        Args:
            host: Redis主机
            port: Redis端口
            db: 数据库编号
            password: 密码
            ttl: 过期时间(秒)
        """
        self.ttl = ttl
        self._client = None
        self._connect(host, port, db, password)

    def _connect(self, host: str, port: int, db: int, password: Optional[str]) -> None:
        """连接Redis"""
        try:
            import redis
            self._client = redis.Redis(
                host=host, port=port, db=db, password=password,
                decode_responses=True, socket_connect_timeout=2
            )
            # 测试连接
            self._client.ping()
            logger.info("Redis连接成功")
        except ImportError:
            logger.warning("redis库未安装，使用内存缓存")
            self._client = None
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}，使用内存缓存")
            self._client = None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._client:
            return None
        try:
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        if not self._client:
            return
        try:
            data = json.dumps(value)
            self._client.setex(key, ttl or self.ttl, data)
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")

    def delete(self, key: str) -> None:
        """删除缓存"""
        if not self._client:
            return
        try:
            self._client.delete(key)
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")

    def clear(self) -> None:
        """清空缓存"""
        if not self._client:
            return
        try:
            self._client.flushdb()
        except Exception as e:
            logger.error(f"Redis清空失败: {e}")


# 全局缓存实例
_cache_service = None

def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

def set_cache_service(service: CacheService) -> None:
    """设置缓存服务"""
    global _cache_service
    _cache_service = service