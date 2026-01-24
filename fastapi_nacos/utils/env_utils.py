import os
import sys
from dotenv import load_dotenv

# 获取当前项目的绝对路径
startup_file = os.path.abspath(sys.argv[0])
root_dir = os.path.dirname(startup_file)

# 加载项目根目录下的.env文件
load_dotenv(os.path.join(root_dir, '.env'), override=True)

# 注册中心配置
discovery_server_addresses = os.getenv("NACOS_DISCOVERY_SERVER_ADDRESSES")
discovery_namespace = os.getenv("NACOS_DISCOVERY_NAMESPACE")
discovery_username = os.getenv("NACOS_DISCOVERY_USERNAME")
discovery_password = os.getenv("NACOS_DISCOVERY_PASSWORD")

# 配置中心配置
config_server_addresses = os.getenv("NACOS_CONFIG_SERVER_ADDRESSES")
config_namespace = os.getenv("NACOS_CONFIG_NAMESPACE")
config_username = os.getenv("NACOS_CONFIG_USERNAME")
config_password = os.getenv("NACOS_CONFIG_PASSWORD")

def get_var(var_name: str, default: str = None) -> str:
    """获取环境变量
    
    Args:
        var_name: 环境变量名
        default: 默认值
        
    Returns:
        环境变量值或默认值
    """
    return os.getenv(var_name, default)
