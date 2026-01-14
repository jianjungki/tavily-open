# 缓存功能使用指南

## 概述

Sear-Crawl4AI 现已集成分布式缓存功能，使用 Redis 作为后端存储。该缓存系统支持多个实例共享缓存数据，可以显著减少重复爬取，提高系统性能。

## 功能特性

- **分布式缓存**：多个应用实例可以共享同一个 Redis 缓存
- **自动缓存检查**：爬取前自动检查缓存，命中则直接返回
- **智能缓存存储**：成功爬取的内容自动存入缓存
- **可配置 TTL**：支持自定义缓存过期时间
- **缓存管理 API**：提供缓存统计和清除接口
- **优雅降级**：Redis 不可用时自动降级为无缓存模式

## 配置说明

### 环境变量

在 `.env` 文件中配置以下参数：

```env
# 缓存启用开关 (true/false)
CACHE_ENABLED=true

# Redis 连接 URL
REDIS_URL=redis://localhost:6379/0

# 缓存过期时间（小时）
CACHE_TTL_HOURS=24
```

### Docker Compose 部署

使用 `docker-compose.yml` 可以自动启动 Redis 服务：

```bash
docker-compose up -d
```

该配置包括：
- Redis 7 Alpine 镜像
- 自动持久化配置
- 健康检查
- 数据卷持久化

## 使用方式

### 1. 启用缓存

确保 `.env` 文件中设置：
```env
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

### 2. 搜索和爬取

使用 `/search` 端点进行搜索和爬取：

```bash
curl -X POST http://localhost:3000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python 教程",
    "limit": 10
  }'
```

响应示例：
```json
{
  "results": [...],
  "success_count": 8,
  "failed_urls": [],
  "cache_hits": 3,
  "newly_crawled": 5
}
```

- `cache_hits`：从缓存中获取的结果数
- `newly_crawled`：新爬取的结果数

### 3. 查看缓存统计

```bash
curl http://localhost:3000/cache/stats
```

响应示例：
```json
{
  "status": "available",
  "total_entries": 150,
  "memory_used": "2.5M",
  "redis_version": "7.0.0"
}
```

### 4. 清除缓存

```bash
curl -X POST http://localhost:3000/cache/clear
```

响应示例：
```json
{
  "status": "success",
  "message": "Cache cleared successfully"
}
```

## 缓存键生成

缓存键由 URL 和 instruction（搜索查询）的 MD5 哈希生成：

```
cache_key = "crawl_cache:" + MD5(url + ":" + instruction)
```

这确保了相同的 URL 和查询条件会使用相同的缓存。

## 性能优化

### 缓存命中率

- 首次搜索：缓存命中率为 0%
- 重复搜索：缓存命中率可达 100%
- 相同 URL 不同查询：缓存命中率为 0%

### 内存管理

- 默认 TTL：24 小时
- 自动过期：超过 TTL 的缓存自动删除
- 持久化：Redis 配置了 AOF 持久化

### 多实例共享

在 Docker Compose 中运行多个应用实例：

```yaml
services:
  app1:
    build: .
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379/0
  
  app2:
    build: .
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379/0
```

所有实例共享同一个 Redis 缓存。

## 故障排除

### Redis 连接失败

如果看到日志：
```
Failed to initialize cache manager: Connection refused
```

检查：
1. Redis 服务是否运行：`docker ps | grep redis`
2. Redis URL 是否正确
3. 网络连接是否正常

### 缓存未生效

检查：
1. `CACHE_ENABLED` 是否设置为 `true`
2. Redis 是否可用：`redis-cli ping`
3. 查看日志中的缓存相关信息

### 内存占用过高

解决方案：
1. 减少 `CACHE_TTL_HOURS`
2. 定期调用 `/cache/clear` 清除缓存
3. 增加 Redis 内存限制

## 日志示例

启用缓存时的日志输出：

```
INFO: Initializing cache manager with Redis: redis://localhost:6379/0
INFO: Cache manager initialized successfully
INFO: Cache stats: {'status': 'available', 'total_entries': 0, 'memory_used': '1.0M', 'redis_version': '7.0.0'}
INFO: Checking cache for 10 URLs
INFO: Cache hit for URL: https://example.com/page1
INFO: Cache miss for URL: https://example.com/page2
INFO: Cached 5 newly crawled results
INFO: Crawl completed, total: 10, cache hits: 5, newly crawled: 5, failed: 0
```

## 最佳实践

1. **定期监控缓存**：使用 `/cache/stats` 监控缓存状态
2. **合理设置 TTL**：根据内容更新频率调整过期时间
3. **定期清理**：对于快速变化的内容，定期清除缓存
4. **备份数据**：Redis 配置了持久化，但建议定期备份
5. **监控内存**：确保 Redis 内存不会溢出

## 禁用缓存

如需禁用缓存，设置：
```env
CACHE_ENABLED=false
```

此时系统将正常运行，但不会使用缓存。

## 相关文件

- [`src/searcrawl/cache.py`](src/searcrawl/cache.py) - 缓存管理器实现
- [`src/searcrawl/config.py`](src/searcrawl/config.py) - 缓存配置
- [`src/searcrawl/crawler.py`](src/searcrawl/crawler.py) - 爬虫集成缓存
- [`src/searcrawl/main.py`](src/searcrawl/main.py) - API 端点
- [`docker-compose.yml`](docker-compose.yml) - Docker 配置
