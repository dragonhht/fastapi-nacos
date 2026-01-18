from os import name
import time
import threading
from typing import Dict, Optional
from v2.nacos import NacosNamingService
from fastapi_nacos.models.service import ServiceRegisterRequest, ServiceInstance
from fastapi_nacos.utils.exceptions import ServiceRegistrationError, HeartbeatError


class ServiceRegistry:
    """服务注册管理类"""
    
    def __init__(self, 
        naming_service: NacosNamingService, 
        logger,
        server_addresses: str,
        namespace: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None):
        """
        初始化服务注册管理器
        
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
        self.registered_instances: Dict[str, Dict] = {}  # 存储已注册的实例信息
        self.heartbeat_threads: Dict[str, threading.Thread] = {}  # 存储心跳线程
        self.heartbeat_stop_events: Dict[str, threading.Event] = {}  # 存储心跳停止事件
        self.heartbeat_interval = 5  # 心跳间隔，单位：秒
    
    async def register_service(self,
        service_name: str,
        ip: str,
        port: int,
        group_name: str = 'DEFAULT_GROUP',
        weight: Optional[float] = 1.0,
        metadata: Dict[str, str] = {},
        cluster_name: str = '',
        ephemeral: bool = True) -> str:
        """
        注册服务到Nacos
        
        Args:
            service_name: 服务名称
            group_name: 服务分组名称
            ip: 服务实例IP地址
            port: 服务实例端口号
            weight: 服务实例权重（0-1000）
            metadata: 服务实例元数据
            cluster_name: 服务实例所在集群名称
            ephemeral: 是否为临时实例
            
        Returns:
            str: 注册的服务实例ID
        """
        try:
            self.logger.info(f"开始注册服务: {service_name}，IP: {ip}:{port}")
            # 调用Nacos客户端注册服务
            # 使用RegisterInstanceParam对象
            from v2.nacos.naming.model.naming_param import RegisterInstanceParam
            register_param = RegisterInstanceParam(
                service_name=service_name,
                group_name=group_name,
                ip=ip,
                port=port,
                weight=weight,
                metadata=metadata,
                cluster_name=cluster_name,
                ephemeral=ephemeral
            )
            result = await self.naming_service.register_instance(register_param)
            self.logger.debug(f"注册服务返回结果: {result}")
            
            # 生成实例ID（格式：ip:port:clusterName@serviceName）
            instance_id = f"{ip}:{port}:{cluster_name or 'DEFAULT'}@{service_name}"
            
            self.logger.info(f"服务注册成功: {service_name}，实例ID: {instance_id}")
            
            # 如果是临时实例，启动心跳线程
            if ephemeral:
                self._start_heartbeat(
                    instance_id=instance_id,
                    service_name=service_name,
                    ip=ip,
                    port=port,
                    group_name=group_name,
                    cluster_name=cluster_name
                )
            
            # 保存注册信息
            self.registered_instances[instance_id] = {
                "service_name": service_name,
                "ip": ip,
                "port": port,
                "group_name": group_name,
                "cluster_name": cluster_name,
                "ephemeral": ephemeral
            }
            
            return instance_id
        except Exception as e:
            self.logger.error(f"服务注册失败: {str(e)}")
            raise ServiceRegistrationError(f"服务注册失败: {str(e)}") from e
    
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
            ip: 服务IP地址
            port: 服务端口
            cluster_name: 集群名称
            ephemeral: 是否为临时实例
            
        Returns:
            bool: 注销是否成功
        """
        try:
            self.logger.info(f"开始注销服务: {service_name}")
            
            # 调用Nacos客户端注销服务
            # 使用DeregisterInstanceParam对象
            from v2.nacos.naming.model.naming_param import DeregisterInstanceParam
            deregister_param = DeregisterInstanceParam(
                service_name=service_name,
                group_name=group_name,
                ip=ip,
                port=port,
                cluster_name=cluster_name,
                ephemeral=ephemeral
            )
            result = await self.naming_service.deregister_instance(deregister_param)
            
            # 停止心跳线程（如果存在）
            if ephemeral:
                self._stop_heartbeat(service_name, ip, port)
            
            self.logger.info(f"服务注销成功: {service_name}")
            return result
        except Exception as e:
            self.logger.error(f"服务注销失败: {str(e)}")
            return False
    
    def _start_heartbeat(
        self,
        instance_id: str,
        service_name: str,
        ip: str,
        port: int,
        group_name: str,
        cluster_name: str
    ):
        """
        启动心跳线程
        
        注意：在新版本的Nacos SDK中，心跳由SDK内部管理，不需要手动发送心跳
        
        Args:
            instance_id: 实例ID
            service_name: 服务名称
            ip: 服务IP地址
            port: 服务端口
            group_name: 服务分组
            cluster_name: 集群名称
        """
        self.logger.info(f"服务实例 {instance_id} 心跳由Nacos SDK内部管理")
    
    def _stop_heartbeat(self, service_name: str, ip: str, port: int):
        """
        停止心跳线程
        
        注意：在新版本的Nacos SDK中，心跳由SDK内部管理，不需要手动停止心跳
        
        Args:
            service_name: 服务名称
            ip: 服务IP地址
            port: 服务端口
        """
        # 查找对应的实例ID
        instance_id = None
        for id, info in self.registered_instances.items():
            if (info["service_name"] == service_name and 
                info["ip"] == ip and 
                info["port"] == port):
                instance_id = id
                break
        
        if instance_id:
            # 移除注册信息
            if instance_id in self.registered_instances:
                del self.registered_instances[instance_id]
            
            self.logger.info(f"移除服务实例注册信息: {service_name}，实例ID: {instance_id}")
    
    def update_health_status(
        self,
        service_name: str,
        ip: str,
        port: int,
        healthy: bool,
        group_name: str = "DEFAULT_GROUP",
        cluster_name: str = "DEFAULT"
    ) -> bool:
        """
        更新服务健康状态
        
        注意：在新版本的Nacos SDK中，健康状态由SDK内部管理
        
        Args:
            service_name: 服务名称
            ip: 服务IP地址
            port: 服务端口
            healthy: 健康状态
            group_name: 服务分组
            cluster_name: 集群名称
            
        Returns:
            bool: 更新是否成功
        """
        self.logger.warning("在新版本的Nacos SDK中，健康状态由SDK内部管理，不需要手动更新")
        return True
    
    def get_registered_instances(self) -> Dict[str, Dict]:
        """
        获取已注册的服务实例列表
        
        Returns:
            Dict[str, Dict]: 已注册的服务实例信息
        """
        return self.registered_instances