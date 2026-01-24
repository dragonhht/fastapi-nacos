"""
项目配置文件解析工具
"""

import os
import sys
import yaml
import re
from fastapi_nacos.utils.env_utils import get_var
from typing import Dict, Any, Union

# 环境变量引用正则表达式: ${ENV_VAR:default_value}
ENV_VAR_PATTERN = re.compile(r'\$\{([^:}]+)(?::([^}]*))?\}')

# 配置参数引用正则表达式: ${config.key}
CONFIG_VAR_PATTERN = re.compile(r'\$\{([a-zA-Z0-9_.]+)\}')


def substitute_env_vars(value: Union[str, Dict[str, Any], Any], config_dict: Dict[str, Any] = None) -> Union[str, Dict[str, Any], Any]:
    """递归替换字符串中的环境变量引用和配置参数引用
    
    Args:
        value: 要处理的值，可以是字符串、字典或其他类型
        config_dict: 配置字典，用于解析配置参数引用
        
    Returns:
        替换后的对应值
    """
    if isinstance(value, str):
        # 首先替换配置参数引用
        def replace_config_match(match: re.Match) -> str:
            config_key = match.group(1)
            if config_dict is not None:
                # 从配置字典中查找对应的值
                if config_key in config_dict:
                    # 直接查找扁平化的键
                    return str(config_dict[config_key])
                else:
                    # 如果路径不存在，返回原字符串
                    return match.group(0)
            else:
                # 如果没有配置字典，返回原字符串
                return match.group(0)
        
        # 替换配置参数引用
        result = CONFIG_VAR_PATTERN.sub(replace_config_match, value)
        
        # 然后替换环境变量引用
        def replace_env_match(match: re.Match) -> str:
            env_var = match.group(1)
            default = match.group(2) or ''
            return get_var(env_var, default)
        
        return ENV_VAR_PATTERN.sub(replace_env_match, result)
    elif isinstance(value, dict):
        # 递归处理字典
        return {
            key: substitute_env_vars(val, config_dict)
            for key, val in value.items()
        }
    elif isinstance(value, list):
        # 递归处理列表
        return [substitute_env_vars(item, config_dict) for item in value]
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

def parse_yaml_content(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """解析 YAML 内容
    
    Args:
        config_dict: 包含 YAML 内容的字典
        
    Returns:
        解析后的配置字典
    """
    # Process the config with multiple iterations to handle dependencies
    max_iterations = 10
    current_config = config_dict
    
    for iteration in range(max_iterations):
        # Create a flat lookup of the current config state
        def create_flat_lookup(cfg, prefix=''):
            lookup = {}
            for k, v in cfg.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    lookup.update(create_flat_lookup(v, full_key))
                elif isinstance(v, list):
                    # Store the list as-is
                    lookup[full_key] = v
                else:
                    lookup[full_key] = v
            return lookup
        
        flat_lookup = create_flat_lookup(current_config)
        
        # Process the config with the current flat lookup
        def process_recursive(obj):
            if isinstance(obj, str):
                return substitute_env_vars(obj, flat_lookup)
            elif isinstance(obj, dict):
                return {k: process_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [process_recursive(item) for item in obj]
            else:
                return obj
        
        new_config = process_recursive(current_config)
        
        # If no changes, we're done
        if new_config == current_config:
            break
            
        current_config = new_config
    
    return current_config

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
            # 解析 YAML 内容
            return parse_yaml_content(config_dict)
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
        startup_file = os.path.abspath(sys.argv[0])
        root_dir = os.path.dirname(startup_file)
        config_path = get_var("FASTAPI_NACOS_CONFIG_FILE", os.path.join(root_dir, "conf", "app.yml"))
        print(f"正在加载配置文件: {config_path}")
        
        # 读取 YAML 配置
        config_dict = read_yaml_file(config_path)
        if config_dict is None:
            config_dict = {}
        
        # 合并环境变量
        # merged_config = merge_config(config_dict)
        
        # 创建配置对象
        return AppConfig(config_dict)
        
    except FileNotFoundError as e:
        print(f"配置文件不存在: {e}")
        print("使用空配置和环境变量初始化...")
        # 文件不存在时使用空配置，所有值从环境变量获取
        return AppConfig({})
        
    except yaml.YAMLError as e:
        print(f"YAML 格式错误: {e}")
        raise RuntimeError(f"配置文件格式错误: {e}")
        
    except IOError as e:
        print(f"文件读取错误: {e}")
        raise RuntimeError(f"配置文件读取失败: {e}")
        
    except Exception as e:
        print(f"配置加载失败: {e}")
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
