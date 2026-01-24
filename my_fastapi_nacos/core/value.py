"""
配置值装饰器模块
"""

import re
from typing import Callable, Any
from my_fastapi_nacos.core.manager import NacosClientManager

# 配置值引用正则表达式: ${key:default} 或 ${key}
CONFIG_VALUE_PATTERN = re.compile(r'^\$\{([a-zA-Z0-9_.]+)(?::([^}]*))?\}$')


def Value(config_key: str) -> Callable:
    """
    配置值装饰器，支持从Nacos配置中心获取配置值
    
    支持两种格式：
    1. ${app.name} - 从Nacos获取app.name配置值
    2. ${app.name:api-server} - 从Nacos获取app.name配置值，未找到时返回默认值api-server
    
    Args:
        config_key: 配置值引用字符串，如${app.name}或${app.name:api-server}
        
    Returns:
        装饰器函数
    """
    # 解析配置键和默认值
    match = CONFIG_VALUE_PATTERN.match(config_key)
    if not match:
        raise ValueError(f"Invalid config key format: {config_key}")
    
    key = match.group(1)
    default = match.group(2) if match.group(2) is not None else None
    
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取配置值
            config_value = NacosClientManager.get_instance().get_config_val(key, default=default)
            # 直接返回配置值，不调用原始函数
            return config_value
        
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取配置值
            config_value = NacosClientManager.get_instance().get_config_val(key, default=default)
            # 直接返回配置值，不调用原始函数
            return config_value
        
        # 根据原始函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 导入asyncio用于检测异步函数
import asyncio
