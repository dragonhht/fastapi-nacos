# FastAPI-Nacos SDK

一个适用于 FastAPI Web 应用的通用 SDK，实现与 Nacos v2 服务的完整集成，包括服务注册、服务发现及配置中心管理功能。

## 功能特性

- **服务注册**：自动将 FastAPI 应用注册到 Nacos 服务注册中心，包含服务元数据管理、健康检查机制及服务心跳维持
- **服务发现**：提供便捷的 API 用于查询 Nacos 注册中心中的其他服务实例信息
- **配置中心**：实现从 Nacos 配置中心动态获取、监听和更新配置信息，支持配置的热加载而无需重启应用
- **FastAPI 集成**：兼容 FastAPI 的依赖注入系统，方便在 FastAPI 应用中使用

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

yaml文件支持变量占位符，引用yaml中其他配置项，例如：

```yaml
app:
  name: fastapi-nacos
nacos:
  config:
    data_id:
      - ${app.name}.yml
```

项目支持的配置项目可查看 [conf/app.yml_example](conf/app.yml_example)

## 快速开始

### 1. 初始化 Nacos 客户端, 自动完成服务注册、服务发现、配置中心功能

```python
from fastapi import FastAPI
from fastapi_nacos import init_nacos_with_fastapi

# 初始化FastAPI应用
app = FastAPI()
# 自动初始化Nacos客户端，检测到存在对应的配置项会自动初始化服务注册、服务发现、配置中心功能
init_nacos_with_fastapi(app)
```

### 2. 配置参数获取

- 使用**Value**：从 Nacos 配置中心获取配置项值，如以下示例，从配置中心获取 `api.name` 配置项的值

```python
from fastapi_nacos import Value

# 定义一个函数，用于获取配置项api.name的值
@Value("${api.name}")
def api_name():
  pass

# 调用
name = api_name()
print(name)
```

### 3. Feign 客户端调用

- 使用**FeignClient**：定义一个 Feign 客户端类，用于调用其他服务的 RESTful API，如以下示例，定义一个 Feign 客户端类 `TestClient`，用于调用 `fastapi-nacos` 服务的 `/hello` 接口

```python
from fastapi_nacos import FeignClient, GetMapping

# 定义一个 Feign 客户端类，用于调用其他服务的 RESTful API, base_url传入非http开头的服务名，会自动从服务注册中心获取服务实例的ip和port，否则直接使用base_url
@FeignClient(base_url="fastapi-nacos")
class TestClient:
    @GetMapping("/hello")
    async def get_hello(self, name: str) -> dict:
        pass

# 调用
test_client = TestClient()
response = await test_client.get_hello(name=name)
```

## 开发

### 安装依赖

```bash
uv install
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
