from fastapi_nacos.core.manager import NacosClientManager
from fastapi_nacos.core.dependencies import init_nacos_registry_discovery_client, init_nacos_config_client
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_nacos.models.config import ConfigListener
from fastapi_nacos.utils.log_utils import log
from fastapi_nacos.config import app_config
from fastapi_nacos.utils.ip_utils import get_ip_address

global_ip = get_ip_address()

async def init_nacos_registry_client():
  """初始化Nacos注册中心客户端"""
  discovery_server_addresses = app_config.get("nacos.discovery.server_addresses")
  if not discovery_server_addresses:
    log.warning("nacos.discovery.server_addresses未配置，跳过Nacos注册中心客户端初始化")
  else:
    log.info("开始初始化Nacos注册中心客户端...")
    await init_nacos_registry_discovery_client(
      server_addresses=discovery_server_addresses,
      namespace=app_config.get("nacos.discovery.namespace"),
      username=app_config.get("nacos.discovery.username"),
      password=app_config.get("nacos.discovery.password")
    )
    log.info("Nacos注册中心客户端初始化完成")

async def init_config_client():
  """初始化Nacos配置中心客户端"""
  config_server_addresses = app_config.get("nacos.config.server_addresses")
  if not config_server_addresses:
    log.warning("nacos.config.server_addresses未配置，跳过Nacos配置中心客户端初始化")
  else:
    log.info("开始初始化Nacos配置中心客户端...")
    await init_nacos_config_client(
      server_addresses=config_server_addresses,
      namespace=app_config.get("nacos.config.namespace"),
      username=app_config.get("nacos.config.username"),
      password=app_config.get("nacos.config.password")
    )
    log.info("Nacos配置中心客户端初始化完成")
    log.info("开始初始化Nacos配置中心监听...")
    await init_watch_config()

async def parse_update_config(namespace: str, data_id: str, group: str = "DEFAULT_GROUP", content: str = None):
  """解析并更新Nacos配置"""
  await NacosClientManager.get_instance().parse_config_content(data_id, group, content)
    

async def init_watch_config():
  """初始化Nacos配置中心监听"""
  imports = app_config.get("nacos.config.imports")
  if not imports:
    log.warning("nacos.config.imports未配置，跳过Nacos配置中心监听初始化")
  else:
    log.info("开始初始化Nacos配置中心监听...")
    for item in imports:
      data_id = item.get("data-id")
      group = item.get("group", "DEFAULT_GROUP")
      if not data_id:
        log.warning(f"nacos.config.imports.item.data-id未配置，跳过Nacos配置中心监听初始化: {item}")
        continue
      # 初始化时获取配置
      await NacosClientManager.get_instance().fetch_and_parse_config(data_id=data_id, group=group)
      # 添加监听，当配置变化时变更配置数据
      await NacosClientManager.get_instance().config.add_listener(
        ConfigListener(
          group=group,
          data_id=data_id,
          callback=parse_update_config
        )
      )
    log.info("Nacos配置中心监听初始化完成")

async def startup():
  """自定义启动逻辑"""
  try:
    # 初始化Nacos注册中心客户端
    await init_nacos_registry_client()
    # 初始化Nacos配置中心客户端
    await init_config_client()
    # 注册服务
    app_name = app_config.get("app.name")
    if app_name:
      await NacosClientManager.get_instance().register_service(
        service_name=app_name,
        ip=global_ip,
        port=app_config.get("app.port", 8000),
      )
  except Exception as e:
    log.error(f"服务注册失败: {e}")
    log.info("注意：这可能是因为Nacos服务器未启动或无法连接。测试应用其他功能仍可正常进行。")

async def shutdown():
  """自定义关闭逻辑"""
  try:
    # 注销服务
    app_name = app_config.get("app.name")
    if app_name:
      await NacosClientManager.get_instance().deregister_service(
        service_name=app_name,
        ip=global_ip,
        port=app_config.get("app.port", 8000),
      )

    # 关闭Nacos客户端管理器
    await NacosClientManager.get_instance().config_shutdown()
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