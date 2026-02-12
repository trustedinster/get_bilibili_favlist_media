"""
minimal_bilibili_api.downloader

精简版下载管理器，支持单文件和批量下载
"""

import os
import asyncio
from pathlib import Path
from typing import List, Optional, Callable, Union
from dataclasses import dataclass
from urllib.parse import urlparse
import time

from .utils.network import get_client, HEADERS
from .video import Video, AudioStream


@dataclass
class DownloadTask:
    """下载任务"""
    url: str
    filepath: str
    filename: str
    total_size: int = 0
    downloaded: int = 0
    status: str = "pending"  # pending, downloading, completed, failed
    error: Optional[str] = None


class ProgressCallback:
    """进度回调接口"""
    
    def __init__(self, callback: Callable[[DownloadTask], None] = None):
        self.callback = callback
    
    def __call__(self, task: DownloadTask):
        if self.callback:
            self.callback(task)


class Downloader:
    """精简下载管理器"""
    
    def __init__(self, max_concurrent: int = 3):
        """
        Args:
            max_concurrent (int): 最大并发下载数
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.client = get_client()
    
    async def download_single(self, url: str, filepath: str, 
                            progress_callback: Optional[ProgressCallback] = None) -> bool:
        """
        下载单个文件
        
        Args:
            url (str): 下载链接
            filepath (str): 保存路径
            progress_callback (ProgressCallback): 进度回调
            
        Returns:
            bool: 是否成功
        """
        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        task = DownloadTask(
            url=url,
            filepath=filepath,
            filename=Path(filepath).name
        )
        
        try:
            task.status = "downloading"
            if progress_callback:
                progress_callback(task)
            
            # 创建下载任务
            dwn_id = await self.client.download_create(url, HEADERS)
            
            # 获取文件大小
            task.total_size = self.client.download_content_length(dwn_id)
            
            # 写入文件
            with open(filepath, "wb") as f:
                while True:
                    chunk = await self.client.download_chunk(dwn_id)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    task.downloaded += len(chunk)
                    
                    if progress_callback:
                        progress_callback(task)
            
            await self.client.download_close(dwn_id)
            task.status = "completed"
            
            if progress_callback:
                progress_callback(task)
                
            return True
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            if progress_callback:
                progress_callback(task)
            return False
    
    async def download_batch(self, tasks: List[tuple], 
                           progress_callback: Optional[ProgressCallback] = None) -> List[bool]:
        """
        批量下载
        
        Args:
            tasks (List[tuple]): [(url, filepath), ...] 下载任务列表
            progress_callback (ProgressCallback): 进度回调
            
        Returns:
            List[bool]: 每个任务的成功状态
        """
        async def download_wrapper(task_tuple):
            url, filepath = task_tuple
            async with self.semaphore:
                return await self.download_single(url, filepath, progress_callback)
        
        # 并发执行所有下载任务
        results = await asyncio.gather(*[download_wrapper(task) for task in tasks])
        return results


class VideoDownloader:
    """视频专用下载器"""
    
    def __init__(self, video: Video, download_dir: str = "./downloads"):
        """
        Args:
            video (Video): 视频对象
            download_dir (str): 下载目录
        """
        self.video = video
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.downloader = Downloader()
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
    
    async def download_audio(self, page_index: int = 0, 
                           quality: Optional[str] = None,
                           filename: Optional[str] = None,
                           progress_callback: Optional[ProgressCallback] = None) -> str:
        """
        下载音频
        
        Args:
            page_index (int): 分P索引
            quality (str): 指定音质 ('64K', '132K', '192K', 'HI_RES', 'DOLBY')
            filename (str): 自定义文件名
            progress_callback (ProgressCallback): 进度回调
            
        Returns:
            str: 下载文件路径
        """
        # 获取音频流
        if quality:
            audio_streams = await self.video.get_audio_streams(page_index)
            target_stream = None
            for stream in audio_streams:
                if stream.quality.name == quality:
                    target_stream = stream
                    break
            if not target_stream:
                raise Exception(f"未找到指定音质: {quality}")
        else:
            target_stream = await self.video.get_best_audio_stream(page_index)
            if not target_stream:
                raise Exception("未找到可用的音频流")
        
        # 生成文件名
        if not filename:
            title = await self.video.get_title()
            clean_title = self.sanitize_filename(title)
            filename = f"{clean_title}_p{page_index+1}_{target_stream.quality.name}.m4a"
        
        filepath = str(self.download_dir / filename)
        
        # 下载
        success = await self.downloader.download_single(
            target_stream.url, filepath, progress_callback
        )
        
        if not success:
            raise Exception("下载失败")
            
        return filepath
    
    async def download_video(self, page_index: int = 0,
                           quality: Optional[str] = None,
                           filename: Optional[str] = None,
                           progress_callback: Optional[ProgressCallback] = None) -> str:
        """
        下载视频（暂未实现完整功能）
        """
        raise NotImplementedError("视频下载功能待完善")


class FavoriteListDownloader:
    """收藏夹批量下载器"""
    
    def __init__(self, fav_list, download_dir: str = "./downloads"):
        """
        Args:
            fav_list: 收藏夹对象
            download_dir (str): 下载目录
        """
        self.fav_list = fav_list
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.downloader = Downloader()
        self.video_downloader_class = VideoDownloader
    
    async def download_all_audios(self, 
                                max_videos: Optional[int] = None,
                                quality: Optional[str] = None,
                                progress_callback: Optional[Callable[[int, int, str], None]] = None) -> dict:
        """
        下载收藏夹中所有视频的音频
        
        Args:
            max_videos (int): 最大下载视频数
            quality (str): 音质
            progress_callback (Callable[[int, int, str], None]): 进度回调
            
        Returns:
            dict: {media_id: filepath}
        """
        results = {}
        videos = await self.fav_list.get_videos()
        total_videos = len(videos)
        if max_videos:
            total_videos = min(total_videos, max_videos)
        
        for i, video in enumerate(videos[:total_videos]):
            media_id = video.media_id
            video_downloader = self.video_downloader_class(video, self.download_dir)
            try:
                filepath = await video_downloader.download_audio(
                    quality=quality,
                    progress_callback=progress_callback
                )
                results[media_id] = filepath
            except Exception as e:
                results[media_id] = str(e)
            
            if progress_callback:
                progress_callback(i+1, total_videos, filepath)
        
        return results


async def download_favorite_list_audios(media_id: int,
                                      download_dir: str = "./downloads",
                                      max_videos: Optional[int] = None,
                                      quality: Optional[str] = None,
                                      progress_callback: Optional[Callable[[int, int, str], None]] = None) -> dict:
    """
    下载收藏夹中所有视频的音频
    
    Args:
        media_id (int): 收藏夹ID
        download_dir (str): 下载目录
        max_videos (int): 最大下载视频数
        quality (str): 音质
        progress_callback (Callable[[int, int, str], None]): 进度回调
        
    Returns:
        dict: {media_id: filepath}
    """
    from .favorite_list import FavoriteList
    fav_list = FavoriteList(media_id)
    downloader = FavoriteListDownloader(fav_list, download_dir)
    return await downloader.download_all_audios(
        max_videos=max_videos,
        quality=quality,
        progress_callback=progress_callback
    )
