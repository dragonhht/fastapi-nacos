from typing import Dict, Optional, Callable
from pydantic import BaseModel, Field


class ConfigRequest(BaseModel):
    """配置获取请求模型"""
    data_id: str
    group: str = Field(default="DEFAULT_GROUP")
    namespace: str = Field(default="")


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
    namespace: str
    callback: Callable[[str], None]
    content_type: str = Field(default="text")