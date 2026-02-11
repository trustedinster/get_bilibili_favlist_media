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


class QRCodeLogin:
    """
    二维码登录类
    """

    def __init__(self, wait_forever: bool = False):
        """
        初始化二维码登录

        Args:
            wait_forever (bool): 是否一直等待直到二维码过期
        """
        self.wait_forever = wait_forever
        self.qr_key = None
        self.credential = None

    async def generate_qr_code(self) -> str:
        """
        生成二维码

        Returns:
            str: 二维码链接
        """
        api = API["qrcode"]["web"]["get_qrcode_and_token"]
        response = await Api(credential=Credential(), **api).result()

        # 提取数据
        data = response.get('data', response)
        qr_link = data.get("url") or data.get("data", {}).get("url")
        self.qr_key = data.get("qrcode_key") or data.get("data", {}).get("qrcode_key")

        if not qr_link or not self.qr_key:
            raise Exception(f"无法提取二维码信息: {data}")

        return qr_link

    def display_qr_code(self, qr_link: str):
        """
        显示二维码

        Args:
            qr_link (str): 二维码链接
        """
        qr = qrcode.QRCode()
        qr.add_data(qr_link)
        qr.print_ascii()
        print("请使用手机 Bilibili App 扫描二维码登录")

    async def check_login_status(self) -> dict:
        """
        检查登录状态

        Returns:
            dict: 登录状态信息
        """
        check_api = API["qrcode"]["web"]["get_events"]
        params = {"qrcode_key": self.qr_key}
        response = await Api(credential=Credential(), **check_api).update_params(**params).result()

        return response.get('data', response)

    def parse_credential(self, events: dict) -> Credential:
        """
        解析登录凭据

        Args:
            events (dict): 登录事件数据

        Returns:
            Credential: 登录凭据
        """
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
    async def auto_login(self):
        # 生成并显示二维码
        qr_link = await self.generate_qr_code()
        self.display_qr_code(qr_link)
        return await self.login(qr_link=qr_link)

    async def login(self, qr_link: str = None) -> Credential:
        """
        执行登录流程

        Returns:
            Credential: 登录凭据
        """
        # 轮询检查登录状态
        max_attempts = float('inf') if self.wait_forever else 100
        attempt = 0

        while attempt < max_attempts:
            await asyncio.sleep(3)
            attempt += 1

            events = await self.check_login_status()
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
                self.credential = self.parse_credential(events)
                return self.credential

        raise Exception("超过最大等待次数，登录超时")
