from typing import Dict, Optional, List, Callable, Any
from v2.nacos import ClientConfigBuilder, NacosNamingService, NacosConfigService
from fastapi_nacos.core.registration import ServiceRegistry
from fastapi_nacos.core.discovery import ServiceDiscovery
from fastapi_nacos.core.config import ConfigManager
from fastapi_nacos.models.service import ServiceInstance
from fastapi_nacos.models.config import ConfigListener
from fastapi_nacos.utils.log_utils import log, log_dir, log_level
from fastapi_nacos.utils.exceptions import NacosConnectionError
from fastapi_nacos.utils.app_config_utils import parse_yaml_content, AppConfig
import yaml

class NacosClientManager:
    """Nacos客户端管理器，SDK的主要入口点"""
    
    # 单例实例
    _instance: Optional['NacosClientManager'] = None
    
    def __init__(self):
        """
        初始化Nacos客户端管理器
        """
        NacosClientManager._instance = self
        print("初始化Nacos客户端管理器-----------------------------------")
        # 维护全局配置字典，用于存储解析后的Nacos配置信息
        self.all_config_dict: Dict[str, AppConfig] = {}

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
                              .log_level(log_level)
                              .log_dir(log_dir)
                              .build()
                            )
            self.config_service = await NacosConfigService.create_config_service(client_config)
            self._config = ConfigManager(self.config_service, log, server_addresses, namespace, username, password)
        except Exception as e:
            log.error(f"初始化配置中心基础服务失败: {str(e)}")
            raise NacosConnectionError(f"初始化配置中心基础服务失败: {str(e)}") from e
    
    @property
    def config(self) -> ConfigManager:
        """获取配置管理器实例"""
        return self._config
    
    async def fetch_and_parse_config(self, data_id: str, group: str = "DEFAULT_GROUP") -> Dict[str, Any]:
        """
        根据指定的data-id和group从Nacos服务获取配置信息并解析
        
        Args:
            data_id: 配置的data-id
            group: 配置的group，默认值为"DEFAULT_GROUP"
            
        Returns:
            解析后的配置字典
            
        Raises:
            NacosConnectionError: 配置中心服务未初始化或网络请求失败
            yaml.YAMLError: YAML解析错误
            Exception: 其他未知错误
        """
        if not hasattr(self, '_config'):
            raise NacosConnectionError("配置中心服务未初始化，请先调用init_config_service方法")
        
        try:
            # 从Nacos获取配置
            config_content = await self.config.get_config(data_id, group)
            await self.parse_config_content(data_id, group, config_content)
            
        except NacosConnectionError:
            raise
        except yaml.YAMLError:
            raise
        except Exception as e:
            log.error(f"获取配置失败: {str(e)}, data_id={data_id}, group={group}")
            raise NacosConnectionError(f"获取配置失败: {str(e)}") from e

    async def parse_config_content(self, data_id: str, group: str = "DEFAULT_GROUP", config_content: str = None):
        """解析并更新Nacos配置"""
        if not config_content:
            log.warning(f"未获取到配置: data_id={data_id}, group={group}")
            self.all_config_dict[data_id] = AppConfig({})
            return {}
        
        # 解析YAML格式的配置内容
        try:
            yaml_dict = yaml.safe_load(config_content)
            if not isinstance(yaml_dict, dict):
                log.warning(f"配置内容不是有效的YAML字典: data_id={data_id}, group={group}")
                return {}
        except yaml.YAMLError as e:
            log.error(f"YAML解析错误: {str(e)}, data_id={data_id}, group={group}")
            raise
        
        # 使用parse_yaml_content方法解析配置内容
        parsed_config = parse_yaml_content(yaml_dict)
        
        # 将解析后的配置结果更新到all_config_dict中
        # 使用data_id作为键，确保配置数据的准确性和完整性
        self.all_config_dict[data_id] = AppConfig(parsed_config)
        
        log.info(f"配置获取并解析成功: data_id={data_id}, group={group}")
        return parsed_config

    def get_config_val(self, key: str, default: Any = None) -> Any:
        """
        获取指定key的配置值
        
        Args:
            key: 配置项的键
        Returns:
            配置项的值，若不存在则返回None
        """
        for data_id, config_dict in self.all_config_dict.items():
          val = config_dict.get(key, None)
          if val:
            return val
        return default

    async def register_service(
        self,
        service_name: str,
        ip: str,
        port: int,
        group_name: str = 'DEFAULT_GROUP',
        weight: Optional[float] = 1.0,
        metadata: Dict[str, str] = {},
        cluster_name: str = '',
        ephemeral: bool = True
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
            
        Returns:
            str: 注册的服务实例ID
        """
        if self.registry:
          instance_id = await self.registry.register_service(
              service_name=service_name,
              group_name=group_name,
              ip=ip,
              port=port,
              weight=weight,
              metadata=metadata or {},
              cluster_name=cluster_name,
              ephemeral=ephemeral
          )
          return instance_id
        else:
          log.error("Nacos注册中心客户端未初始化")
    
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
        if self.registry:
          return await self.registry.deregister_service(
              service_name=service_name,
              group_name=group_name,
              ip=ip,
              port=port,
              cluster_name=cluster_name,
              ephemeral=ephemeral
          )
        else:
          log.error("Nacos注册中心客户端未初始化")
          return False
    
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
    ) -> Optional[str]:
        """
        获取配置信息
        
        Args:
            data_id: 配置ID
            group: 配置分组
            
        Returns:
            Optional[str]: 配置内容
        """
        log.info(f"获取配置: data_id={data_id}, group={group}")
        
        return await self.config.get_config(data_id=data_id, group=group)
    
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

    async def config_shutdown(self):
        """
        关闭配置中心客户端
        """
        if self.config:
          await self.config.shutdown()

    @classmethod
    def get_instance(cls) -> Optional['NacosClientManager']:
        """
        获取Nacos客户端管理器的单例实例
        
        Returns:
            Optional[NacosClientManager]: Nacos客户端管理器实例
        """
        if cls._instance is None:
            cls._instance = NacosClientManager()
        return cls._instance

    @classmethod
    def get_registry_instance(cls) -> Optional['ServiceRegistry']:
        """
        获取服务注册管理器实例
        
        Returns:
            Optional[ServiceRegistry]: 服务注册管理器实例
        """
        return cls._instance.registry

    @classmethod
    def get_discovery_instance(cls) -> Optional['ServiceDiscovery']:
        """
        获取服务发现管理器实例
        
        Returns:
            Optional[ServiceDiscovery]: 服务发现管理器实例
        """
        return cls._instance.discovery
