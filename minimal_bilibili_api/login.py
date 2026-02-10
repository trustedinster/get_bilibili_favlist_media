"""
minimal_bilibili_api.login

登录相关功能
"""

import json
import time
import asyncio
import qrcode
import qrcode_terminal
from typing import Union
from .utils.utils import get_api
from .utils.network import Api, Credential


API = get_api("login")


class QrCodeLoginEvents:
    """
    二维码登录状态枚举
    """
    SCAN = "scan"
    CONF = "confirm" 
    TIMEOUT = "timeout"
    DONE = "done"


async def login_with_qr(wait_forever: bool = False) -> Credential:
    """
    二维码登录
    
    Args:
        wait_forever (bool): 是否一直等待直到二维码过期，默认 False
    
    Returns:
        Credential: 登录凭据
    """
    # 获取二维码
    api = API["qrcode"]["web"]["get_qrcode_and_token"]
    response = await Api(credential=Credential(), **api).result()
    
    # 检查响应结构
    print(f"API 响应: {response}")
    
    # 根据实际响应结构调整数据提取
    if isinstance(response, dict):
        if 'data' in response:
            data = response['data']
        else:
            data = response
    else:
        raise Exception(f"意外的响应格式: {response}")
    
    # 提取二维码信息
    qr_link = data.get("url") or data.get("data", {}).get("url")
    qr_key = data.get("qrcode_key") or data.get("data", {}).get("qrcode_key")
    
    if not qr_link or not qr_key:
        raise Exception(f"无法从响应中提取二维码信息: {data}")
    
    # 显示二维码
    qr = qrcode.QRCode()
    qr.add_data(qr_link)
    qr.print_ascii()
    print("请使用手机 Bilibili App 扫描二维码登录")
    
    # 轮询检查登录状态
    max_attempts = float('inf') if wait_forever else 100  # 无限次或限制次数
    attempt = 0
    
    while attempt < max_attempts:
        await asyncio.sleep(3)
        attempt += 1
        
        check_api = API["qrcode"]["web"]["get_events"]
        params = {"qrcode_key": qr_key}
        response = await Api(credential=Credential(), **check_api).update_params(**params).result()
        
        # 检查响应结构
        if isinstance(response, dict):
            if 'data' in response:
                events = response['data']
            else:
                events = response
        else:
            events = response
            
        code = events.get("code", events.get("data", {}).get("code"))
        if code == 86101:  # 未扫描
            print(f"等待扫描... (尝试 {attempt})")
            continue
        elif code == 86090:  # 未确认
            print("已扫描，请在手机上确认登录")
            continue
        elif code == 86038:  # 超时
            raise Exception("二维码已过期")
        else:  # 登录成功
            # 提取登录信息
            cred_url = events.get("url") or events.get("data", {}).get("url")
            ac_time_value = events.get("refresh_token") or events.get("data", {}).get("refresh_token")
            
            if not cred_url:
                raise Exception(f"无法获取登录凭证URL: {events}")
            
            # 解析 cookies
            cookies_list = cred_url.split("?")[1].split("&")
            sessdata = ""
            bili_jct = ""
            dedeuserid = ""
            
            for cookie in cookies_list:
                if cookie.startswith("SESSDATA="):
                    sessdata = cookie[9:]
                elif cookie.startswith("bili_jct="):
                    bili_jct = cookie[9:]
                elif cookie.startswith("DedeUserID="):
                    dedeuserid = cookie[11:]
                    
            return Credential(
                sessdata=sessdata,
                bili_jct=bili_jct,
                dedeuserid=dedeuserid,
                ac_time_value=ac_time_value
            )
    
    # 如果达到最大尝试次数仍未登录成功
    raise Exception("超过最大等待次数，登录超时")


async def login_with_password(username: str, password: str) -> Credential:
    """
    密码登录（需要处理验证码）
    
    Args:
        username (str): 用户名/手机号
        password (str): 密码
        
    Returns:
        Credential: 登录凭据
        
    Note: 此方法需要处理极验验证码，建议使用二维码登录
    """
    raise NotImplementedError("密码登录需要处理验证码，建议使用二维码登录")


async def login_with_sms(phone: str, code: str) -> Credential:
    """
    短信验证码登录
    
    Args:
        phone (str): 手机号
        code (str): 短信验证码
        
    Returns:
        Credential: 登录凭据
        
    Note: 需要先调用发送短信接口
    """
    raise NotImplementedError("短信登录需要先发送验证码")