from typing import Dict, Optional, List, Callable
from v2.nacos import ClientConfigBuilder, NacosNamingService, NacosConfigService
from fastapi import FastAPI
from fastapi_nacos.core.registration import ServiceRegistry
from fastapi_nacos.core.discovery import ServiceDiscovery
from fastapi_nacos.core.config import ConfigManager
from fastapi_nacos.models.service import ServiceInstance, ServiceRegisterRequest
from fastapi_nacos.models.config import ConfigRequest, ConfigListener
from fastapi_nacos.utils.log_utils import log, log_dir, log_level
from fastapi_nacos.utils.exceptions import NacosConnectionError

class NacosClientManager:
    """Nacos客户端管理器，SDK的主要入口点"""
    
    # 单例实例
    _instance: Optional['NacosClientManager'] = None
    
    def __init__(self):
        """
        初始化Nacos客户端管理器
        """
        # 更新单例实例
        NacosClientManager._instance = self

    async def init_registry_discovery_service(
        self,
        server_addresses: str,
        namespace: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        初始化注册中心基础服务
        
        Args:
            server_addresses: Nacos服务器地址
            namespace: Nacos命名空间ID
            username: Nacos用户名
            password: Nacos密码
        """
        try:
            client_config = (ClientConfigBuilder()
                              .server_address(server_addresses)
                              .namespace_id(namespace)
                              .username(username)
                              .password(password)
                              .log_level(log_level)
                              .log_dir(log_dir)
                              .build()
                            )
            self.naming_service = await NacosNamingService.create_naming_service(client_config)
            self._registry = ServiceRegistry(self.naming_service, log, server_addresses, namespace, username, password)
            self._discovery = ServiceDiscovery(self.naming_service, log, server_addresses, namespace, username, password)
        except Exception as e:
            log.error(f"初始化注册中心基础服务失败: {str(e)}")
            raise NacosConnectionError(f"初始化注册中心基础服务失败: {str(e)}") from e

    @property
    def registry(self) -> ServiceRegistry:
        """获取服务注册管理器实例"""
        return self._registry

    @property
    def discovery(self) -> ServiceDiscovery:
        """获取服务发现管理器实例"""
        return self._discovery

    async def init_config_service(
        self,
        server_addresses: str,
        namespace: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        初始化配置中心基础服务
        
        Args:
            server_addresses: Nacos服务器地址
            namespace: Nacos命名空间ID
            username: Nacos用户名
            password: Nacos密码
        """
        # 初始化配置中心基础服务
        try:
            client_config = (ClientConfigBuilder()
                              .server_address(server_addresses)
                              .namespace_id(namespace)
                              .username(username)
                              .password(password)
                              .build()
                            )
            self.config_service = await NacosConfigService.create_config_service(client_config)
            self.config = ConfigManager(self.config_service, log)
        except Exception as e:
            log.error(f"初始化配置中心基础服务失败: {str(e)}")
            raise NacosConnectionError(f"初始化配置中心基础服务失败: {str(e)}") from e
    
    async def register_service(
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
    ) -> str:
        """
        注册服务到Nacos
        
        Args:
            service_name: 服务名称
            ip: 服务IP地址
            port: 服务端口
            group_name: 服务分组
            weight: 服务权重
            metadata: 服务元数据
            cluster_name: 集群名称
            ephemeral: 是否为临时实例
            fastapi_app: FastAPI应用实例（用于自动注册）
            
        Returns:
            str: 注册的服务实例ID
        """
        request = ServiceRegisterRequest(
            service_name=service_name,
            group_name=group_name,
            ip=ip,
            port=port,
            weight=weight,
            metadata=metadata or {},
            cluster_name=cluster_name,
            ephemeral=ephemeral
        )
        
        instance_id = await self.registry.register_service(request)
        
        # 如果提供了FastAPI应用，则自动在应用启动和关闭时管理服务注册
        if fastapi_app:
            self._setup_fastapi_hooks(fastapi_app, service_name, group_name, ip, port, cluster_name, ephemeral)
        
        return instance_id
    
    async def deregister_service(
        self,
        service_name: str,
        group_name: str = "DEFAULT_GROUP",
        ip: Optional[str] = None,
        port: Optional[int] = None,
        cluster_name: str = "DEFAULT",
        ephemeral: bool = True
    ) -> bool:
        """
        从Nacos注销服务
        
        Args:
            service_name: 服务名称
            group_name: 服务分组
            ip: 服务IP地址（如果未提供，将使用注册时的IP）
            port: 服务端口（如果未提供，将使用注册时的端口）
            cluster_name: 集群名称
            ephemeral: 是否为临时实例
            
        Returns:
            bool: 注销是否成功
        """
        return await self.registry.deregister_service(
            service_name=service_name,
            group_name=group_name,
            ip=ip,
            port=port,
            cluster_name=cluster_name,
            ephemeral=ephemeral
        )
    
    async def get_service_instances(
        self,
        service_name: str,
        group_name: str = "DEFAULT_GROUP",
        healthy_only: bool = True,
        clusters: Optional[List[str]] = None
    ) -> List[ServiceInstance]:
        """
        获取服务实例列表
        
        Args:
            service_name: 服务名称
            group_name: 服务分组
            healthy_only: 是否只返回健康实例
            clusters: 集群列表
            
        Returns:
            List[ServiceInstance]: 服务实例列表
        """
        return await self.discovery.get_service_instances(
            service_name=service_name,
            group_name=group_name,
            healthy_only=healthy_only,
            clusters=clusters
        )
    
    async def choose_one_instance(
        self,
        service_name: str,
        group_name: str = "DEFAULT_GROUP",
        healthy_only: bool = True,
        clusters: Optional[List[str]] = None,
        strategy: str = "random"
    ) -> Optional[ServiceInstance]:
        """
        选择一个服务实例（支持负载均衡策略）
        
        Args:
            service_name: 服务名称
            group_name: 服务分组
            healthy_only: 是否只返回健康实例
            clusters: 集群列表
            strategy: 负载均衡策略，可选值: random, round_robin, weight_random
            
        Returns:
            Optional[ServiceInstance]: 选中的服务实例
        """
        return await self.discovery.choose_one_instance(
            service_name=service_name,
            group_name=group_name,
            healthy_only=healthy_only,
            clusters=clusters,
            strategy=strategy
        )
    
    async def get_config(
        self,
        data_id: str,
        group: str = "DEFAULT_GROUP",
        namespace: str = ""
    ) -> Optional[str]:
        """
        获取配置信息
        
        Args:
            data_id: 配置ID
            group: 配置分组
            namespace: 命名空间ID
            
        Returns:
            Optional[str]: 配置内容
        """
        request = ConfigRequest(
            data_id=data_id,
            group=group,
            namespace=namespace
        )
        return await self.config.get_config(request)
    
    async def set_config(
        self,
        data_id: str,
        group: str = "DEFAULT_GROUP",
        content: str = "",
        namespace: str = ""
    ) -> bool:
        """
        设置配置信息
        
        Args:
            data_id: 配置ID
            group: 配置分组
            content: 配置内容
            namespace: 命名空间ID
            
        Returns:
            bool: 设置是否成功
        """
        return await self.config.set_config(
            data_id=data_id,
            group=group,
            content=content,
            namespace=namespace
        )
    
    async def add_config_listener(
        self,
        data_id: str,
        callback: Callable[[str], None],
        group: str = "DEFAULT_GROUP",
        namespace: str = "",
        content_type: str = "text"
    ) -> bool:
        """
        添加配置监听器
        
        Args:
            data_id: 配置ID
            callback: 配置变更回调函数
            group: 配置分组
            namespace: 命名空间ID
            content_type: 内容类型
            
        Returns:
            bool: 添加是否成功
        """
        listener = ConfigListener(
            data_id=data_id,
            group=group,
            namespace=namespace,
            callback=callback,
            content_type=content_type
        )
        return await self.config.add_listener(listener)
    
    def _setup_fastapi_hooks(
        self,
        app: FastAPI,
        service_name: str,
        group_name: str,
        ip: str,
        port: int,
        cluster_name: str,
        ephemeral: bool
    ):
        """
        设置FastAPI应用的生命周期钩子，用于自动管理服务注册
        
        Args:
            app: FastAPI应用实例
            service_name: 服务名称
            group_name: 服务分组
            ip: 服务IP地址
            port: 服务端口
            cluster_name: 集群名称
            ephemeral: 是否为临时实例
        """
        # 应用启动时注册服务
        @app.on_event("startup")
        async def on_startup():
            try:
                log.info(f"FastAPI应用启动，开始注册服务: {service_name}")
                await self.register_service(
                    service_name=service_name,
                    ip=ip,
                    port=port,
                    group_name=group_name,
                    cluster_name=cluster_name,
                    ephemeral=ephemeral
                )
            except Exception as e:
                log.error(f"FastAPI应用启动时注册服务失败: {str(e)}")
        
        # 应用关闭时注销服务
        @app.on_event("shutdown")
        async def on_shutdown():
            try:
                log.info(f"FastAPI应用关闭，开始注销服务: {service_name}")
                await self.deregister_service(
                    service_name=service_name,
                    group_name=group_name,
                    ip=ip,
                    port=port,
                    cluster_name=cluster_name,
                    ephemeral=ephemeral
                )
            except Exception as e:
                log.error(f"FastAPI应用关闭时注销服务失败: {str(e)}")
    
    @classmethod
    def get_instance(cls) -> Optional['NacosClientManager']:
        """
        获取Nacos客户端管理器的单例实例
        
        Returns:
            Optional[NacosClientManager]: Nacos客户端管理器实例
        """
        return cls._instance

    @classmethod
    def get_registry_instance(cls) -> Optional['ServiceRegistry']:
        """
        获取服务注册管理器实例
        
        Returns:
            Optional[ServiceRegistry]: 服务注册管理器实例
        """
        return cls._instance.registry
