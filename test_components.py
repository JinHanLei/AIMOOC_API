import requests
import json
from settings import BILIBILI_COOKIE

# 测试服务器地址
BACKEND_URL = "http://localhost:3000"  # Flask服务器

def test_hello():
    """测试服务器状态"""
    try:
        response = requests.get(f"{BACKEND_URL}/")
        print("\n=== 测试服务器状态 ===")
        print(response.json())
    except Exception as e:
        print(f"测试服务器状态失败: {str(e)}")

def test_bili_download():
    """测试B站视频下载"""
    try:
        # 测试不同类型的视频
        test_urls = [
            # 既没有手工字幕也没有AI字幕
            "https://www.bilibili.com/video/BV1wy4y1D7JT/?p=3",
            # 只有AI字幕
            "https://www.bilibili.com/video/BV1PT4y1e7UU",
            # 英文
            "https://www.bilibili.com/video/BV1G54y1o7RP",
            # 都有
            "https://www.bilibili.com/video/BV1pv411H78e"
        ]
        
        print("\n=== 测试视频下载 ===")
        for url in test_urls:
            print(f"\n下载视频: {url}")
            response = requests.post(
                f"{BACKEND_URL}/bili",
                json={"url": url, "cookie": BILIBILI_COOKIE}
            )
            if response.status_code == 200:
                print("视频下载成功")
            else:
                print(f"下载失败: {response.json()}")
    except Exception as e:
        print(f"测试视频下载失败: {str(e)}")

def test_subtitle():
    """测试字幕获取"""
    try:
        # 测试不同类型的视频
        test_urls = [
            # 既没有手工字幕也没有AI字幕
            "https://www.bilibili.com/video/BV1wy4y1D7JT/?p=3",
            # 只有AI字幕
            "https://www.bilibili.com/video/BV1PT4y1e7UU",
            # 英文
            "https://www.bilibili.com/video/BV1G54y1o7RP",
            # 都有
            "https://www.bilibili.com/video/BV1pv411H78e"
        ]
        
        print("\n=== 测试字幕获取 ===")
        for url in test_urls:
            print(f"\n获取字幕: {url}")
            response = requests.post(
                f"{BACKEND_URL}/subtitle",
                json={"url": url, "cookie": BILIBILI_COOKIE}
            )
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"测试字幕获取失败: {str(e)}")

def test_asr():
    """测试ASR服务"""
    ASR_URL = "http://10.8.27.22:5000"    # ASR服务器
    try:
        print("\n=== 测试ASR服务 ===")
        audio_dir = "./bilibili_video/BV1wy4y1D7JT_p3_audio.mp3"
        response = requests.post(
            f"{ASR_URL}/asr",
            files={"file": open(audio_dir, 'rb')},
            timeout=7200
        )
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"测试ASR服务失败: {str(e)}")

if __name__ == "__main__":
    # test_hello()
    test_bili_download()
    # test_subtitle()