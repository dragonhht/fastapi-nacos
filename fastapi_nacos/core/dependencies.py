from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi_nacos.core import NacosClientManager

# 全局Nacos客户端实例
_nacos_client_manager: Optional[NacosClientManager] = None


async def init_nacos_registry_discovery_client(
    server_addresses: str,
    namespace: str = "public",
    username: Optional[str] = None,
    password: Optional[str] = None
) -> None:
    """
    初始化全局Nacos注册中心发现客户端
    
    Args:
        server_addresses: Nacos服务器地址，格式："ip1:port1,ip2:port2"
        namespace: Nacos命名空间ID
        username: Nacos用户名
        password: Nacos密码
    """
    global _nacos_client_manager
    _nacos_client_manager = NacosClientManager()
    await _nacos_client_manager.init_registry_discovery_service(
        server_addresses, namespace, username, password
    )

def get_nacos_client() -> NacosClientManager:
    """
    获取Nacos客户端实例（用于FastAPI依赖注入）
    
    Returns:
        NacosClientManager: Nacos客户端实例
        
    Raises:
        HTTPException: 如果Nacos客户端未初始化
    """
    if _nacos_client_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nacos客户端未初始化，请先调用init_nacos_client函数"
        )
    return _nacos_client_manager


def get_service_registry(nacos_client: NacosClientManager = Depends(get_nacos_client)):
    """
    获取服务注册管理器（用于FastAPI依赖注入）
    
    Args:
        nacos_client: Nacos客户端实例
        
    Returns:
        ServiceRegistry: 服务注册管理器
    """
    return nacos_client.registry


def get_service_discovery(nacos_client: NacosClientManager = Depends(get_nacos_client)):
    """
    获取服务发现管理器（用于FastAPI依赖注入）
    
    Args:
        nacos_client: Nacos客户端实例
        
    Returns:
        ServiceDiscovery: 服务发现管理器
    """
    return nacos_client.discovery


def get_config_manager(nacos_client: NacosClientManager = Depends(get_nacos_client)):
    """
    获取配置中心管理器（用于FastAPI依赖注入）
    
    Args:
        nacos_client: Nacos客户端实例
        
    Returns:
        ConfigManager: 配置中心管理器
    """
    return nacos_client.config