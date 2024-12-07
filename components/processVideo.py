import requests, time, hashlib, urllib.request, re, json
from moviepy.editor import VideoFileClip
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from settings import BILIBILI_COOKIE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': '*/*',
    'Range': 'bytes=0-',
    'Origin': 'https://www.bilibili.com',
    'Cookie': BILIBILI_COOKIE
}

def check_folder(fp):
    """检查必要的文件夹是否存在"""
    if not os.path.exists(fp):
        os.makedirs(fp)

def extract_bv_and_p_from_url(url):
    """从B站URL中提取BV号和分P号"""
    bv_number = re.search(r'BV\w{10}', url).group()
    p_number = re.search(r'[?&]p=(\d+)', url)
    if not bv_number:
        raise ValueError("无法从URL中提取BV号")
    return bv_number, int(p_number.group(1)) if p_number else 1


def get_video_info(bv_number):
    """
    直接从B站API获取视频的元数据信息
    
    Args:
        bv_number (str): 视频的BV号
        
    Returns:
        dict: 包含视频信息的字典
    """
    try:
        # 获取视频基本信息
        view_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_number}"
        response = requests.get(view_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        if data['code'] != 0:
            raise Exception(f"获取视频信息失败: {data['message']}")
            
        video_data = data['data']
        
        # 构建返回的数据结构
        # result = {
        #     'bvid': video_data['bvid'],
        #     'aid': video_data['aid'],
        #     'cid': video_data['cid'],  # 第一个分P的cid
        #     'title': video_data['title'],
        #     'desc': video_data['desc'],
        #     'duration': video_data['duration'],
        #     'owner': {
        #         'name': video_data['owner']['name'],
        #         'mid': video_data['owner']['mid']
        #     },
        #     'pages': []
        # }
        #
        # # 添加分P信息
        # if 'pages' in video_data:
        #     for page in video_data['pages']:
        #         result['pages'].append({
        #             'cid': page['cid'],
        #             'page': page['page'],  # 分P号
        #             'part': page['part'],  # 分P标题
        #             'duration': page['duration']
        #         })
                
        return video_data
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")
    except KeyError as e:
        raise Exception(f"解析视频信息失败: {str(e)}")
    except Exception as e:
        raise Exception(f"获取视频信息时发生错误: {str(e)}")


def get_video_cid_aid(meta_data, p_number):
    """从元数据中获取指定分P的cid和aid"""
    pages = meta_data.get("pages", [])
    if not pages:
        return meta_data["cid"], meta_data["aid"]
    if p_number > len(pages):
        raise ValueError(f"错误：视频只有{len(pages)}个分P，无法下载第{p_number}P")
    page = pages[p_number - 1]
    return page["cid"], meta_data["aid"]


def get_download_url(aid, cid, cookie):
    """获取视频的下载链接"""
    download_url = "https://bili.zhouql.vip/download/"
    post_data = {
        "aid": aid,
        "cid": cid,
        "cookie": cookie or BILIBILI_COOKIE
    }
    response = requests.post(download_url, json=post_data)
    data = response.json()
    if data["code"] != 0:
        raise Exception(f"下载链接请求失败: {data['message']}")
    return data["data"]["durl"][0]["url"], data["data"].get("quality", "未知")

def download_file(url, file_path):
    """下载文件"""
    try:
        response = requests.get(url, stream=True, headers=HEADERS)
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        return True
    except Exception as e:
        return False


def download_video(video_url, cookie=None):
    """主下载函数"""
    try:
        bv_number, p_number = extract_bv_and_p_from_url(video_url)
        meta_data = get_video_info(bv_number)
        cid, aid = get_video_cid_aid(meta_data, p_number)
        download_url, quality = get_download_url(aid, cid, cookie)
        check_folder("bilibili_video")
        file_suffix = f"_p{p_number}" if p_number > 1 else ""
        video_path = fr"bilibili_video/{bv_number}{file_suffix}.mp4"
        if download_file(download_url, video_path):
            return video_path
        return False
    except Exception as e:
        print("发生错误:", str(e))
        return False

def video2audio(video_path, output_dir="bilibili_video"):
    try:
        audio_base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_name = f"{audio_base_name}_audio"
        check_folder(output_dir)
        video = VideoFileClip(video_path)
        audio = video.audio
        audio_path = os.path.join(output_dir, f"{output_name}.mp3")
        audio.write_audiofile(audio_path)
        audio.close()
        video.close()
        return audio_path
    except Exception as e:
        return False


if __name__ == "__main__":
    # url = "https://www.bilibili.com/video/BV1wy4y1D7JT/?p=3&spm_id_from=333.788.top_right_bar_window_history.content.click&vd_source=51187f45b082dafba052581f0233ba2e"
    # download_video(url)
    res = get_video_info('BV1wy4y1D7JT')
    print(res)
