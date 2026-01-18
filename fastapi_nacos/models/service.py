from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class ServiceInstance(BaseModel):
    """服务实例模型"""
    ip: str
    port: int
    service_name: str
    group_name: str = Field(default="DEFAULT_GROUP")
    weight: float = Field(default=1.0, ge=0, le=1000)
    healthy: bool = Field(default=True)
    enabled: bool = Field(default=True)
    metadata: Dict[str, str] = Field(default_factory=dict)
    cluster_name: str = Field(default="DEFAULT")
    instance_id: Optional[str] = Field(default=None)


class ServiceRegisterRequest(BaseModel):
    """服务注册请求模型"""
    service_name: str
    group_name: str = Field(default="DEFAULT_GROUP")
    ip: str
    port: int
    weight: float = Field(default=1.0, ge=0, le=1000)
    metadata: Dict[str, str] = Field(default_factory=dict)
    cluster_name: str = Field(default="DEFAULT")
    ephemeral: bool = Field(default=True)


class ServiceInfo(BaseModel):
    """服务信息模型"""
    name: str
    group_name: str
    clusters: Optional[str] = None
    cacheMillis: int = 1000
    hosts: List[ServiceInstance]
    last_ref_time: Optional[int] = None
    checksum: Optional[str] = None
    all_ip: bool = False
    reach_protection_threshold: Optional[int] = None