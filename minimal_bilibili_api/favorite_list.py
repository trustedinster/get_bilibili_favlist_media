"""
minimal_bilibili_api.favorite_list

收藏夹相关功能
"""

from enum import Enum
from typing import List, Union, Optional
from .utils.utils import get_api
from .utils.network import Api, Credential


API = get_api("favorite-list")


class FavoriteListContentOrder(Enum):
    """
    收藏夹内容排序方式
    """
    MTIME = "mtime"   # 最近收藏
    VIEW = "view"     # 最多播放
    PUBTIME = "pubtime"  # 最新投稿


class FavoriteList:
    """
    收藏夹类
    """

    def __init__(self, media_id: int, credential: Credential = None):
        """
        Args:
            media_id (int): 收藏夹 ID
            credential (Credential): 凭据
        """
        self.media_id = media_id
        self.credential = credential if credential else Credential()

    async def get_info(self) -> dict:
        """
        获取收藏夹信息

        Returns:
            dict: 收藏夹信息
        """
        api = API["info"]["info"]
        params = {"media_id": self.media_id}
        return await Api(**api, credential=self.credential).update_params(**params).result()

    async def get_content(
        self,
        page: int = 1,
        keyword: str = None,
        order: FavoriteListContentOrder = FavoriteListContentOrder.MTIME
    ) -> dict:
        """
        获取收藏夹内容

        Args:
            page (int): 页码
            keyword (str): 搜索关键词
            order (FavoriteListContentOrder): 排序方式

        Returns:
            dict: 收藏夹内容
        """
        return await get_video_favorite_list_content(
            media_id=self.media_id,
            page=page,
            keyword=keyword,
            order=order,
            credential=self.credential
        )


async def get_video_favorite_list(
    uid: int,
    credential: Credential = None
) -> dict:
    """
    获取用户的视频收藏夹列表

    Args:
        uid (int): 用户 UID
        credential (Credential): 凭据

    Returns:
        dict: 收藏夹列表
    """
    api = API["info"]["list_list"]
    params = {"up_mid": uid, "type": 2}
    return await Api(**api, credential=credential).update_params(**params).result()


async def get_video_favorite_list_content(
    media_id: int,
    page: int = 1,
    keyword: str = None,
    order: FavoriteListContentOrder = FavoriteListContentOrder.MTIME,
    credential: Credential = None
) -> dict:
    """
    获取视频收藏夹内容

    Args:
        media_id (int): 收藏夹 ID
        page (int): 页码
        keyword (str): 搜索关键词
        order (FavoriteListContentOrder): 排序方式
        credential (Credential): 凭据

    Returns:
        dict: 收藏夹内容
    """
    api = API["info"]["list_content"]
    params = {
        "media_id": media_id,
        "pn": page,
        "ps": 20,
        "order": order.value,
        "type": 0,
        "tid": 0
    }

    if keyword:
        params["keyword"] = keyword

    return await Api(**api, credential=credential).update_params(**params).result()
