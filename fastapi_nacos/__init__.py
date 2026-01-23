# 导出主要类和功能
from fastapi_nacos.core import (
    NacosClientManager,
    nacos_lifespan,
    init_nacos_with_fastapi,
)
from fastapi_nacos.core.dependencies import (
    init_nacos_registry_discovery_client,
    get_nacos_client,
    get_service_registry,
    get_service_discovery,
    get_config_manager
)
from fastapi_nacos.models.service import ServiceInstance, ServiceRegisterRequest, ServiceInfo
from fastapi_nacos.models.config import ConfigRequest, ConfigResponse, ConfigListener
from fastapi_nacos.utils.exceptions import (
    FastApiNacosException,
    NacosConnectionError,
    ServiceRegistrationError,
    ServiceDiscoveryError,
    ConfigError,
    ConfigListenerError,
    HeartbeatError
)
from fastapi_nacos.http.http_client import (
  FeignClient,
  GetMapping,
  PostMapping,
  PutMapping,
  DeleteMapping
)

from fastapi_nacos.core.value import Value

__version__ = "0.1.0"
__all__ = [
    # 核心类
    "NacosClientManager",
    "nacos_lifespan",
    "init_nacos_with_fastapi",
    
    # 依赖注入函数
    "init_nacos_registry_discovery_client",
    "get_nacos_client",
    "get_service_registry",
    "get_service_discovery",
    "get_config_manager",
    
    # 服务模型
    "ServiceInstance",
    "ServiceRegisterRequest",
    "ServiceInfo",
    
    # 配置模型
    "ConfigRequest",
    "ConfigResponse",
    "ConfigListener",
    
    # 异常类
    "FastApiNacosException",
    "NacosConnectionError",
    "ServiceRegistrationError",
    "ServiceDiscoveryError",
    "ConfigError",
    "ConfigListenerError",
    "HeartbeatError",
    
    # HTTP客户端
    "FeignClient",
    "GetMapping",
    "PostMapping",
    "PutMapping",
    "DeleteMapping",
    
    # 配置值装饰器
    "Value"
]