"""
minimal_bilibili_api

精简版哔哩哔哩 API，仅保留登录、收藏夹、音频下载、视频标题功能
"""

from .utils.network import Credential, Api
from .login import login_with_qr, login_with_password, login_with_sms
from .favorite_list import FavoriteList, get_video_favorite_list, get_video_favorite_list_content
from .audio import Audio, get_audio_download_url
from .video import Video, get_video_title

__version__ = "1.0.0"

__all__ = [
    "Credential",
    "Api", 
    "login_with_qr",
    "login_with_password", 
    "login_with_sms",
    "FavoriteList",
    "get_video_favorite_list",
    "get_video_favorite_list_content", 
    "Audio",
    "get_audio_download_url",
    "Video",
    "get_video_title"
]