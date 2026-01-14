# 缓存实现指南

## 概述

本项目已集成分布式缓存系统，使用 Redis 作为后端存储，支持多个实例共享缓存。缓存系统可以显著减少重复爬取，提高系统性能。

## 架构设计

### 缓存管理器 (CacheManager)

位置: [`src/searcrawl/cache.py`](src/searcrawl/cache.py)

缓存管理器提供以下核心功能：

- **单个 URL 缓存**: 支持缓存单个 URL 的爬取结果
- **批量缓存操作**: 支持批量获取和存储缓存
- **缓存过期管理**: 支持可配置的 TTL (Time-To-Live)
- **缓存统计**: 提供缓存使用情况统计
- **缓存清理**: 支持清理单个或全部缓存

### 缓存键生成

缓存键通过 MD5 哈希生成，基于 URL 和搜索指令的组合：

```python
cache_key = f"crawl_cache:{md5(url:instruction).hexdigest()}"
```

这确保了相同的 URL 和指令组合会使用相同的缓存键。

## 配置说明

### 环境变量

在 `.env` 文件中配置以下变量：

```bash
# 缓存启用开关 (true/false)
CACHE_ENABLED=true

# Redis 连接 URL
REDIS_URL=redis://localhost:6379/0

# 缓存过期时间 (小时)
CACHE_TTL_HOURS=24
```

### Docker Compose 配置

项目已更新 `docker-compose.yml`，包含 Redis 服务：

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: searcrawl_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  app:
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379/0
```

## 使用方式

### 启动服务

使用 Docker Compose 启动完整的服务栈：

```bash
docker-compose up -d
```

这将启动：
1. Redis 服务 (端口 6379)
2. SearXNG 搜索引擎 (如已配置)
3. Sear-Crawl4AI 应用 (端口 3000)

### API 响应

缓存命中时，API 响应会包含额外的缓存统计信息：

```json
{
  "results": [...],
  "success_count": 10,
  "failed_urls": [],
  "cache_hits": 5,
  "newly_crawled": 5
}
```

字段说明：
- `cache_hits`: 从缓存中获取的结果数
- `newly_crawled`: 新爬取的结果数

### 缓存管理

#### 获取缓存统计

```python
from searcrawl.cache import CacheManager

cache_manager = CacheManager("redis://localhost:6379/0")
stats = cache_manager.get_cache_stats()
print(stats)
# 输出: {
#   "status": "available",
#   "total_entries": 100,
#   "memory_used": "1.5M",
#   "redis_version": "7.0.0"
# }
```

#### 清理缓存

```python
# 清理单个 URL 的缓存
cache_manager.clear_url("https://example.com", instruction="search query")

# 清理所有缓存
cache_manager.clear_all()
```

#### 检查缓存可用性

```python
if cache_manager.is_available():
    print("缓存系统可用")
else:
    print("缓存系统不可用，将继续运行但不使用缓存")
```

## 多实例共享

### 场景

当部署多个 Sear-Crawl4AI 实例时，所有实例可以共享同一个 Redis 缓存：

```
┌─────────────────┐
│  Instance 1     │
│  (Port 3000)    │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
    ┌────▼─────────────────▼────┐
    │   Shared Redis Cache      │
    │   (Port 6379)             │
    └────▲─────────────────▲────┘
         │                 │
┌────────┴────────┐ ┌──────┴──────────┐
│  Instance 2     │ │  Instance 3     │
│  (Port 3001)    │ │  (Port 3002)    │
└─────────────────┘ └─────────────────┘
```

### 配置多实例

使用 Docker Compose 扩展服务：

```yaml
services:
  app1:
    build: .
    container_name: searcrawl_app1
    ports:
      - "3000:3000"
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379/0

  app2:
    build: .
    container_name: searcrawl_app2
    ports:
      - "3001:3000"
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379/0
```

启动多实例：

```bash
docker-compose up -d app1 app2
```

## 性能优化

### 缓存命中率

缓存命中率取决于：

1. **搜索查询的重复性**: 相同的搜索查询会使用相同的缓存
2. **URL 的稳定性**: 相同的 URL 会使用相同的缓存
3. **缓存 TTL**: 更长的 TTL 意味着更高的命中率，但可能返回过时数据

### 建议配置

- **高频搜索场景**: `CACHE_TTL_HOURS=72` (3 天)
- **实时数据场景**: `CACHE_TTL_HOURS=1` (1 小时)
- **混合场景**: `CACHE_TTL_HOURS=24` (1 天，默认)

### 监控缓存

定期检查缓存统计信息：

```bash
# 连接到 Redis
redis-cli -h localhost -p 6379

# 查看所有缓存键
KEYS crawl_cache:*

# 查看缓存键数量
DBSIZE

# 查看内存使用
INFO memory
```

## 故障排除

### 缓存不可用

如果 Redis 连接失败，系统会自动降级到无缓存模式：

```
[WARNING] Cache manager initialized but Redis is not available
[INFO] Continuing without cache
```

此时系统仍然可以正常工作，但不会使用缓存。

### 检查 Redis 连接

```bash
# 测试 Redis 连接
redis-cli -h localhost -p 6379 ping
# 输出: PONG

# 查看 Redis 日志
docker logs searcrawl_redis
```

### 清理过期缓存

Redis 会自动清理过期的缓存项。如需手动清理：

```bash
# 清理所有缓存
redis-cli -h localhost -p 6379 FLUSHDB

# 清理特定模式的缓存
redis-cli -h localhost -p 6379 EVAL "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" 0 "crawl_cache:*"
```

## 最佳实践

1. **定期监控**: 定期检查缓存统计信息和 Redis 内存使用
2. **合理设置 TTL**: 根据数据更新频率设置合适的 TTL
3. **备份 Redis 数据**: 在生产环境中启用 Redis 持久化
4. **负载均衡**: 使用负载均衡器分发请求到多个实例
5. **缓存预热**: 在系统启动时预加载常用的搜索结果

## 相关文件

- 缓存模块: [`src/searcrawl/cache.py`](src/searcrawl/cache.py)
- 爬虫集成: [`src/searcrawl/crawler.py`](src/searcrawl/crawler.py)
- 主应用: [`src/searcrawl/main.py`](src/searcrawl/main.py)
- 配置文件: [`src/searcrawl/config.py`](src/searcrawl/config.py)
- Docker 配置: [`docker-compose.yml`](docker-compose.yml)
- 环境变量示例: [`.env.example`](.env.example)
