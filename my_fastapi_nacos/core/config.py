import json
import yaml
from typing import Dict, Optional
from v2.nacos import NacosConfigService
from my_fastapi_nacos.models.config import ConfigListener
from my_fastapi_nacos.utils.exceptions import ConfigError, ConfigListenerError


class ConfigManager:
    """配置中心管理类"""
    
    def __init__(self, config_service: NacosConfigService, logger, server_addresses, namespace, username, password):
        """
        初始化配置中心管理器
        
        Args:
            config_service: Nacos配置服务实例
            logger: 日志记录器
            server_addresses: Nacos服务器地址列表
            namespace: Nacos命名空间
            username: Nacos用户名
            password: Nacos密码
        """
        self.config_service = config_service
        self.logger = logger
        self.server_addresses = server_addresses
        self.namespace = namespace
        self.username = username
        self.password = password
        self.config_listeners: Dict[str, ConfigListener] = {}  # 配置监听器
    
    async def get_config(self, data_id: str, group: str = "DEFAULT_GROUP") -> Optional[str]:
        """
        获取配置信息
        
        Args:
            data_id: 配置数据ID
            group: 配置分组，默认DEFAULT_GROUP
            
        Returns:
            Optional[str]: 配置内容
        """
        try:
            self.logger.info(f"获取配置: data_id={data_id}, group={group}")
            
            # 调用Nacos客户端获取配置
            from v2.nacos.config.model.config_param import ConfigParam
            config_param = ConfigParam(
                data_id=data_id,
                group=group
            )
            content = await self.config_service.get_config(config_param)
            
            self.logger.debug(f"配置获取结果: {content}")
            
            self.logger.info(f"配置获取成功: data_id={data_id}")
            return content
        except Exception as e:
            self.logger.error(f"获取配置失败: data_id={data_id}，错误: {str(e)}")
            raise ConfigError(f"获取配置失败: {str(e)}") from e
    
    async def get_config_dict(self, data_id: str, group: str = "DEFAULT_GROUP") -> Dict:
        """
        获取配置信息并转换为字典
        
        Args:
            data_id: 配置数据ID
            group: 配置分组，默认DEFAULT_GROUP
            
        Returns:
            Dict: 配置内容字典
        """
        content = await self.get_config(data_id, group)
        if not content:
            return {}
        
        try:
            # 尝试解析为JSON
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # 尝试解析为YAML
                return yaml.safe_load(content)
            except yaml.YAMLError:
                self.logger.error(f"配置内容解析失败: data_id={request.data_id}")
                raise ConfigError(f"配置内容解析失败: data_id={request.data_id}")
    
    async def add_listener(self, listener: ConfigListener) -> bool:
        """
        添加配置监听器
        
        Args:
            listener: 配置监听器模型
            
        Returns:
            bool: 添加是否成功
        """
        try:
            listener_key = f"{self.namespace}:{listener.group}:{listener.data_id}"
            self.logger.info(f"添加配置监听器: {listener_key}")
            
            # 保存监听器
            self.config_listeners[listener_key] = listener
            
            # 在新版本的Nacos SDK中，使用add_listener方法添加监听器
            # 该方法内部会管理监听线程
            await self.config_service.add_listener(
                data_id=listener.data_id,
                group=listener.group,
                listener=listener.callback
            )
            self.logger.info(f"配置监听器添加成功: {listener_key}")
            return True
        except Exception as e:
            self.logger.error(f"添加配置监听器失败: {listener_key}，错误: {str(e)}")
            raise ConfigListenerError(f"添加配置监听器失败: {str(e)}") from e
    
    async def remove_listener(self, data_id: str, group: str = "DEFAULT_GROUP", namespace: str = "") -> bool:
        """
        移除配置监听器
        
        Args:
            data_id: 配置ID
            group: 配置分组
            namespace: 命名空间ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            listener_key = f"{namespace}:{group}:{data_id}"
            self.logger.info(f"移除配置监听器: {listener_key}")
            
            # 获取监听器
            if listener_key in self.config_listeners:
                listener = self.config_listeners[listener_key]
                
                # 在新版本的Nacos SDK中，使用remove_listener方法移除监听器
                await self.config_service.remove_listener(
                    data_id=listener.data_id,
                    group=listener.group,
                    listener=listener.callback
                )
                
                # 移除监听器
                del self.config_listeners[listener_key]
                self.logger.info(f"配置监听器移除成功: {listener_key}")
                return True
            else:
                self.logger.warning(f"配置监听器不存在: {listener_key}")
                return False
        except Exception as e:
            self.logger.error(f"移除配置监听器失败: {listener_key}，错误: {str(e)}")
            raise ConfigListenerError(f"移除配置监听器失败: {str(e)}") from e
    
    def _start_listener(self, listener: ConfigListener, listener_key: str):
        """
        启动配置监听线程
        
        注意：在新版本的Nacos SDK中，监听器由SDK内部管理，不需要手动启动监听线程
        
        Args:
            listener: 配置监听器模型
            listener_key: 监听器键
        """
        self.logger.info(f"配置监听器 {listener_key} 由Nacos SDK内部管理")
    
    def _stop_listener(self, listener_key: str):
        """
        停止配置监听线程
        
        注意：在新版本的Nacos SDK中，监听器由SDK内部管理，不需要手动停止监听线程
        
        Args:
            listener_key: 监听器键
        """
        self.logger.info(f"配置监听器 {listener_key} 由Nacos SDK内部管理")

    async def shutdown(self):
        """
        关闭配置中心客户端
        """
        if self.config_service:
          await self.config_service.shutdown()