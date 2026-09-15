# src/app/clients/studentmanage_v2/security.py
"""
密码加密工具 - argon2 版本
"""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# 导入日志
"""
    import logging
    from ....framework.ai.aicompanion_v2.logging_config import setup_logging
    setup_logging()
    logger = logging.getLogger(__name__)
"""
# ============================================================
# argon2 配置
# ============================================================
ph = PasswordHasher(
    time_cost=3,           # 迭代次数（默认 3）
    memory_cost=65536,     # 内存开销，单位 KB（默认 64MB）
    parallelism=4,         # 并行度（默认 4）
    hash_len=32,           # 哈希长度（默认 32 字节）
    salt_len=16,           # 盐长度（默认 16 字节）
)
def hash_password(password:str ) -> str:
    """
    加密密码
    
    返回格式：$argon2id$v=19$m=65536,t=3,p=4$...盐...$...哈希...
    """
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Returns:
        True 表示密码正确
    """
    try:
        ph.verify(hashed_password, plain_password)
        #logger.info(hashed_password)
        return True
    except VerifyMismatchError:
        return False
    except Exception as e:
        logger.exception(f"密码验证失败:{e}")
        return False

def needs_rehash(hashed_password: str) -> bool:
    """
    检查哈希是否需要重新计算（参数升级后）
    """
    return ph.check_needs_rehash(hashed_password)