import requests
import json
from settings import BILIBILI_COOKIE

# 测试服务器地址
BACKEND_URL = "http://localhost:3000"  # FastAPI服务器


def test_video():
    """测试视频接口"""
    try:
        # 测试不同类型的视频
        test_urls = [
            # 既没有手工字幕也没有AI字幕
            "https://www.bilibili.com/video/BV1wy4y1D7JT/?p=3",
            # 只有AI字幕
            # "https://www.bilibili.com/video/BV1PT4y1e7UU",
            # # 英文
            # "https://www.bilibili.com/video/BV1G54y1o7RP",
            # # 都有
            # "https://www.bilibili.com/video/BV1pv411H78e"
        ]
        print("\n=== 测试视频 ===")
        for url in test_urls:
            print(f"\n处理视频: {url}")
            response = requests.post(
                f"{BACKEND_URL}/video",
                json={"url": url, "cookie": BILIBILI_COOKIE}
            )
            if response.status_code == 200:
                print("视频处理成功")
            else:
                print(f"处理失败: {response.json()}")
    except Exception as e:
        print(f"测试视频处理失败: {str(e)}")


def test_subtitle():
    """测试字幕接口"""
    try:
        test_urls = [
            # 既没有手工字幕也没有AI字幕
            "https://www.bilibili.com/video/BV1wy4y1D7JT/?p=3",
            # 只有AI字幕
            # "https://www.bilibili.com/video/BV1PT4y1e7UU",
            # # 英文字幕
            # "https://www.bilibili.com/video/BV1G54y1o7RP",
            # # 中英字幕
            # "https://www.bilibili.com/video/BV1pv411H78e"
        ]
        
        print("\n=== 测试字幕获取 ===")
        for url in test_urls:
            print(f"\n获取字幕: {url}")
            response = requests.post(
                f"{BACKEND_URL}/subtitle",
                json={"url": url, "cookie": BILIBILI_COOKIE}
            )
            
            if response.status_code == 200:
                subtitle_data = response.json()
                print("字幕获取成功:")
                print(subtitle_data)
            else:
                print(f"获取失败: {response.json()}")
                
    except Exception as e:
        print(f"测试字幕获取失败: {str(e)}")

def test_notes():
    """测试笔记接口"""
    try:
        test_urls = [
            # 既没有手工字幕也没有AI字幕
            "https://www.bilibili.com/video/BV1wy4y1D7JT/?p=3",
            # 只有AI字幕
            # "https://www.bilibili.com/video/BV1PT4y1e7UU",
            # # 英文字幕
            # "https://www.bilibili.com/video/BV1G54y1o7RP",
            # # 中英字幕
            # "https://www.bilibili.com/video/BV1pv411H78e"
        ]
        
        print("\n=== 测试笔记生成 ===")
        for url in test_urls:
            print(f"\n生成笔记: {url}")
            response = requests.post(
                f"{BACKEND_URL}/notes",
                json={"url": url, "cookie": BILIBILI_COOKIE}
            )
            
            if response.status_code == 200:
                notes_data = response.json()
                print("笔记生成成功:")
                print(notes_data['notes'])
            else:
                print(f"生成失败: {response.json()}")
    except Exception as e:
        print(f"测试笔记生成失败: {str(e)}")

def test_quiz():
    """测试题目生成接口"""
    try:
        test_urls = [
            "https://www.bilibili.com/video/BV1wy4y1D7JT/?p=3",
        ]
        
        print("\n=== 测试题目生成 ===")
        for url in test_urls:
            print(f"\n生成题目: {url}")
            response = requests.post(
                f"{BACKEND_URL}/quiz",
                json={"url": url, "cookie": BILIBILI_COOKIE}
            )
            
            if response.status_code == 200:
                quiz_data = response.json()
                print("题目生成成功:")
                print(quiz_data['quizzes'])
            else:
                print(f"生成失败: {response.json()}")
                
    except Exception as e:
        print(f"测试题目生成失败: {str(e)}")

if __name__ == "__main__":
    # test_video()
    # test_subtitle()
    test_notes()
    test_quiz()