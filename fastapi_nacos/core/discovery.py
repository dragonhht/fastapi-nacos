import random
import time
from typing import List, Optional, Dict
from v2.nacos import NacosNamingService
from fastapi_nacos.models.service import ServiceInstance, ServiceInfo
from fastapi_nacos.utils.exceptions import ServiceDiscoveryError


class ServiceDiscovery:
    """服务发现管理类"""
    
    def __init__(self, 
        naming_service: NacosNamingService, 
        logger,
        server_addresses: str,
        namespace: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None):
        """
        初始化服务发现管理器
        
        Args:
            naming_service: Nacos命名服务实例
            logger: 日志记录器
            server_addresses: Nacos服务器地址
            namespace: Nacos命名空间ID
            username: Nacos用户名
            password: Nacos密码
        """
        self.naming_service = naming_service
        self.logger = logger
        self.server_addresses = server_addresses
        self.namespace = namespace
        self.username = username
        self.password = password
        self.service_cache: Dict[str, Dict] = {}  # 服务缓存，格式: {"service_group": {"instances": [], "timestamp": 0}}
        self.cache_ttl = 30  # 缓存有效期，单位：秒
    
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
        try:
            self.logger.info(f"查询服务实例: {service_name}，分组: {group_name}，健康实例: {healthy_only}")
            
            # 调用Nacos客户端获取服务实例
            # 使用ListInstanceParam对象
            from v2.nacos.naming.model.naming_param import ListInstanceParam
            list_param = ListInstanceParam(
                service_name=service_name,
                group_name=group_name,
                healthy_only=healthy_only,
                clusters=clusters or []
            )
            instances = await self.naming_service.list_instances(list_param)
            
            self.logger.debug(f"服务实例查询结果: {instances}")
            
            # 转换为ServiceInstance模型列表
            service_instances = []
            # 处理Nacos SDK返回格式，可能是字典或对象
            instances_data = instances
            if hasattr(instances, 'hosts'):
                instances_data = instances.hosts
            elif isinstance(instances, dict) and 'hosts' in instances:
                instances_data = instances['hosts']
            
            for instance in instances_data:
                # 处理实例数据格式，可能是字典或对象
                ip = instance.get('ip') if isinstance(instance, dict) else instance.ip
                port = instance.get('port') if isinstance(instance, dict) else instance.port
                weight = instance.get('weight', 1.0) if isinstance(instance, dict) else instance.weight
                healthy = instance.get('healthy', True) if isinstance(instance, dict) else instance.healthy
                enabled = instance.get('enabled', True) if isinstance(instance, dict) else instance.enabled
                metadata = instance.get('metadata', {}) if isinstance(instance, dict) else instance.metadata
                cluster_name = instance.get('clusterName') if isinstance(instance, dict) else getattr(instance, 'cluster_name', 'DEFAULT')
                instance_id = instance.get('instanceId') if isinstance(instance, dict) else getattr(instance, 'instance_id', f"{ip}:{port}:{cluster_name}@{service_name}")
                
                service_instance = ServiceInstance(
                    ip=ip,
                    port=port,
                    service_name=service_name,
                    group_name=group_name,
                    weight=weight,
                    healthy=healthy,
                    enabled=enabled,
                    metadata=metadata,
                    cluster_name=cluster_name,
                    instance_id=instance_id
                )
                service_instances.append(service_instance)
            
            self.logger.info(f"服务实例查询成功: {service_name}，找到 {len(service_instances)} 个实例")
            return service_instances
        except Exception as e:
            self.logger.error(f"查询服务实例失败: {service_name}，错误: {str(e)}")
            raise ServiceDiscoveryError(f"查询服务实例失败: {str(e)}") from e
    
    async def get_service_info(
        self,
        service_name: str,
        group_name: str = "DEFAULT_GROUP",
        clusters: Optional[List[str]] = None
    ) -> Optional[ServiceInfo]:
        """
        获取完整的服务信息
        
        Args:
            service_name: 服务名称
            group_name: 服务分组
            clusters: 集群列表
            
        Returns:
            Optional[ServiceInfo]: 服务信息模型
        """
        try:
            self.logger.info(f"查询服务信息: {service_name}，分组: {group_name}")
            
            # 调用Nacos客户端获取服务实例
            # 使用ListInstanceParam对象
            from v2.nacos.naming.model.naming_param import ListInstanceParam
            list_param = ListInstanceParam(
                service_name=service_name,
                group_name=group_name,
                healthy_only=False,  # 获取所有实例，无论健康状态
                clusters=clusters or []
            )
            instances = await self.naming_service.list_instances(list_param)
            
            if not instances:
                self.logger.warning(f"未找到服务信息: {service_name}")
                return None
            
            # 转换服务实例
            service_instances = []
            # 处理Nacos SDK返回格式，可能是字典或对象
            instances_data = instances
            if hasattr(instances, 'hosts'):
                instances_data = instances.hosts
            elif isinstance(instances, dict) and 'hosts' in instances:
                instances_data = instances['hosts']
            
            for instance in instances_data:
                # 处理实例数据格式，可能是字典或对象
                ip = instance.get('ip') if isinstance(instance, dict) else instance.ip
                port = instance.get('port') if isinstance(instance, dict) else instance.port
                weight = instance.get('weight', 1.0) if isinstance(instance, dict) else instance.weight
                healthy = instance.get('healthy', True) if isinstance(instance, dict) else instance.healthy
                enabled = instance.get('enabled', True) if isinstance(instance, dict) else instance.enabled
                metadata = instance.get('metadata', {}) if isinstance(instance, dict) else instance.metadata
                cluster_name = instance.get('clusterName') if isinstance(instance, dict) else getattr(instance, 'cluster_name', 'DEFAULT')
                instance_id = instance.get('instanceId') if isinstance(instance, dict) else getattr(instance, 'instance_id', f"{ip}:{port}:{cluster_name}@{service_name}")
                
                service_instance = ServiceInstance(
                    ip=ip,
                    port=port,
                    service_name=service_name,
                    group_name=group_name,
                    weight=weight,
                    healthy=healthy,
                    enabled=enabled,
                    metadata=metadata,
                    cluster_name=cluster_name,
                    instance_id=instance_id
                )
                service_instances.append(service_instance)
            
            # 转换为ServiceInfo模型
            service_info = ServiceInfo(
                name=service_name,
                group_name=group_name,
                clusters=clusters,
                cacheMillis=1000,  # 默认缓存时间
                hosts=service_instances,
                last_ref_time=int(time.time() * 1000),  # 当前时间戳
                checksum=None,
                all_ip=False,
                reach_protection_threshold=None
            )
            
            self.logger.info(f"服务信息查询成功: {service_name}")
            return service_info
        except Exception as e:
            self.logger.error(f"查询服务信息失败: {service_name}，错误: {str(e)}")
            raise ServiceDiscoveryError(f"查询服务信息失败: {str(e)}") from e
    
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
        try:
            instances = await self.get_service_instances(
                service_name=service_name,
                group_name=group_name,
                healthy_only=healthy_only,
                clusters=clusters
            )
            
            if not instances:
                self.logger.warning(f"未找到可用的服务实例: {service_name}")
                return None
            
            # 根据策略选择实例
            if strategy == "random":
                # 随机选择
                instance = random.choice(instances)
            elif strategy == "weight_random":
                # 加权随机选择
                total_weight = sum(instance.weight for instance in instances)
                if total_weight <= 0:
                    instance = random.choice(instances)
                else:
                    random_val = random.uniform(0, total_weight)
                    current_weight = 0
                    for instance in instances:
                        current_weight += instance.weight
                        if random_val <= current_weight:
                            break
            else:
                # 默认随机选择
                instance = random.choice(instances)
            
            self.logger.info(f"选择服务实例: {service_name}，实例: {instance.ip}:{instance.port}，策略: {strategy}")
            return instance
        except Exception as e:
            self.logger.error(f"选择服务实例失败: {service_name}，错误: {str(e)}")
            raise ServiceDiscoveryError(f"选择服务实例失败: {str(e)}") from e
    
    async def get_all_services(
        self,
        group_name: str = "DEFAULT_GROUP",
        page_no: int = 1,
        page_size: int = 100
    ) -> List[str]:
        """
        获取所有服务名称列表
        
        Args:
            group_name: 服务分组
            page_no: 页码
            page_size: 每页数量
            
        Returns:
            List[str]: 服务名称列表
        """
        try:
            self.logger.info(f"查询所有服务列表，分组: {group_name}")
            
            # 在新版本的Nacos SDK中，获取所有服务的方法名可能不同
            # 这里使用list_services方法，参数可能需要调整
            services = await self.naming_service.list_services(
                group_name=group_name,
                page_no=page_no,
                page_size=page_size
            )
            
            self.logger.debug(f"服务列表查询结果: {services}")
            
            # 提取服务名称
            service_names = []
            if hasattr(services, "service_names"):
                service_names = services.service_names
            elif hasattr(services, "doms"):
                service_names = services.doms
            elif isinstance(services, dict) and "doms" in services:
                service_names = services["doms"]
            
            self.logger.info(f"服务列表查询成功，找到 {len(service_names)} 个服务")
            return service_names
        except Exception as e:
            self.logger.error(f"查询所有服务列表失败，错误: {str(e)}")
            raise ServiceDiscoveryError(f"查询所有服务列表失败: {str(e)}") from e
    
    async def get_instance(
        self,
        service_name: str,
        ip: str,
        port: int,
        group_name: str = "DEFAULT_GROUP",
        cluster_name: str = "DEFAULT"
    ) -> Optional[ServiceInstance]:
        """
        获取单个服务实例信息
        
        Args:
            service_name: 服务名称
            ip: 服务IP地址
            port: 服务端口
            group_name: 服务分组
            cluster_name: 集群名称
            
        Returns:
            Optional[ServiceInstance]: 服务实例信息
        """
        try:
            self.logger.info(f"查询单个服务实例: {service_name}，实例: {ip}:{port}")
            
            # 先获取所有实例，然后筛选
            instances = await self.get_service_instances(
                service_name=service_name,
                group_name=group_name,
                healthy_only=False,
                clusters=[cluster_name]
            )
            
            # 查找匹配的实例
            for instance in instances:
                if instance.ip == ip and instance.port == port:
                    self.logger.info(f"找到服务实例: {service_name}，实例: {ip}:{port}")
                    return instance
            
            self.logger.warning(f"未找到服务实例: {service_name}，实例: {ip}:{port}")
            return None
        except Exception as e:
            self.logger.error(f"查询单个服务实例失败: {service_name}，实例: {ip}:{port}，错误: {str(e)}")
            raise ServiceDiscoveryError(f"查询单个服务实例失败: {str(e)}") from e
    
    async def refresh_service_cache(self, service_name: str, group_name: str = "DEFAULT_GROUP"):
        """
        刷新服务缓存
        
        Args:
            service_name: 服务名称
            group_name: 服务分组
        """
        try:
            self.logger.info(f"刷新服务缓存: {service_name}，分组: {group_name}")
            
            # 获取最新的服务实例
            instances = await self.get_service_instances(
                service_name=service_name,
                group_name=group_name,
                healthy_only=False
            )
            
            # 更新缓存
            cache_key = f"{service_name}@{group_name}"
            self.service_cache[cache_key] = {
                "instances": instances,
                "timestamp": self._get_current_timestamp()
            }
            
            self.logger.info(f"服务缓存刷新成功: {service_name}")
        except Exception as e:
            self.logger.error(f"刷新服务缓存失败: {service_name}，错误: {str(e)}")
            raise ServiceDiscoveryError(f"刷新服务缓存失败: {str(e)}") from e
    
    def _get_current_timestamp(self) -> int:
        """
        获取当前时间戳
        
        Returns:
            int: 当前时间戳（秒）
        """
        import time
        return int(time.time())
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        检查缓存是否有效
        
        Args:
            cache_key: 缓存键
            
        Returns:
            bool: 缓存是否有效
        """
        if cache_key not in self.service_cache:
            return False
        
        cache = self.service_cache[cache_key]
        current_time = self._get_current_timestamp()
        return (current_time - cache["timestamp"]) < self.cache_ttl