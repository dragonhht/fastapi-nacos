# 导出主要类和功能
from .core import NacosClientManager
from .core.dependencies import (
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

__version__ = "0.1.0"
__all__ = [
    # 核心类
    "NacosClientManager",
    
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
    "HeartbeatError"
]