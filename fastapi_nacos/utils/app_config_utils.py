"""
项目配置文件解析工具

此模块提供配置文件解析功能，支持以下特性：
1. 默认从 conf/app.yml 读取 YAML 配置
2. 支持通过命令行参数 --conf 指定自定义配置文件路径
3. 双重读取机制：YAML 配置不存在时自动从环境变量获取
4. 完善的错误处理和友好的错误提示
5. 返回结构化配置对象，方便参数访问
"""

import os
import sys
import yaml
import re
from fastapi_nacos.utils.log_utils import log
from fastapi_nacos.utils.env_utils import get_var
from typing import Dict, Any, Union

# 环境变量引用正则表达式: ${ENV_VAR:default_value}
ENV_VAR_PATTERN = re.compile(r'\$\{([^:}]+)(?::([^}]*))?\}')


def substitute_env_vars(value: Union[str, Dict[str, Any], Any]) -> Union[str, Dict[str, Any], Any]:
    """递归替换字符串中的环境变量引用
    
    Args:
        value: 要处理的值，可以是字符串、字典或其他类型
        
    Returns:
        替换后的对应值
    """
    if isinstance(value, str):
        # 查找并替换所有环境变量引用
        def replace_match(match: re.Match) -> str:
            env_var = match.group(1)
            default = match.group(2) or ''
            return get_var(env_var, default)
        
        return ENV_VAR_PATTERN.sub(replace_match, value)
    elif isinstance(value, dict):
        # 递归处理字典
        return {
            key: substitute_env_vars(val)
            for key, val in value.items()
        }
    elif isinstance(value, list):
        # 递归处理列表
        return [substitute_env_vars(item) for item in value]
    else:
        # 其他类型直接返回
        return value


class AppConfig:
    """配置对象类，提供属性访问和字典访问两种方式"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """初始化配置对象
        
        Args:
            config_dict: 配置字典
        """
        self._config = config_dict
        # 将字典转换为属性
        self._convert_dict_to_attrs(config_dict)
    
    def _convert_dict_to_attrs(self, data: Dict[str, Any], prefix: str = ""):
        """将字典递归转换为对象属性
        
        Args:
            data: 要转换的字典数据
            prefix: 属性前缀（用于嵌套结构）
        """
        for key, value in data.items():
            attr_name = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                # 递归处理嵌套字典
                nested_attr = AppConfig(value)
                setattr(self, attr_name, nested_attr)
            else:
                # 直接设置简单值
                setattr(self, attr_name, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（类似字典的get方法）
        
        Args:
            key: 配置键名，支持嵌套格式如 "db.host"
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                elif hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            return value
        except (KeyError, AttributeError):
            return default
    
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问
        
        Args:
            key: 配置键名
            
        Returns:
            配置值
        """
        return self.get(key)
    
    def __contains__(self, key: str) -> bool:
        """检查配置是否包含指定键
        
        Args:
            key: 配置键名
            
        Returns:
            是否包含该键
        """
        return self.get(key) is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            配置字典
        """
        return self._config
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            配置的字符串表示
        """
        return yaml.dump(self._config, default_flow_style=False, allow_unicode=True)

def read_yaml_file(file_path: str) -> Dict[str, Any]:
    """读取 YAML 配置文件并替换环境变量
    
    Args:
        file_path: YAML 文件路径
        
    Returns:
        配置字典
        
    Raises:
        FileNotFoundError: 文件不存在
        yaml.YAMLError: YAML 格式错误
        IOError: 文件读取错误
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"配置文件不存在: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
            # 应用环境变量替换
            return substitute_env_vars(config_dict)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"YAML 格式错误: {e}")
    except IOError as e:
        raise IOError(f"文件读取错误: {e}")

def merge_config(config_dict: Dict[str, Any], env_prefix: str = "") -> Dict[str, Any]:
    """合并配置字典和环境变量
    
    Args:
        config_dict: 从文件读取的配置字典
        env_prefix: 环境变量前缀
        
    Returns:
        合并后的配置字典
    """
    merged = {}  # 避免修改原始字典
    
    for key, value in config_dict.items():
        if isinstance(value, dict):
            # 递归处理嵌套字典
            nested_prefix = f"{env_prefix}{key}_" if env_prefix else f"{key}_"
            merged[key] = merge_config(value, nested_prefix)
        else:
            # 优先使用环境变量（如果存在）
            env_key = f"{env_prefix}{key}".upper()
            env_value = get_var(env_key)
            if env_value is not None:
                # 根据原始值类型转换环境变量
                if isinstance(value, bool):
                    merged[key] = env_value.lower() in ('true', '1', 'yes')
                elif isinstance(value, int):
                    try:
                        merged[key] = int(env_value)
                    except ValueError:
                        merged[key] = value  # 转换失败则使用原始值
                elif isinstance(value, float):
                    try:
                        merged[key] = float(env_value)
                    except ValueError:
                        merged[key] = value  # 转换失败则使用原始值
                else:
                    merged[key] = env_value
            else:
                # 环境变量不存在则使用原始值
                merged[key] = value
    
    return merged


def load_config() -> AppConfig:
    """加载配置（主函数）
    
    Returns:
        配置对象
        
    Raises:
        Exception: 配置加载失败
    """
    try:
        config_path = get_var("CONFIG_FILE", "conf/app.yml")
        log.info(f"正在加载配置文件: {config_path}")
        
        # 读取 YAML 配置
        config_dict = read_yaml_file(config_path)
        if config_dict is None:
            config_dict = {}
        
        # 合并环境变量
        merged_config = merge_config(config_dict)
        
        # 创建配置对象
        return AppConfig(merged_config)
        
    except FileNotFoundError as e:
        log.error(f"配置文件不存在: {e}")
        log.info("使用空配置和环境变量初始化...")
        # 文件不存在时使用空配置，所有值从环境变量获取
        return AppConfig({})
        
    except yaml.YAMLError as e:
        log.error(f"YAML 格式错误: {e}")
        raise RuntimeError(f"配置文件格式错误: {e}")
        
    except IOError as e:
        log.error(f"文件读取错误: {e}")
        raise RuntimeError(f"配置文件读取失败: {e}")
        
    except Exception as e:
        log.error(f"配置加载失败: {e}")
        raise RuntimeError(f"配置加载失败: {e}")


if __name__ == "__main__":
    try:
        config = load_config()
        print("配置加载成功!")
        print("\n配置内容:")
        print(config)
        
        # 测试访问方式
        print("\n测试访问方式:")
        # 属性访问
        if hasattr(config, "server"):
            print(f"服务器端口 (属性访问): {config.server.port}")
        # 字典访问
        print(f"服务器端口 (字典访问): {config['server.port']}")
        # get 方法
        print(f"服务器主机 (get方法): {config.get('server.host', 'localhost')}")
        # 环境变量回退
        print(f"环境变量测试: {config.get('test_env_var', '默认值')}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        sys.exit(1)
