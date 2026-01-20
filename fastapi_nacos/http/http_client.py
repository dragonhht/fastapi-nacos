"""
HTTP客户端,类似OpenFeign
"""

from abc import ABC, abstractmethod
import asyncio
from typing import Optional, Any
import enum
import httpx

class MediaType(enum.Enum):
  """
  媒体类型枚举类，用于指定HTTP请求的Content-Type头
  """
  JSON = "application/json"
  FORM_URLENCODED = "application/x-www-form-urlencoded"
  MULTIPART_FORM_DATA = "multipart/form-data"
  OCTET_STREAM = "application/octet-stream"
  XML = "application/xml"
  GIF = "image/gif"
  JPEG = "image/jpeg"
  PNG = "image/png"
  HTML = "text/html"

"""
请求方法装饰器
"""

def GetMapping(path: str):
  """
  GET请求方法装饰器

  Args:
      path (str): 请求路径，例如 "/users/{user_id}"
  """
  def decorator(func):
    func._http_method = "GET"
    func._path = path
    return func
  return decorator

def PostMapping(path: str, content_type: MediaType = MediaType.JSON):
  """
  POST请求方法装饰器

  Args:
      path (str): 请求路径，例如 "/users"
  """
  def decorator(func):
    func._http_method = "POST"
    func._path = path
    func._content_type = content_type.value
    return func
  return decorator

def PutMapping(path: str, content_type: MediaType = MediaType.JSON):
  """
  PUT请求方法装饰器

  Args:
      path (str): 请求路径，例如 "/users/{user_id}"
  """
  def decorator(func):
    func._http_method = "PUT"
    func._path = path
    func._content_type = content_type.value
    return func
  return decorator

def DeleteMapping(path: str, content_type: MediaType = MediaType.JSON):
  """
  DELETE请求方法装饰器

  Args:
      path (str): 请求路径，例如 "/users/{user_id}"
  """
  def decorator(func):
    func._http_method = "DELETE"
    func._path = path
    func._content_type = content_type.value
    return func
  return decorator

def PatchMapping(path: str, content_type: MediaType = MediaType.JSON):
  """
  PATCH请求方法装饰器

  Args:
      path (str): 请求路径，例如 "/users/{user_id}"
  """
  def decorator(func):
    func._http_method = "PATCH"
    func._path = path
    func._content_type = content_type.value
    return func
  return decorator


class FeignConfig(ABC):
  """
  Feign客户端配置基类，用于http请求前做额外处理
  """
  @abstractmethod
  async def pre_request(self, request: httpx.Request) -> httpx.Request:
    """
    对HTTP请求进行预处理

    Args:
        request (httpx.Request): 原始HTTP请求对象

    Returns:
        httpx.Request: 处理后的HTTP请求对象
    """
    pass

# 声明式客户端装饰器
class FeignClient:
  """
  Feign客户端类，用于发送HTTP请求
  
  Args:
      base_url (str): 服务的基础URL，例如 "http://localhost:8000"。 如果使用服务名，则会自动从Nacos获取服务实例的URL
      timeout (float, optional): 请求超时时间，单位为秒。默认值为5秒。
      config (Optional[FeignConfig], optional): Feign客户端配置对象。默认值为None。
  """

  def __init__(self, base_url: str, timeout: float = 5, config: Optional[FeignConfig] = None):
    # TODO 支持服务名
    self.base_url = base_url
    self.timeout = timeout
    self.config = config

  def __call__(self, cls) -> Any:
    base_url = self.base_url
    timeout = self.timeout
    config = self.config
    # 遍历类的所有方法
    for name, method in cls.__dict__.items():
      # 只处理被GetMapping/PostMapping/PutMapping/DeleteMapping标记的方法
      if callable(method) and not name.startswith('_') and hasattr(method, '_http_method'):
        # 提取方法的HTTP元数据
        http_method = method._http_method
        path = method._path
        content_type = getattr(method, "_content_type", MediaType.JSON.value)

        # 定义新的方法用于实现HTTP请求
        def create_feign_method(http_method, path, content_type):
          async def feign_method(self, *args, **kwargs):
            try:
              # 构建完整URL,替换路径参数（如 /user/{id}）
              url = path.format(kwargs)
              # 构造请求参数
              request_kwargs = {}
              
              request_kwargs["headers"] = {"Content-Type": content_type}
              if http_method == "GET":
                # GET请求的查询参数
                request_kwargs["params"] = kwargs
              elif http_method == "POST" or http_method == "PUT" or http_method == "PATCH":
                if content_type == MediaType.JSON.value:
                  # 请求的JSON数据
                  request_kwargs["json"] = kwargs
                elif content_type == MediaType.FORM_URLENCODED.value:
                  # 请求的表单数据
                  request_kwargs["data"] = kwargs
                elif content_type == MediaType.MULTIPART_FORM_DATA.value:
                  # 请求的多部分表单数据
                  request_kwargs["files"] = kwargs
              elif http_method == "DELETE":
                request_kwargs["params"] = kwargs

              # 创建HTTP请求
              # TODO 需要处理base_url以/结尾的情况
              full_url = f"{base_url}{url}"
              request = httpx.Request(http_method, full_url, **request_kwargs)
              # 应用Feign配置（如果有）
              if config:
                request = await config.pre_request(request)
              # 发送请求
              async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.send(request)
              # 检查响应状态码
              response.raise_for_status()
              # 返回响应JSON数据
              # TODO 处理其他格式的结果
              return response.json()
            except httpx.HTTPStatusError as e:
              # 处理HTTP状态错误（4xx, 5xx）
              print(f"HTTP错误: {e.response.status_code} - {e.response.text}")
              raise e
            except httpx.RequestError as e:
              # 处理请求错误（网络问题等）
              print(f"请求错误: {e}")
              raise e
          return feign_method

        new_method = create_feign_method(http_method, path, content_type)

        # 替换原方法为新的HTTP请求实现
        setattr(cls, name, new_method)
    # 返回增强后的类
    return cls

@FeignClient(base_url="https://www.baidu.com")
class UserClient:

  @GetMapping("/s")
  async def get_user(self, ie: str, wd: str) -> Any:
    pass
  
  @GetMapping("/{path}")
  async def get_users(self, path: str, ie: str, wd: str) -> list:
    pass

async def main():
  client = UserClient()
  user = await client.get_user(ie="utf-8", wd="fastapi-nacos")
  print(user)

if __name__ == "__main__":
  asyncio.run(main())