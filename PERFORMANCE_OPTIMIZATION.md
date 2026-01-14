# 性能优化文档

## 概述

本文档详细说明了对 Sear-Crawl4AI 项目进行的性能优化，这些优化显著提升了系统的并发处理能力和响应速度。

## 优化前的问题

### 1. 同步阻塞的 HTTP 请求
- **问题**：使用 Python 内置的 `http.client` 库进行同步 HTTP 请求
- **影响**：在等待 SearXNG 响应时会阻塞整个事件循环，导致无法处理其他并发请求
- **瓶颈**：这是最严重的性能瓶颈，直接限制了系统的并发能力

### 2. 全局单例爬虫实例
- **问题**：整个应用共享一个 `WebCrawler` 实例
- **影响**：多个并发请求竞争同一个浏览器资源，导致资源争抢和上下文切换开销
- **瓶颈**：并发处理能力被限制为 1

## 优化方案

### 1. I/O 异步化

#### 修改内容
- 将 [`make_searxng_request()`](src/searcrawl/crawler.py:122) 方法从同步改为异步
- 使用 `httpx` 异步 HTTP 客户端库替代 `http.client`

#### 代码变更
```python
# 优化前（同步）
@staticmethod
def make_searxng_request(...) -> dict:
    conn = http.client.HTTPConnection(SEARXNG_HOST, SEARXNG_PORT)
    # ... 同步请求代码

# 优化后（异步）
@staticmethod
async def make_searxng_request(...) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=form_data, headers=headers)
        return response.json()
```

#### 效果
- ✅ 消除了 I/O 阻塞问题
- ✅ 显著提升了应用的响应能力
- ✅ 允许在等待网络响应时处理其他请求

### 2. 爬虫连接池

#### 设计思路
借鉴数据库连接池的思想，创建一个 `WebCrawler` 实例池：
- 应用启动时预先初始化多个独立的爬虫实例
- 每个实例拥有独立的浏览器进程
- 请求到达时从池中获取空闲实例，使用完毕后归还

#### 实现细节

**配置项**（[`src/searcrawl/config.py`](src/searcrawl/config.py:32)）：
```python
CRAWLER_POOL_SIZE = int(os.getenv("CRAWLER_POOL_SIZE", "4"))
```

**池化架构**（[`src/searcrawl/main.py`](src/searcrawl/main.py:33)）：
```python
# 全局爬虫池
crawler_pool = asyncio.Queue(maxsize=CRAWLER_POOL_SIZE)

# 启动时初始化
for i in range(CRAWLER_POOL_SIZE):
    crawler = WebCrawler()
    await crawler.initialize()
    await crawler_pool.put(crawler)

# 获取爬虫实例
async def get_crawler_from_pool():
    crawler = await asyncio.wait_for(crawler_pool.get(), timeout=30.0)
    return crawler

# 归还爬虫实例
async def return_crawler_to_pool(crawler: WebCrawler):
    await crawler_pool.put(crawler)
```

**使用模式**（[`src/searcrawl/main.py`](src/searcrawl/main.py:189)）：
```python
async def crawl(request: CrawlRequest):
    crawler = await get_crawler_from_pool()
    try:
        return await crawler.crawl_urls(request.urls, request.instruction)
    finally:
        await return_crawler_to_pool(crawler)
```

#### 效果
- ✅ 并发能力从 1 提升到池的大小（默认 4）
- ✅ 真正实现了并行处理多个爬取任务
- ✅ 资源利用率显著提升

## 性能提升预期

### 并发能力
- **优化前**：1 个并发请求
- **优化后**：4 个并发请求（可配置）
- **提升倍数**：4x（基于默认配置）

### 响应时间
- **搜索请求**：消除了同步 HTTP 阻塞，响应时间显著降低
- **爬取任务**：多个请求可以并行处理，整体吞吐量提升

### 资源利用
- **CPU**：更好的并行处理能力
- **内存**：每个爬虫实例独立，内存使用量增加（可通过配置控制）
- **网络**：异步 I/O 提升了网络资源利用率

## 配置指南

### 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 爬虫池大小（默认：4）
# 建议根据服务器资源调整：
# - 2核4G: 2-4
# - 4核8G: 4-8
# - 8核16G: 8-16
CRAWLER_POOL_SIZE=4
```

### 调优建议

#### 1. 确定最佳池大小
```bash
# 测试不同的池大小
CRAWLER_POOL_SIZE=2  # 低负载场景
CRAWLER_POOL_SIZE=4  # 中等负载场景（推荐）
CRAWLER_POOL_SIZE=8  # 高负载场景
```

#### 2. 监控指标
- **CPU 使用率**：应保持在 70-80% 以下
- **内存使用**：每个爬虫实例约占用 200-500MB
- **响应时间**：监控 P95、P99 响应时间
- **错误率**：关注 503 错误（所有爬虫繁忙）

#### 3. 性能测试
```bash
# 使用 Apache Bench 进行压力测试
ab -n 100 -c 10 -p search.json -T application/json http://localhost:3000/search

# 使用 wrk 进行压力测试
wrk -t4 -c10 -d30s --latency http://localhost:3000/search
```

## 依赖更新

新增依赖项（已添加到 [`requirements.txt`](requirements.txt:9)）：
```
httpx
```

安装依赖：
```bash
pip install -r requirements.txt
```

## 部署注意事项

### Docker 部署
确保 Docker 容器有足够的资源：
```yaml
# docker-compose.yml
services:
  searcrawl:
    environment:
      - CRAWLER_POOL_SIZE=4
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G
```

### 生产环境建议
1. **启动时间**：池化后启动时间会增加（每个爬虫实例需要初始化浏览器）
2. **健康检查**：建议增加健康检查端点，确保爬虫池正常工作
3. **监控告警**：监控 503 错误率，及时调整池大小
4. **优雅关闭**：已实现优雅关闭，确保所有爬虫实例正确释放资源

## 故障排查

### 问题：频繁出现 503 错误
**原因**：爬虫池大小不足，所有实例都在忙碌
**解决**：增加 `CRAWLER_POOL_SIZE` 的值

### 问题：内存占用过高
**原因**：爬虫池大小过大
**解决**：减少 `CRAWLER_POOL_SIZE` 的值

### 问题：启动时间过长
**原因**：需要初始化多个浏览器实例
**解决**：这是正常现象，可以通过减少池大小来缩短启动时间

## 架构对比

### 优化前
```
请求 → FastAPI → 全局单例 WebCrawler → 单个浏览器实例
                    ↓
                  阻塞等待
```

### 优化后
```
请求1 → FastAPI → 爬虫池 → WebCrawler 1 → 浏览器实例 1
请求2 → FastAPI → 爬虫池 → WebCrawler 2 → 浏览器实例 2
请求3 → FastAPI → 爬虫池 → WebCrawler 3 → 浏览器实例 3
请求4 → FastAPI → 爬虫池 → WebCrawler 4 → 浏览器实例 4
请求5 → FastAPI → 爬虫池 → 等待空闲实例...
                    ↓
                  并行处理
```

## 总结

通过 I/O 异步化和爬虫池化两项优化，系统的并发处理能力和响应速度得到了显著提升：

✅ **消除了同步 I/O 阻塞**
✅ **并发能力提升 4 倍**（基于默认配置）
✅ **响应时间显著降低**
✅ **资源利用率大幅提升**
✅ **支持灵活配置和调优**

这些优化使 Sear-Crawl4AI 能够更好地应对高并发场景，为用户提供更快速、更稳定的服务。
