import socket
from fastapi_nacos.utils.log_utils import log

def get_ip_address(prefer_internal: bool = True) -> str:
        """
        获取IP地址
        
        Args:
            prefer_internal: 是否优先获取内网IP
            
        Returns:
            IP地址字符串
        """
        try:
            if prefer_internal:
                # 获取内网IP
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(('8.8.8.8', 53))
                    ip = s.getsockname()[0]
                    s.close()
                    log.info(f"获取到内网IP: {ip}")
                    return ip
                except Exception as e:
                    log.warning(f"获取内网IP失败: {e}")
            
            # 方法2：获取所有IP，排除回环地址
            hostname = socket.gethostname()
            addrs = socket.getaddrinfo(hostname, None)
            
            for addr in addrs:
                ip = addr[4][0]
                # 只返回IPv4地址，排除回环地址
                if ':' not in ip and not ip.startswith('127.'):
                    log.info(f"从主机名获取到IP: {ip}")
                    return ip
            
            # 方法3：回退到本地回环地址
            log.warning("无法获取IP地址，使用127.0.0.1")
            return "127.0.0.1"
            
        except Exception as e:
            log.error(f"获取IP地址时发生错误: {e}")
            return "127.0.0.1"