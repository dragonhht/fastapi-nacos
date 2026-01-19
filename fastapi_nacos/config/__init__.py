# 应用配置类
from fastapi_nacos.utils.app_config_utils import load_config

app_config = load_config()
print(app_config)