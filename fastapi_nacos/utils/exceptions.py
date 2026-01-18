class FastApiNacosException(Exception):
    """FastAPI-Nacos SDK的基础异常类"""
    pass


class NacosConnectionError(FastApiNacosException):
    """Nacos连接错误异常"""
    pass


class ServiceRegistrationError(FastApiNacosException):
    """服务注册错误异常"""
    pass


class ServiceDiscoveryError(FastApiNacosException):
    """服务发现错误异常"""
    pass


class ConfigError(FastApiNacosException):
    """配置中心错误异常"""
    pass


class ConfigListenerError(FastApiNacosException):
    """配置监听错误异常"""
    pass


class HeartbeatError(FastApiNacosException):
    """心跳发送错误异常"""
    pass