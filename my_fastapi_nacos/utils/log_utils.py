import sys, os
from loguru import logger
from my_fastapi_nacos.config import app_config

# 获取当前项目的绝对路径
startup_file = os.path.abspath(sys.argv[0])
root_dir = os.path.dirname(startup_file)

# 从配置中获取日志级别
log_level = app_config.get("logging.level", "DEBUG")
log_file = app_config.get("logging.file", os.path.join(root_dir, "logs", "app.log"))

# 处理相对路径和绝对路径
if log_file and not os.path.isabs(log_file):
    log_file = os.path.join(root_dir, log_file)

log_dir = os.path.dirname(log_file)
if log_dir:  # 避免空路径
    os.makedirs(log_dir, exist_ok=True)

class MyLogger:
  def __init__(self):
    self.logger = logger
    # 清空所有配置
    self.logger.remove()
    # 添加控制台输出格式
    self.logger.add(sys.stdout, level=log_level,
      format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
              "{process.name} | " # 进程名
              "{thread.name} | " # 线程名
              "<level>{level}</level> | "
              "<cyan>{module}</cyan>.<cyan>{function}</cyan>" # 模块名.方法名
              ":<cyan>{line}</cyan>: " # 行号
              "- <level>{message}</level>" # 日志内容
    )

    # 输出到文件的格式
    self.logger.add(
      log_file,
      level=log_level,
      rotation="100 MB", # 每个日志文件最大100MB
      retention="10 days", # 保留10天的日志文件
      encoding="utf-8",
      format="{time:YYYY-MM-DD HH:mm:ss} | "
              "{process.name} | " # 进程名
              "{thread.name} | " # 线程名
              "{level} | "
              "{module}.{function}" # 模块名.方法名
              ":{line}: " # 行号
              "- {message}" # 日志内容
    )

  def get_logger(self):
    return self.logger

log = MyLogger().get_logger()