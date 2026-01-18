# FastAPI-Nacos SDK

一个适用于FastAPI Web应用的通用SDK，实现与Nacos服务的完整集成，包括服务注册、服务发现及配置中心管理功能。

## 功能特性

- **服务注册**：自动将FastAPI应用注册到Nacos服务注册中心，包含服务元数据管理、健康检查机制及服务心跳维持
- **服务发现**：提供便捷的API用于查询Nacos注册中心中的其他服务实例信息，支持按服务名、分组等条件筛选
- **配置中心**：实现从Nacos配置中心动态获取、监听和更新配置信息，支持配置的热加载而无需重启应用
- **FastAPI集成**：兼容FastAPI的依赖注入系统，方便在FastAPI应用中使用
- **完善的日志记录**：提供详细的日志记录，方便调试和问题排查
- **错误处理**：完善的异常处理机制，提供清晰的错误信息

## 安装

使用pip安装：

```bash
pip install fastapi-nacos
```

或者使用uv安装：

```bash
uv add fastapi-nacos
```

## 快速开始

### 1. 初始化Nacos客户端

```python
from fastapi import FastAPI
from fastapi_nacos import NacosClientManager

# 初始化FastAPI应用
app = FastAPI()

# 初始化Nacos客户端
nacos_client = NacosClientManager(
    server_addresses="localhost:8848",  # Nacos服务器地址
    namespace="",  # 命名空间ID
    username="nacos",  # 用户名（可选）
    password="nacos"  # 密码（可选）
)
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

## FastAPI依赖注入

SDK提供了FastAPI依赖注入支持，可以方便地在路由中使用：

```python
from fastapi import FastAPI, Depends
from fastapi_nacos import (
    init_nacos_client,
    get_nacos_client,
    get_service_discovery,
    get_config_manager
)

app = FastAPI()

# 初始化Nacos客户端
init_nacos_client(
    server_addresses="localhost:8848",
    namespace=""
)

# 在路由中使用Nacos客户端
@app.get("/services/{service_name}")
async def get_service(
    service_name: str,
    nacos_client=Depends(get_nacos_client)
):
    instances = nacos_client.get_service_instances(service_name=service_name)
    return {"service_name": service_name, "instances": instances}

# 直接使用服务发现管理器
@app.get("/discovery/{service_name}")
async def discovery_service(
    service_name: str,
    discovery=Depends(get_service_discovery)
):
    instances = discovery.get_service_instances(service_name=service_name)
    return {"service_name": service_name, "instances": instances}

# 直接使用配置中心管理器
@app.get("/config/{data_id}")
async def get_app_config(
    data_id: str,
    config_manager=Depends(get_config_manager)
):
    config = config_manager.get_config(
        request={"data_id": data_id, "group": "DEFAULT_GROUP"}
    )
    return {"data_id": data_id, "config": config}
