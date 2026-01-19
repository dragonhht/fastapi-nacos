# FastAPI-Nacos SDK

一个适用于 FastAPI Web 应用的通用 SDK，实现与 Nacos v2 服务的完整集成，包括服务注册、服务发现及配置中心管理功能。

## 功能特性

- **服务注册**：自动将 FastAPI 应用注册到 Nacos 服务注册中心，包含服务元数据管理、健康检查机制及服务心跳维持
- **服务发现**：提供便捷的 API 用于查询 Nacos 注册中心中的其他服务实例信息，支持按服务名、分组等条件筛选
- **配置中心**：实现从 Nacos 配置中心动态获取、监听和更新配置信息，支持配置的热加载而无需重启应用
- **FastAPI 集成**：兼容 FastAPI 的依赖注入系统，方便在 FastAPI 应用中使用
- **完善的日志记录**：提供详细的日志记录，方便调试和问题排查
- **错误处理**：完善的异常处理机制，提供清晰的错误信息

## 安装

使用 pip 安装：

```bash
pip install fastapi-nacos
```

或者使用 uv 安装：

```bash
uv add fastapi-nacos
```

## 配置项

> nacos 的基础配置通过yaml文件进行配置，默认文件路径为 `conf/app.yml`，也可以通过环境变量 `FASTAPI_NACOS_CONFIG_FILE` 进行指定。项目中可通过`.env`文件配置项目环境变量。

- `FASTAPI_NACOS_CONFIG_FILE`：应用配置文件路径

项目yaml文件支持环境变量占位符，优先使用环境变量中的值，不存在则使用默认值，例如：

```yaml
nacos:
  discovery:
    server_addresses: ${NACOS_DISCOVERY_SERVER_ADDRESSES:localhost:8848}
    namespace: ${NACOS_DISCOVERY_NAMESPACE:public}
    username: ${NACOS_DISCOVERY_USERNAME:nacos}
    password: ${NACOS_DISCOVERY_PASSWORD:nacos}
```

项目支持的配置项目可查看 [conf/app.yml_example](conf/app.yml_example)

## 快速开始

### 1. 初始化 Nacos 客户端

```python
from fastapi import FastAPI
from fastapi_nacos import init_nacos_with_fastapi

# 初始化FastAPI应用
app = FastAPI()
# 自动初始化Nacos客户端，检测到存在对应的环境变量会自动初始化
init_nacos_with_fastapi(app)
```

### 2. 服务注册

```python
# 注册服务
nacos_client.register_service(
    service_name="fastapi-service",
    ip="127.0.0.1",
    port=8000,
    metadata={"version": "1.0.0", "env": "dev"},
    fastapi_app=app  # 可选，自动在应用启动和关闭时管理服务注册
)
```

### 3. 服务发现

```python
# 获取服务实例列表
instances = nacos_client.get_service_instances(
    service_name="other-service",
    healthy_only=True  # 只获取健康实例
)

# 选择一个服务实例（支持负载均衡）
instance = nacos_client.choose_one_instance(
    service_name="other-service",
    strategy="weight_random"  # 加权随机策略
)
```

### 4. 配置中心

```python
# 获取配置
config = nacos_client.get_config(
    data_id="fastapi-config",
    group="DEFAULT_GROUP"
)

# 获取配置并转换为字典
config_dict = nacos_client.get_config_dict(
    data_id="fastapi-config",
    group="DEFAULT_GROUP"
)

# 设置配置
nacos_client.set_config(
    data_id="fastapi-config",
    group="DEFAULT_GROUP",
    content="{\"key\": \"value\"}"
)

# 监听配置变更
def config_callback(content):
    print(f"配置变更: {content}")

nacos_client.add_config_listener(
    data_id="fastapi-config",
    group="DEFAULT_GROUP",
    callback=config_callback
)
```

## FastAPI 依赖注入

SDK 提供了 FastAPI 依赖注入支持，可以方便地在路由中使用：

## 配置选项

可以通过环境变量配置：

## 开发

### 安装依赖

```bash
uv install
```

### 运行测试

```bash
uv run pytest
```

### 构建包

```bash
uv build
```

## 许可证

Apache License 2.0

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: https://github.com/dragonhht/fastapi-nacos/issues
