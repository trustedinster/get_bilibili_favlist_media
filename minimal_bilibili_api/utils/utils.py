"""
minimal_bilibili_api.utils.utils

精简版通用工具库
"""

import json
import os
from typing import List, TypeVar


def get_api(field: str, *args) -> dict:
    """
    获取 API 配置
    
    Args:
        field (str): API 所属分类
        
    Returns:
        dict: API 配置
    """
    path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "data", "api", f"{field.lower()}.json"
        )
    )
    if os.path.exists(path):
        with open(path, encoding="utf8") as f:
            data = json.load(f)
            for arg in args:
                data = data[arg]
            return data
    else:
        return {}


def join(seperator: str, array: list):
    """
    用指定字符连接数组
    
    Args:
        seperator (str): 分隔字符
        array (list): 数组
        
    Returns:
        str: 连接结果
    """
    return seperator.join(map(lambda x: str(x), array))


def raise_for_statement(statement: bool, msg: str = "未满足条件") -> None:
    if not statement:
        raise Exception(msg)