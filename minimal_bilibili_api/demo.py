"""
Minimal Bilibili API 示例脚本
展示如何使用精简版 API
"""

import asyncio
import json
from minimal_bilibili_api import (
    QRCodeLogin,
    FavoriteList,
    get_video_favorite_list,
    Audio,
    get_audio_download_url,
    Video,
    get_video_title,
Credential
)


async def demo_login():
    """演示异步登录方式"""
    try:
        # 使用 QRCodeLogin 类的异步方法
        login_instance = QRCodeLogin()
        credential = await login_instance.auto_login()
        print("✅ 登录成功!")
        print(f"SESSDATA: {credential.sessdata[:10]}...")
        print(f"DedeUserID: {credential.dedeuserid}")
        return credential
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return None


async def demo_favorite_list(credential):
    """演示收藏夹功能"""
    print("\n=== 收藏夹功能演示 ===")
    try:
        # 获取用户收藏夹列表
        fav_list = await get_video_favorite_list(uid=int(credential.dedeuserid), credential=credential)
        print("✅ 获取收藏夹列表成功")
        print(f"收藏夹数量: {len(fav_list.get('data', {}).get('list', []))}")

        # 获取第一个收藏夹的内容
        if fav_list.get('data', {}).get('list'):
            first_fav = fav_list['data']['list'][0]
            fav = FavoriteList(media_id=first_fav['id'], credential=credential)

            # 获取收藏夹信息
            info = await fav.get_info()
            print(f"收藏夹名称: {info.get('data', {}).get('title', '')}")

            # 获取收藏夹内容
            content = await fav.get_content()
            print(f"收藏内容数量: {len(content.get('data', {}).get('medias', []))}")

    except Exception as e:
        print(f"❌ 收藏夹操作失败: {e}")


async def demo_audio(credential):
    """演示音频功能"""
    print("\n=== 音频功能演示 ===")
    try:
        # 这里需要一个真实的音频 ID 来测试
        # audio = Audio(auid=12345, credential=credential)
        # info = await audio.get_info()
        # download_url = await audio.get_download_url()
        # print("✅ 音频功能测试通过")
        print("💡 音频功能已实现，需要具体的音频 ID 来测试")
    except Exception as e:
        print(f"❌ 音频操作失败: {e}")


async def demo_video(credential):
    """演示视频功能"""
    print("\n=== 视频功能演示 ===")
    try:
        # 测试获取视频标题
        title = await get_video_title(bvid="BV1GJ411x7h7", credential=credential)
        print(f"✅ 视频标题: {title}")

        # 演示新的音频流功能
        print("\n--- 音频流功能演示 ---")
        video = Video(bvid="BV1GJ411x7h7", credential=credential)

        # 获取音频流列表
        audio_streams = await video.get_audio_streams()
        print(f"发现 {len(audio_streams)} 个音频流:")
        for i, stream in enumerate(audio_streams, 1):
            print(f"  {i}. {stream.quality.name} - {stream.url[:60]}...")

        # 获取最佳音频流
        best_audio = await video.get_best_audio_stream()
        if best_audio:
            print(f"\n最佳音频流: {best_audio.quality.name}")
            print(f"下载链接长度: {len(best_audio.url)} 字符")

        print("✅ 视频音频流功能演示完成")

    except Exception as e:
        print(f"❌ 视频操作失败: {e}")


async def main():
    """主函数"""
    print("🚀 Minimal Bilibili API 演示程序")
    print("=" * 50)

    # 1. 演示进行登录
    credential = Credential()
    if not credential:
        return

    # 2. 收藏夹功能
    # await demo_favorite_list(credential)

    # 3. 视频功能
    await demo_video(credential)

    print("\n🎉 演示完成!")


if __name__ == "__main__":
    asyncio.run(main())
