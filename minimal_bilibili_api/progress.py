"""
minimal_bilibili_api.progress

精简版下载进度显示工具
"""

import sys
from typing import Optional
from .downloader import DownloadTask


class SimpleProgressDisplay:
    """简单的进度显示"""
    
    def __init__(self, show_speed: bool = True):
        self.show_speed = show_speed
        self.last_time = 0
        self.last_downloaded = 0
    
    def format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f}KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f}MB"
        else:
            return f"{size/(1024*1024*1024):.1f}GB"
    
    def format_speed(self, speed: float) -> str:
        """格式化下载速度"""
        return self.format_size(int(speed)) + "/s"
    
    def display_progress(self, task: DownloadTask):
        """显示下载进度"""
        if task.status == "completed":
            print(f"\r✅ {task.filename} 下载完成 ({self.format_size(task.total_size)})")
            return
        elif task.status == "failed":
            print(f"\r❌ {task.filename} 下载失败: {task.error}")
            return
        elif task.status == "pending":
            print(f"⏳ 准备下载 {task.filename}...")
            return
        
        # 计算进度
        if task.total_size > 0:
            progress = (task.downloaded / task.total_size) * 100
            bar_length = 30
            filled_length = int(bar_length * progress // 100)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            # 计算速度
            speed_str = ""
            if self.show_speed:
                import time
                current_time = time.time()
                if self.last_time > 0:
                    time_diff = current_time - self.last_time
                    if time_diff > 0:
                        speed = (task.downloaded - self.last_downloaded) / time_diff
                        speed_str = f" {self.format_speed(speed)}"
                
                self.last_time = current_time
                self.last_downloaded = task.downloaded
            
            # 显示进度条
            print(f"\r{task.filename} [{bar}] {progress:.1f}% "
                  f"({self.format_size(task.downloaded)}/{self.format_size(task.total_size)}){speed_str}", 
                  end="", flush=True)


class BatchProgressDisplay:
    """批量下载进度显示"""
    
    def __init__(self):
        self.current = 0
        self.total = 0
        self.current_title = ""
    
    def update_progress(self, current: int, total: int, title: str):
        """更新批量下载进度"""
        self.current = current
        self.total = total
        self.current_title = title
        
        # 显示进度
        progress = (current / total) * 100 if total > 0 else 0
        print(f"\r📦 批量下载: {current}/{total} ({progress:.1f}%) - 当前: {title}", 
              end="", flush=True)
    
    def finish(self, success_count: int, failed_count: int, errors: list = None):
        """完成批量下载"""
        print(f"\n✅ 批量下载完成!")
        print(f"   成功: {success_count}")
        print(f"   失败: {failed_count}")
        
        if errors and failed_count > 0:
            print(f"\n❌ 错误详情:")
            for error in errors[:5]:  # 只显示前5个错误
                print(f"   - {error}")
            if len(errors) > 5:
                print(f"   ... 还有 {len(errors) - 5} 个错误")


# 便捷函数
def create_simple_progress_callback():
    """创建简单进度回调"""
    display = SimpleProgressDisplay()
    return lambda task: display.display_progress(task)


def create_batch_progress_callback():
    """创建批量进度回调"""
    display = BatchProgressDisplay()
    return lambda current, total, title: display.update_progress(current, total, title)


def finish_batch_display(result: dict):
    """完成批量显示"""
    display = BatchProgressDisplay()
    display.finish(result["success"], result["failed"], result.get("errors", []))


# 兼容性函数
def progress_callback_wrapper(callback_type: str = "simple"):
    """进度回调包装器"""
    if callback_type == "simple":
        return create_simple_progress_callback()
    elif callback_type == "batch":
        return create_batch_progress_callback()
    else:
        return None