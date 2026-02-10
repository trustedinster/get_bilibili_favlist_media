minimal_bilibili_api

精简版哔哩哔哩 API 库

## 功能特性

- 🚀 **轻量级**: 只保留核心功能，去除冗余代码
- 🔐 **登录支持**: 支持二维码登录
- 📁 **收藏夹**: 获取收藏夹列表和内容
- 🎵 **音频下载**: 获取音频信息和下载链接
- 🎬 **视频标题**: 获取视频标题信息
- ⚡ **高性能**: 基于 curl_cffi，支持 HTTP/2

## 安装依赖

```bash
pip install curl_cffi qrcode qrcode-terminal
```

## 快速开始

### 1. 登录

```python
import asyncio
from minimal_bilibili_api import login_with_qr

async def main():
    # 二维码登录
    credential = await login_with_qr()
    print("登录成功!")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 获取收藏夹

```python
from minimal_bilibili_api import FavoriteList, get_video_favorite_list

async def get_favorites():
    # 获取用户收藏夹列表
    fav_list = await get_video_favorite_list(uid=123456)
    
    # 获取特定收藏夹内容
    fav = FavoriteList(media_id=12345, credential=credential)
    info = await fav.get_info()  # 收藏夹信息
    content = await fav.get_content()  # 收藏夹内容
```

### 3. 音频下载

```python
from minimal_bilibili_api import Audio, get_audio_download_url

async def download_audio():
    # 方式1: 使用 Audio 类
    audio = Audio(auid=12345, credential=credential)
    info = await audio.get_info()
    download_info = await audio.get_download_url()
    
    # 方式2: 直接获取下载链接
    download_info = await get_audio_download_url(auid=12345)
```

### 4. 获取视频标题

```python
from minimal_bilibili_api import Video, get_video_title

async def get_title():
    # 方式1: 使用 Video 类
    video = Video(bvid="BV1xx411c7mu", credential=credential)
    title = await video.get_title()
    
    # 方式2: 直接获取标题
    title = await get_video_title(bvid="BV1xx411c7mu")
```

## API 文档

### 登录模块

#### `login_with_qr()`
二维码登录，返回 Credential 对象

### 收藏夹模块

#### `FavoriteList`
- `get_info()` - 获取收藏夹信息
- `get_content()` - 获取收藏夹内容

#### `get_video_favorite_list(uid)`
获取用户的所有收藏夹列表

#### `get_video_favorite_list_content(media_id)`
获取指定收藏夹的内容

### 音频模块

#### `Audio`
- `get_info()` - 获取音频信息
- `get_download_url()` - 获取音频下载链接

#### `get_audio_download_url(auid)`
直接获取音频下载链接

### 视频模块

#### `Video`
- `get_info()` - 获取视频完整信息
- `get_title()` - 获取视频标题

#### `get_video_title(bvid/aid)`
直接获取视频标题

## 凭据管理

```python
from minimal_bilibili_api import Credential

# 创建凭据
cred = Credential(
    sessdata="your_sessdata",
    bili_jct="your_bili_jct", 
    dedeuserid="your_dedeuserid"
)

# 检查凭据完整性
cred.raise_for_no_sessdata()  # 检查是否有 sessdata
cred.raise_for_no_bili_jct()  # 检查是否有 bili_jct
```

## 注意事项

1. 本库仅保留了最核心的功能
2. 只支持 curl_cffi 作为网络客户端
3. 部分高级功能已被移除
4. 建议使用二维码登录方式