```

## API参考

### NacosClientManager

SDK的主要入口类，提供服务注册、服务发现和配置中心功能。

#### 初始化

```python
def __init__(
    self,
    server_addresses: str,
    namespace: str = "",
    username: Optional[str] = None,
    password: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    **kwargs
)
```

参数：
- `server_addresses`: Nacos服务器地址，格式："ip1:port1,ip2:port2"
- `namespace`: Nacos命名空间ID
- `username`: Nacos用户名
- `password`: Nacos密码
- `access_key`: Nacos访问密钥
- `secret_key`: Nacos密钥
- `**kwargs`: 其他Nacos客户端参数

#### 服务注册

```python
def register_service(
    self,
    service_name: str,
    ip: str,
    port: int,
    group_name: str = "DEFAULT_GROUP",
    weight: float = 1.0,
    metadata: Optional[Dict[str, str]] = None,
    cluster_name: str = "DEFAULT",
    ephemeral: bool = True,
    fastapi_app: Optional[FastAPI] = None
) -> str
```

参数：
- `service_name`: 服务名称
- `ip`: 服务IP地址
- `port`: 服务端口
- `group_name`: 服务分组，默认："DEFAULT_GROUP"
- `weight`: 服务权重，默认：1.0
- `metadata`: 服务元数据，默认：{}
- `cluster_name`: 集群名称，默认："DEFAULT"
- `ephemeral`: 是否为临时实例，默认：True
- `fastapi_app`: FastAPI应用实例，用于自动注册

返回值：
- `str`: 注册的服务实例ID

#### 服务注销

```python
def deregister_service(
    self,
    service_name: str,
    group_name: str = "DEFAULT_GROUP",
    ip: Optional[str] = None,
    port: Optional[int] = None,
    cluster_name: str = "DEFAULT",
    ephemeral: bool = True
) -> bool
```

参数：
- `service_name`: 服务名称
- `group_name`: 服务分组，默认："DEFAULT_GROUP"
- `ip`: 服务IP地址
- `port`: 服务端口
- `cluster_name`: 集群名称，默认："DEFAULT"
- `ephemeral`: 是否为临时实例，默认：True

返回值：
- `bool`: 注销是否成功

#### 获取服务实例列表

```python
def get_service_instances(
    self,
    service_name: str,
    group_name: str = "DEFAULT_GROUP",
    healthy_only: bool = True,
    clusters: Optional[List[str]] = None
) -> List[ServiceInstance]
```

参数：
- `service_name`: 服务名称
- `group_name`: 服务分组，默认："DEFAULT_GROUP"
- `healthy_only`: 是否只返回健康实例，默认：True
- `clusters`: 集群列表

返回值：
- `List[ServiceInstance]`: 服务实例列表

#### 选择一个服务实例

```python
def choose_one_instance(
    self,
    service_name: str,
    group_name: str = "DEFAULT_GROUP",
    healthy_only: bool = True,
    clusters: Optional[List[str]] = None,
    strategy: str = "random"
) -> Optional[ServiceInstance]
```

参数：
- `service_name`: 服务名称
- `group_name`: 服务分组，默认："DEFAULT_GROUP"
- `healthy_only`: 是否只返回健康实例，默认：True
- `clusters`: 集群列表
- `strategy`: 负载均衡策略，可选值: random, weight_random，默认：random

返回值：
- `Optional[ServiceInstance]`: 选中的服务实例

#### 获取配置

```python
def get_config(
    self,
    data_id: str,
    group: str = "DEFAULT_GROUP",
    namespace: str = ""
) -> Optional[str]
```

参数：
- `data_id`: 配置ID
- `group`: 配置分组，默认："DEFAULT_GROUP"
- `namespace`: 命名空间ID，默认：""

返回值：
- `Optional[str]`: 配置内容

#### 设置配置

```python
def set_config(
    self,
    data_id: str,
    group: str = "DEFAULT_GROUP",
    content: str = "",
    namespace: str = ""
) -> bool
```

参数：
- `data_id`: 配置ID
- `group`: 配置分组，默认："DEFAULT_GROUP"
- `content`: 配置内容，默认：""
- `namespace`: 命名空间ID，默认：""

返回值：
- `bool`: 设置是否成功

#### 添加配置监听器

```python
def add_config_listener(
    self,
    data_id: str,
    group: str = "DEFAULT_GROUP",
    namespace: str = "",
    callback: Callable[[str], None],
    content_type: str = "text"
) -> bool
```

参数：
- `data_id`: 配置ID
- `group`: 配置分组，默认："DEFAULT_GROUP"
- `namespace`: 命名空间ID，默认：""
- `callback`: 配置变更回调函数
- `content_type`: 内容类型，默认："text"

返回值：
- `bool`: 添加是否成功

### 依赖注入函数

#### init_nacos_client

```python
def init_nacos_client(
    server_addresses: str,
    namespace: str = "",
    username: Optional[str] = None,
    password: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    **kwargs
) -> None
```

初始化全局Nacos客户端，用于依赖注入。

#### get_nacos_client

```python
def get_nacos_client() -> NacosClientManager
```

获取Nacos客户端实例（用于FastAPI依赖注入）。

#### get_service_registry

```python
def get_service_registry(nacos_client: NacosClientManager = Depends(get_nacos_client))
```

获取服务注册管理器（用于FastAPI依赖注入）。

#### get_service_discovery

```python
def get_service_discovery(nacos_client: NacosClientManager = Depends(get_nacos_client))
```

获取服务发现管理器（用于FastAPI依赖注入）。

#### get_config_manager

```python
def get_config_manager(nacos_client: NacosClientManager = Depends(get_nacos_client))
```

获取配置中心管理器（用于FastAPI依赖注入）。

## 模型类

### ServiceInstance

服务实例模型：
- `ip`: 服务IP地址
- `port`: 服务端口
- `service_name`: 服务名称
- `group_name`: 服务分组
- `weight`: 服务权重
- `healthy`: 是否健康
- `enabled`: 是否启用
- `metadata`: 元数据
- `cluster_name`: 集群名称
- `instance_id`: 实例ID

### ConfigRequest

配置请求模型：
- `data_id`: 配置ID
- `group`: 配置分组
- `namespace`: 命名空间ID

## 异常类

- `FastApiNacosException`: 基础异常类
- `NacosConnectionError`: Nacos连接错误
- `ServiceRegistrationError`: 服务注册错误
- `ServiceDiscoveryError`: 服务发现错误
- `ConfigError`: 配置中心错误
- `ConfigListenerError`: 配置监听错误
- `HeartbeatError`: 心跳发送错误

## 配置选项

可以通过环境变量配置：

- `FASTAPI_NACOS_LOG_LEVEL`: 日志级别，默认：INFO

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

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues: https://github.com/yourusername/fastapi-nacos/issues
