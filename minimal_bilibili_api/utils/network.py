"""
minimal_bilibili_api.utils.network

精简版网络请求模块，仅支持 curl_cffi
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Optional, Union
from dataclasses import dataclass

from curl_cffi import requests


# 默认请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Referer": "https://www.bilibili.com/",
}


class DownloadClient:
    """
    简化的下载客户端
    """
    def __init__(self):
        self.downloads = {}
        self.download_cnt = 0
        
    async def download_create(self, url: str, headers: dict = None) -> int:
        """
        创建下载任务
        """
        if headers is None:
            headers = HEADERS.copy()
        
        self.download_cnt += 1
        session = requests.AsyncSession()
        resp = await session.get(url, headers=headers)
        self.downloads[self.download_cnt] = {
            "response": resp,
            "session": session,
            "content_iter": resp.aiter_bytes()
        }
        return self.download_cnt
    
    async def download_chunk(self, cnt: int) -> bytes:
        """
        下载数据块
        """
        download_info = self.downloads[cnt]
        try:
            # 使用传统的异步迭代方式
            chunk = await download_info["content_iter"].__anext__()
            return chunk
        except StopAsyncIteration:
            return b""
    
    def download_content_length(self, cnt: int) -> int:
        """
        获取下载内容总长度
        """
        resp = self.downloads[cnt]["response"]
        return int(resp.headers.get("content-length", "0"))
    
    async def download_close(self, cnt: int) -> None:
        """
        关闭下载连接
        """
        download_info = self.downloads[cnt]
        await download_info["session"].close()
        del self.downloads[cnt]


def get_client() -> DownloadClient:
    """
    获取下载客户端实例
    """
    # 使用全局单例
    global _download_client
    if _download_client is None:
        _download_client = DownloadClient()
    return _download_client


# 全局下载客户端实例
_download_client = None


@dataclass
class Credential:
    """
    凭据类，用于保存登录信息
    """
    sessdata: str = ""
    bili_jct: str = "" 
    dedeuserid: str = ""
    ac_time_value: str = ""
    buvid3: str = ""

    def has_sessdata(self) -> bool:
        return self.sessdata != ""

    def has_bili_jct(self) -> bool:
        return self.bili_jct != ""

    def has_dedeuserid(self) -> bool:
        return self.dedeuserid != ""

    def raise_for_no_sessdata(self):
        if not self.has_sessdata():
            raise Exception("缺少 SESSDATA")

    def raise_for_no_bili_jct(self):
        if not self.has_bili_jct():
            raise Exception("缺少 bili_jct")

    def raise_for_no_dedeuserid(self):
        if not self.has_dedeuserid():
            raise Exception("缺少 DedeUserID")


@dataclass  
class Api:
    """
    API 请求类
    """
    url: str
    method: str = "GET"
    credential: Optional[Credential] = None
    params: Dict = None
    data: Dict = None
    headers: Dict = None
    wbi: bool = False
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}
        if self.data is None:
            self.data = {}
        if self.headers is None:
            self.headers = {}
            
    def update_params(self, **kwargs):
        self.params.update(kwargs)
        return self
        
    def update_data(self, **kwargs):
        self.data.update(kwargs)
        return self
        
    def update_headers(self, **kwargs):
        self.headers.update(kwargs)
        return self
        
    async def result(self):
        """执行请求并返回结果"""
        # 添加默认 headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com/",
        }
        headers.update(self.headers)
        
        # 添加认证信息
        cookies = {}
        if self.credential:
            if self.credential.sessdata:
                cookies["SESSDATA"] = self.credential.sessdata
            if self.credential.bili_jct:
                cookies["bili_jct"] = self.credential.bili_jct
            if self.credential.dedeuserid:
                cookies["DedeUserID"] = self.credential.dedeuserid
            if self.credential.buvid3:
                cookies["buvid3"] = self.credential.buvid3
                
        # 发起请求
        session = requests.AsyncSession()
        try:
            if self.method.upper() == "GET":
                resp = await session.get(
                    self.url,
                    params=self.params,
                    headers=headers,
                    cookies=cookies
                )
            else:
                resp = await session.post(
                    self.url,
                    params=self.params,
                    data=self.data,
                    headers=headers,
                    cookies=cookies
                )
                
            # 解析响应
            if resp.status_code == 200:
                try:
                    result = resp.json()
                    if isinstance(result, dict) and result.get("code", 0) != 0:
                        raise Exception(f"API 错误: {result.get('message', '未知错误')}")
                    return result
                except json.JSONDecodeError:
                    return resp.text
            else:
                raise Exception(f"HTTP 错误: {resp.status_code}")
        finally:
            await session.close()