from typing import Optional, Callable
from pydantic import BaseModel, Field


class ConfigRequest(BaseModel):
    """配置获取请求模型"""
    data_id: str
    group: str = Field(default="DEFAULT_GROUP")


class ConfigResponse(BaseModel):
    """配置获取响应模型"""
    data_id: str
    group: str
    namespace: str
    content: str
    type: Optional[str] = Field(default="text")


class ConfigListener(BaseModel):
    """配置监听器模型"""
    data_id: str
    group: str
    callback: Callable[[str], None]