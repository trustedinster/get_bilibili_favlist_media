"""
minimal_bilibili_api.video

视频相关功能
"""

import re
from typing import Union
from .utils.utils import get_api
from .utils.network import Api, Credential


API = get_api("video")


class Video:
    """
    视频类
    """

    def __init__(self, bvid: str = None, aid: int = None, credential: Credential = None):
        """
        Args:
            bvid (str): BV 号
            aid (int): AV 号
            credential (Credential): 凭据
        """
        if bvid:
            self.bvid = bvid
            # 简单的 BV to AV 转换（实际应该更复杂）
            self.aid = int(bvid[2:], 36) if bvid.startswith('BV') else None
        elif aid:
            self.aid = aid
            self.bvid = None
        else:
            raise Exception("必须提供 bvid 或 aid")
            
        self.credential = credential if credential else Credential()

    async def get_info(self) -> dict:
        """
        获取视频完整信息
        
        Returns:
            dict: 视频信息
        """
        api = API["info"]["info"]
        params = {}
        if self.bvid:
            params["bvid"] = self.bvid
        if self.aid:
            params["aid"] = self.aid
            
        return await Api(**api, credential=self.credential).update_params(**params).result

    async def get_title(self) -> str:
        """
        获取视频标题
        
        Returns:
            str: 视频标题
        """
        info = await self.get_info()
        return info.get("data", {}).get("title", "") if "data" in info else info.get("title", "")


async def get_video_title(bvid: str = None, aid: int = None, credential: Credential = None) -> str:
    """
    获取视频标题
    
    Args:
        bvid (str): BV 号
        aid (int): AV 号
        credential (Credential): 凭据
        
    Returns:
        str: 视频标题
    """
    video = Video(bvid=bvid, aid=aid, credential=credential)
    return await video.get_title()