"""
minimal_bilibili_api.audio

音频相关功能
"""

from typing import Union
from .utils.utils import get_api
from .utils.network import Api, Credential


API = get_api("audio")


class Audio:
    """
    音频类
    """

    def __init__(self, auid: int, credential: Credential = None):
        """
        Args:
            auid (int): 音频 AU 号
            credential (Credential): 凭据
        """
        self.auid = auid
        self.credential = credential if credential else Credential()

    async def get_info(self) -> dict:
        """
        获取音频信息
        
        Returns:
            dict: 音频信息
        """
        api = API["audio_info"]["info"]
        params = {"sid": self.auid}
        return await Api(**api, credential=self.credential).update_params(**params).result

    async def get_download_url(self) -> dict:
        """
        获取音频下载链接
        
        Returns:
            dict: 下载链接信息
        """
        api = API["audio_info"]["download_url"]
        params = {"sid": self.auid, "privilege": 2, "quality": 2}
        return await Api(**api, credential=self.credential).update_params(**params).result


async def get_audio_download_url(auid: int, credential: Credential = None) -> dict:
    """
    获取音频下载链接
    
    Args:
        auid (int): 音频 AU 号
        credential (Credential): 凭据
        
    Returns:
        dict: 下载链接信息
    """
    api = API["audio_info"]["download_url"]
    params = {"sid": auid, "privilege": 2, "quality": 2}
    return await Api(**api, credential=credential).update_params(**params).result