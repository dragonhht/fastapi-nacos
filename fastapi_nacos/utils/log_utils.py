import sys, os
from loguru import logger

# 获取当前项目的绝对路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(root_dir, "logs")
log_level = "DEBUG"

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

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
      log_dir + "/app.log",
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