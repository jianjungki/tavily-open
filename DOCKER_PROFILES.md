# Docker Compose Profiles 使用指南

本项目使用 Docker Compose profiles 功能来管理可选服务，让你可以根据需要选择启动哪些服务。

## 可用的 Profiles

### 默认（无 profile）
启动核心服务：
- **Redis**: 缓存服务
- **App**: 主应用

### `searxng` Profile
启动核心服务 + SearXNG 元搜索引擎：
- **Redis**: 缓存服务
- **App**: 主应用
- **SearXNG**: 元搜索引擎

### `full` Profile
启动所有服务（包括所有可选服务）：
- **Redis**: 缓存服务
- **App**: 主应用
- **SearXNG**: 元搜索引擎

## 使用方法

### 1. 启动基础服务（默认）

```bash
# 仅启动 Redis 和 App
docker-compose up -d
```

### 2. 启动包含 SearXNG 的服务

```bash
# 使用 searxng profile
docker-compose --profile searxng up -d

# 或使用 full profile
docker-compose --profile full up -d
```

### 3. 查看服务状态

```bash
# 查看所有运行中的服务
docker-compose ps

# 查看包含 profile 服务的状态
docker-compose --profile searxng ps
```

### 4. 停止服务

```bash
# 停止默认服务
docker-compose down

# 停止包含 profile 的服务
docker-compose --profile searxng down

# 停止所有服务（包括所有 profiles）
docker-compose --profile full down
```

### 5. 查看日志

```bash
# 查看默认服务日志
docker-compose logs -f

# 查看包含 SearXNG 的日志
docker-compose --profile searxng logs -f

# 查看特定服务日志
docker-compose --profile searxng logs -f searxng
```

### 6. 重启服务

```bash
# 重启默认服务
docker-compose restart

# 重启包含 SearXNG 的服务
docker-compose --profile searxng restart

# 重启特定服务
docker-compose --profile searxng restart searxng
```

## 环境变量配置

### 使用 SearXNG 时

编辑 `.env` 文件：

```env
# SearXNG 配置
SEARXNG_SECRET=your_secret_key_here
SEARXNG_URL=http://searxng:8080
```

### 不使用 SearXNG 时

如果不启动 SearXNG，可以配置外部 SearXNG 实例：

```env
# 使用外部 SearXNG 实例
SEARXNG_URL=https://your-external-searxng.com
```

或者留空/注释掉：

```env
# SEARXNG_URL=
```

## 常见场景

### 场景 1: 开发环境（仅基础服务）

```bash
# 快速启动，不需要 SearXNG
docker-compose up -d

# 访问应用
curl http://localhost:8000
```

### 场景 2: 完整功能测试（包含 SearXNG）

```bash
# 启动所有服务
docker-compose --profile full up -d

# 测试 SearXNG
curl http://localhost:8080/healthz

# 测试应用
curl http://localhost:8000
```

### 场景 3: 生产环境（选择性启动）

```bash
# 根据需要选择 profile
docker-compose --profile searxng up -d

# 或使用环境变量
export COMPOSE_PROFILES=searxng
docker-compose up -d
```

## 使用环境变量设置 Profile

你也可以通过环境变量来设置默认 profile：

```bash
# 设置环境变量
export COMPOSE_PROFILES=searxng

# 现在 docker-compose 命令会自动使用该 profile
docker-compose up -d
docker-compose ps
docker-compose down
```

或在 `.env` 文件中设置：

```env
COMPOSE_PROFILES=searxng
```

## 多个 Profiles

可以同时使用多个 profiles：

```bash
# 启动多个 profiles（如果将来添加更多可选服务）
docker-compose --profile searxng --profile other-service up -d
```

## 检查配置

查看当前配置（包括 profiles）：

```bash
# 查看默认配置
docker-compose config

# 查看包含 profile 的配置
docker-compose --profile searxng config

# 查看所有 profiles 的配置
docker-compose --profile full config
```

## 故障排除

### Profile 服务未启动

如果忘记指定 profile，可选服务不会启动：

```bash
# 错误：SearXNG 不会启动
docker-compose up -d

# 正确：SearXNG 会启动
docker-compose --profile searxng up -d
```

### 查看哪些服务属于哪个 Profile

查看 `docker-compose.yml` 中的 `profiles` 字段：

```yaml
services:
  searxng:
    profiles:
      - searxng
      - full
```

### 停止 Profile 服务

确保使用相同的 profile 参数来停止服务：

```bash
# 启动时使用的 profile
docker-compose --profile searxng up -d

# 停止时也要使用相同的 profile
docker-compose --profile searxng down
```

## 最佳实践

1. **开发环境**: 使用默认配置（无 profile），快速启动
2. **测试环境**: 使用 `--profile full`，测试所有功能
3. **生产环境**: 根据实际需求选择合适的 profile
4. **CI/CD**: 在脚本中明确指定 profile，避免歧义

## 参考

- [Docker Compose Profiles 官方文档](https://docs.docker.com/compose/profiles/)
- [项目 docker-compose.yml](docker-compose.yml)
- [SearXNG 集成说明](searxng/settings.yml)
