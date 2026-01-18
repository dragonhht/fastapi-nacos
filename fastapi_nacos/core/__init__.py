from fastapi_nacos.core.manager import NacosClientManager
from fastapi_nacos.core.dependencies import init_nacos_registry_discovery_client, init_nacos_config_client
from contextlib import asynccontextmanager
from fastapi import FastAPI
import fastapi_nacos.utils.env_utils as env_utils
from fastapi_nacos.utils.log_utils import log

async def init_nacos_registry_client():
  """初始化Nacos注册中心客户端"""
  if not env_utils.discovery_server_addresses:
    log.warning("NACOS_DISCOVERY_SERVER_ADDRESSES 未配置，跳过Nacos注册中心客户端初始化")
  else:
    log.info("开始初始化Nacos注册中心客户端...")
    await init_nacos_registry_discovery_client(
      server_addresses=env_utils.discovery_server_addresses,
      namespace=env_utils.discovery_namespace,
      username=env_utils.discovery_username,
      password=env_utils.discovery_password
    )
    log.info("Nacos注册中心客户端初始化完成")

async def init_config_client():
  """初始化Nacos配置中心客户端"""
  if not env_utils.config_server_addresses:
    log.warning("NACOS_CONFIG_SERVER_ADDRESSES 未配置，跳过Nacos配置中心客户端初始化")
  else:
    log.info("开始初始化Nacos配置中心客户端...")
    await init_nacos_config_client(
      server_addresses=env_utils.config_server_addresses,
      namespace=env_utils.config_namespace,
      username=env_utils.config_username,
      password=env_utils.config_password
    )
    log.info("Nacos配置中心客户端初始化完成")

async def startup():
  """自定义启动逻辑"""
  try:
    # 初始化Nacos注册中心客户端
    await init_nacos_registry_client()
    # 初始化Nacos配置中心客户端
    await init_config_client()
    # 注册服务
    await NacosClientManager.get_instance().register_service(
        service_name="fastapi-service",
        ip="192.168.1.220",
        port=8000,
    )
  except Exception as e:
    log.error(f"服务注册失败: {e}")
    log.info("注意：这可能是因为Nacos服务器未启动或无法连接。测试应用其他功能仍可正常进行。")

async def shutdown():
  """自定义关闭逻辑"""
  try:
    # 注销服务
    await NacosClientManager.get_instance().deregister_service(
        service_name="fastapi-service",
        ip="192.168.1.220",
        port=8000,
    )

    # 关闭Nacos客户端管理器
    NacosClientManager.get_instance().config_shutdown()
  except Exception as e:
    log.error(f"服务注销失败: {e}")
    log.info("注意：这可能是因为Nacos服务器未启动或无法连接。测试应用其他功能仍可正常进行。")

@asynccontextmanager
async def nacos_lifespan(app: FastAPI):
    """
    应用生命周期管理器
    - yield 之前：启动逻辑
    - yield 之后：关闭逻辑
    """
    # 启动逻辑
    await startup()
    
    # 应用运行期间
    yield
    
    # 关闭逻辑
    await shutdown()
    
    log.info("应用关闭")

def init_nacos_with_fastapi(app: FastAPI):
  """
  初始化Nacos客户端并注册FastAPI服务
  """
  if app.router.lifespan_context:
      log.warning("FastAPI应用已配置自定义生命周期管理")
      original_lifespan = app.router.lifespan_context
      
      # 包装生命周期管理
      @asynccontextmanager
      async def wrapped_lifespan(app: FastAPI):
        # 执行自定义的nacos生命周期管理
        await startup()
        # 执行原有生命周期管理
        async with original_lifespan(app) as state:
            yield state
        
        # 执行自定义的关闭逻辑
        await shutdown()
      
      app.router.lifespan_context = wrapped_lifespan
      log.info("Nacos生命周期管理已集成到FastAPI应用")
  else:
    log.info("FastAPI应用未配置自定义生命周期管理，将使用Nacos默认生命周期管理")
    app.router.lifespan_context = nacos_lifespan