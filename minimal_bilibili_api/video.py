"""
minimal_bilibili_api.video

视频相关功能
"""

import re
from typing import Union, List, Optional
from dataclasses import dataclass
from enum import Enum
from .utils.utils import get_api
from .utils.network import Api, Credential, get_client, HEADERS


API = get_api("video")


class AudioQuality(Enum):
    """
    音频质量枚举
    """
    _64K = 30216
    _132K = 30232
    _192K = 30280
    HI_RES = 30251
    DOLBY = 30255
    
    def __le__(self, other):
        """支持 <= 比较操作"""
        if isinstance(other, AudioQuality):
            # 按照音质从低到高排序：64K < 132K < 192K < HI_RES < DOLBY
            quality_order = [
                AudioQuality._64K,
                AudioQuality._132K, 
                AudioQuality._192K,
                AudioQuality.HI_RES,
                AudioQuality.DOLBY
            ]
            return quality_order.index(self) <= quality_order.index(other)
        return NotImplemented
    
    def __lt__(self, other):
        """支持 < 比较操作"""
        if isinstance(other, AudioQuality):
            quality_order = [
                AudioQuality._64K,
                AudioQuality._132K,
                AudioQuality._192K,
                AudioQuality.HI_RES,
                AudioQuality.DOLBY
            ]
            return quality_order.index(self) < quality_order.index(other)
        return NotImplemented


@dataclass
class AudioStream:
    """
    音频流信息
    """
    url: str
    quality: AudioQuality

    def __str__(self):
        return f"AudioStream(url='{self.url}', quality={self.quality.name})"


@dataclass
class VideoStream:
    """
    视频流信息
    """
    url: str
    quality: str

    def __str__(self):
        return f"VideoStream(url='{self.url}', quality={self.quality})"


