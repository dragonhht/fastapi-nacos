"""
HTTP客户端,类似OpenFeign
"""

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from typing import Optional, Any
import enum
import httpx
import inspect

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
    if base_url.startswith("http"):
      self.base_url = base_url
      self.service_name = None
    else:
      self.base_url = None  # 延迟解析服务名
      self.service_name = base_url
    self.timeout = timeout
    self.config = config
    
  async def _resolve_service_name(self) -> str:
    """
    解析服务名到基础URL
    确保在服务发现之前Nacos客户端已经初始化
    """
    if self.base_url:
      return self.base_url
    
    if not self.service_name:
      raise ServiceDiscoveryError("服务名未设置")
    
    # 直接使用全局Nacos客户端实例
    from my_fastapi_nacos.core.dependencies import get_nacos_client_no_exception
    client = get_nacos_client_no_exception()
    
    service_discovery = client.discovery
    if service_discovery is None:
      raise ServiceDiscoveryError("服务发现组件未初始化，请确保应用配置了Nacos服务发现")
    
    service_instance = await service_discovery.choose_one_instance(self.service_name)
    if service_instance is None:
      raise ServiceDiscoveryError(f"未找到服务实例: {self.service_name}")
    
    # 构建基础URL
    self.base_url = f"http://{service_instance.ip}:{service_instance.port}"
    return self.base_url

  def __call__(self, cls) -> Any:
    feign_client = self  # 保存对FeignClient实例的引用
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
        def create_feign_method(http_method, path, content_type, original_method):
          # 获取原始方法的签名，用于映射位置参数到参数名
          sig = inspect.signature(original_method)
          
          async def feign_method(self, *args, **kwargs):
            try:
              # 提取实际参数（处理位置参数和dataclass对象）
              actual_kwargs = {}
              
              # 处理位置参数，将它们映射到参数名
              if args:
                # 获取参数名列表（排除self）
                param_names = list(sig.parameters.keys())[1:]  # 排除第一个参数self
                
                # 将位置参数映射到参数名
                for i, arg in enumerate(args):
                  if i < len(param_names):
                    param_name = param_names[i]
                    actual_kwargs[param_name] = arg
              
              # 处理关键字参数
              for key, value in kwargs.items():
                # 检查是否是dataclass对象
                if hasattr(value, '__dataclass_fields__'):
                  # 提取dataclass的字段和值
                  for field_name, field in value.__dataclass_fields__.items():
                    actual_kwargs[field_name] = getattr(value, field_name)
                else:
                  # 直接使用普通参数
                  actual_kwargs[key] = value
              
              # 解析服务名（如果需要）
              base_url = await feign_client._resolve_service_name()
              
              # 构建完整URL,替换路径参数（如 /user/{id}）
              url = path.format(**actual_kwargs)
              # 构造请求参数
              request_kwargs = {}
              
              # 使用传入的 content_type 参数
              request_headers = {"Content-Type": content_type}
              request_kwargs["headers"] = request_headers
              if http_method == "GET":
                # GET请求的查询参数
                request_kwargs["params"] = actual_kwargs
              elif http_method == "POST" or http_method == "PUT" or http_method == "PATCH":
                if content_type == MediaType.JSON.value:
                  # 请求的JSON数据
                  request_kwargs["json"] = actual_kwargs
                elif content_type == MediaType.FORM_URLENCODED.value:
                  # 请求的表单数据
                  request_kwargs["data"] = actual_kwargs
                elif content_type == MediaType.MULTIPART_FORM_DATA.value:
                  # 请求的多部分表单数据
                  request_kwargs["files"] = actual_kwargs
              elif http_method == "DELETE":
                request_kwargs["params"] = actual_kwargs

              # 创建HTTP请求
              # 处理base_url以/结尾的情况
              if base_url.endswith('/'):
                base_url = base_url[:-1]
              if url.startswith('/'):
                url = url[1:]
              full_url = f"{base_url}/{url}"
              request = httpx.Request(http_method, full_url, **request_kwargs)
              # 应用Feign配置（如果有）
              if config:
                request = await config.pre_request(request)
              # 发送请求
              async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.send(request)
              # 检查响应状态码
              response.raise_for_status()
              
              # 根据响应的Content-Type返回不同格式的数据
              response_content_type = response.headers.get('Content-Type', '')
              
              if 'application/json' in response_content_type:
                  # 返回JSON格式数据
                  return response.json()
              elif 'text/' in response_content_type:
                  # 返回文本格式数据
                  return response.text
              else:
                  # 返回原始字节数据
                  return response.content
            except httpx.HTTPStatusError as e:
              # 处理HTTP状态错误（4xx, 5xx）
              print(f"HTTP错误: {e.response.status_code} - {e.response.text}")
              raise e
            except httpx.RequestError as e:
              # 处理请求错误（网络问题等）
              print(f"请求错误: {e}")
              raise e
          return feign_method

        new_method = create_feign_method(http_method, path, content_type, method)

        # 替换原方法为新的HTTP请求实现
        setattr(cls, name, new_method)
    # 返回增强后的类
    return cls

@dataclass
class ReqModel:
  postId: int = None
  title: str = ''
  body: str = ''
  userId: int = 1


@FeignClient(base_url="https://jsonplaceholder.typicode.com")
class TestClient:

  @GetMapping("/posts")
  async def get_posts(self) -> list:
    pass
  
  @GetMapping("/posts/{id}")
  async def get_post(self, id: int) -> dict:
    pass
  
  @GetMapping("/comments")
  async def get_comments(self, req: ReqModel) -> list:
    pass
  @GetMapping("/comments")
  async def get_comment2s(self, postId: int) -> list:
    pass

  @PostMapping("/posts")
  async def post_posts(self, req: ReqModel) -> dict:
    pass
  @PutMapping("/posts/{id}")
  async def put_posts(self, id: int, req: ReqModel) -> dict:
    pass

async def main():
  client = TestClient()
  # print('get_posts')
  # print(await client.get_posts())
  print("获取帖子ID为1的所有评论:")
  comments = await client.get_comment2s(postId=1)
  print(comments)
  print("获取帖子ID为1的所有评论:")
  comments = await client.get_comment2s(1)
  print(comments)
  # print("创建新帖子:")
  # new_post = await client.post_posts(req=ReqModel(title="新帖子", body="这是新帖子的内容"))
  # print(new_post)
  # print("更新帖子ID为1的内容:")
  # updated_post = await client.put_posts(id=1, req=ReqModel(title="更新后的帖子", body="这是更新后的帖子内容"))
  # print(updated_post)

if __name__ == "__main__":
  asyncio.run(main())