class VideoDownloadParser:
    """
    视频下载链接解析器
    """

    def __init__(self, data: dict):
        self.data = data
        # 处理可能的包装格式
        if "data" in self.data:
            self.data = self.data["data"]
        if self.data.get("video_info"):  # bangumi
            self.data = self.data["video_info"]

    def is_dash_stream(self) -> bool:
        """
        判断是否为 DASH 流（音视频分离）
        """
        return "dash" in self.data

    def is_flv_stream(self) -> bool:
        """
        判断是否为 FLV 流
        """
        return "durl" in self.data and self.data.get("format", "").startswith("flv")

    def get_audio_streams(self) -> List[AudioStream]:
        """
        获取所有音频流
        """
        if not self.is_dash_stream():
            return []

        streams = []
        dash_data = self.data["dash"]

        # 普通音频流
        if "audio" in dash_data:
            for audio_data in dash_data["audio"]:
                url = audio_data.get("baseUrl") or audio_data.get("base_url", "")
                if url:
                    quality = AudioQuality(audio_data["id"])
                    streams.append(AudioStream(url=url, quality=quality))

        # Hi-Res 音频
        if "flac" in dash_data and dash_data["flac"]:
            flac_data = dash_data["flac"]
            if "audio" in flac_data:
                url = flac_data["audio"].get("base_url", "")
                if url:
                    quality = AudioQuality.HI_RES
                    streams.append(AudioStream(url=url, quality=quality))

        # 杜比音频
        if "dolby" in dash_data and dash_data["dolby"]:
            dolby_data = dash_data["dolby"]
            if "audio" in dolby_data and dolby_data["audio"]:
                for audio_data in dolby_data["audio"]:
                    url = audio_data.get("base_url", "")
                    if url:
                        quality = AudioQuality.DOLBY
                        streams.append(AudioStream(url=url, quality=quality))

        return streams

    def get_video_streams(self) -> List[VideoStream]:
        """
        获取所有视频流
        """
        if not self.is_dash_stream():
            return []

        streams = []
        dash_data = self.data["dash"]

        if "video" in dash_data:
            for video_data in dash_data["video"]:
                url = video_data.get("baseUrl") or video_data.get("base_url", "")
                if url:
                    quality_id = video_data["id"]
                    # 简单的质量映射
                    quality_map = {
                        16: "360P", 32: "480P", 64: "720P",
                        80: "1080P", 112: "1080P+", 116: "1080P60",
                        120: "4K", 125: "HDR", 126: "杜比视界", 127: "8K"
                    }
                    quality = quality_map.get(quality_id, f"Quality_{quality_id}")
                    streams.append(VideoStream(url=url, quality=quality))

        return streams

    def get_best_audio_stream(self, max_quality: AudioQuality = AudioQuality.DOLBY) -> Optional[AudioStream]:
        """
        获取最佳音频流（优先级：杜比 > Hi-Res > 192K > 132K > 64K）
        """
        streams = self.get_audio_streams()
        if not streams:
            return None

        # 按优先级排序
        priority_order = [
            AudioQuality.DOLBY,
            AudioQuality.HI_RES,
            AudioQuality._192K,
            AudioQuality._132K,
            AudioQuality._64K
        ]

        for quality in priority_order:
            for stream in streams:
                if stream.quality == quality and quality <= max_quality:
                    return stream

        return streams[0] if streams else None

    def get_flv_stream(self) -> Optional[VideoStream]:
        """
        获取 FLV 流
        """
        if not self.is_flv_stream():
            return None

        url = self.data["durl"][0].get("url", "")
        return VideoStream(url=url, quality="FLV") if url else None


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

        # 分步调用避免链式调用问题
        api_instance = Api(**api, credential=self.credential)
        api_instance.update_params(**params)
        return await api_instance.result()

    async def get_title(self) -> str:
        """
        获取视频标题

        Returns:
            str: 视频标题
        """
        info = await self.get_info()
        return info.get("data", {}).get("title", "") if "data" in info else info.get("title", "")

    async def get_download_url(self, page_index: int = 0) -> dict:
        """
        获取视频下载链接

        Args:
            page_index (int): 分 P 索引，默认为 0

        Returns:
            dict: 下载链接信息
        """
        # 先获取分 P 信息
        pages_api = API["info"]["pages"]
        pages_params = {}
        if self.bvid:
            pages_params["bvid"] = self.bvid
        if self.aid:
            pages_params["aid"] = self.aid

        api_instance = Api(**pages_api, credential=self.credential)
        api_instance.update_params(**pages_params)
        pages_result = await api_instance.result()
        pages = pages_result.get("data", []) if "data" in pages_result else pages_result

        if page_index >= len(pages):
            raise Exception(f"分 P 索引超出范围，共有 {len(pages)} 个分 P")

        cid = pages[page_index]["cid"]

        # 获取下载链接
        playurl_api = API["info"]["playurl"]
        playurl_params = {
            "qn": "127",  # 最高质量
            "fnval": 4048,  # 支持所有格式
            "fnver": 0,
            "fourk": 1,
            "avid": self.aid,
            "bvid": self.bvid,
            "cid": cid
        }

        api_instance = Api(**playurl_api, credential=self.credential, wbi=True)
        api_instance.update_params(**playurl_params)
        return await api_instance.result()

    async def get_audio_streams(self, page_index: int = 0) -> List[AudioStream]:
        """
        获取音频流列表

        Args:
            page_index (int): 分 P 索引，默认为 0

        Returns:
            List[AudioStream]: 音频流列表
        """
        download_data = await self.get_download_url(page_index)
        parser = VideoDownloadParser(download_data)
        return parser.get_audio_streams()

    async def get_best_audio_stream(self, page_index: int = 0) -> Optional[AudioStream]:
        """
        获取最佳音频流

        Args:
            page_index (int): 分 P 索引，默认为 0

        Returns:
            AudioStream: 最佳音频流
        """
        download_data = await self.get_download_url(page_index)
        parser = VideoDownloadParser(download_data)
        return parser.get_best_audio_stream()

    async def download_audio_to_dir(self, download_dir: str = "./downloads",
                                  page_index: int = 0,
                                  quality: str = None,
                                  filename: str = None,
                                  progress_callback=None) -> str:
        """
        下载音频到指定目录

        Args:
            download_dir (str): 下载目录
            page_index (int): 分 P 索引
            quality (str): 指定音质
            filename (str): 自定义文件名
            progress_callback: 进度回调函数

        Returns:
            str: 下载文件路径
        """
        from .downloader import VideoDownloader, ProgressCallback

        downloader = VideoDownloader(self, download_dir)
        progress_cb = ProgressCallback(progress_callback) if progress_callback else None

        return await downloader.download_audio(
            page_index=page_index,
            quality=quality,
            filename=filename,
            progress_callback=progress_cb
        )


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
