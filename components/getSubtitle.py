import requests
import openai
import time
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from components.processVideo import extract_bv_and_p_from_url, get_video_info, get_video_cid_aid
from settings import OPENAI_BASE_URL, OPENAI_API_KEY, ASR_URL, ASR_CHECK_PROMPT, BILIBILI_COOKIE


def get_subtitle_from_bilibili(aid, cid, cookies=None, max_retries=3):
    """从B站API获取字幕，支持重试"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://www.bilibili.com/',
        "cookie": cookies or BILIBILI_COOKIE
    }
    
    for attempt in range(max_retries):
        try:
            player_url = f"https://api.bilibili.com/x/player/wbi/v2?aid={aid}&cid={cid}"
            player_response = requests.get(player_url, headers=headers)
            if player_response.status_code == 200:
                player_data = player_response.json()
                subtitles = player_data.get('data', {}).get('subtitle', {}).get('subtitles', [])
                
                # 存储所有成功获取的字幕
                all_subtitles = []
                
                # 遍历每个字幕
                for subtitle in subtitles:
                    lan_doc = subtitle.get('lan_doc')
                    subtitle_data = None
                    
                    # 尝试获取v1版本字幕
                    try:
                        subtitle_v1 = requests.get(f"https:{subtitle.get('subtitle_url')}", headers=headers)
                        subtitle_data = subtitle_v1.json()["body"]
                        all_subtitles.append({
                            "lan": lan_doc,
                            "subtitle": subtitle_data
                        })
                        continue  # 如果v1成功，直接处理下一个字幕
                    except Exception as e:
                        print(f"获取{lan_doc}的v1字幕失败: {str(e)}")
                    
                    # 如果v1失败且存在v2，尝试获取v2版本字幕
                    if subtitle.get('subtitle_url_v2'):
                        try:
                            subtitle_v2 = requests.get(f"https:{subtitle.get('subtitle_url_v2')}", headers=headers)
                            subtitle_data = subtitle_v2.json()["body"]
                            all_subtitles.append({
                                "lan": lan_doc,
                                "subtitle": subtitle_data
                            })
                        except Exception as e:
                            print(f"获取{lan_doc}的v2字幕失败: {str(e)}")
                if all_subtitles:
                    return all_subtitles
                    
            # 如果这次尝试失败，但还有重试机会
            if attempt < max_retries - 1:
                print(f"第{attempt + 1}次获取字幕失败，等待1秒后重试...")
                time.sleep(1)  # 等待1秒后重试
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"第{attempt + 1}次获取字幕出错: {str(e)}，等待1秒后重试...")
                time.sleep(1)
            else:
                print(f"最后一次尝试失败: {str(e)}")
    return None


def get_subtitle_from_ai(audio_dir, ai_check=False):
    subtitle_res = requests.post(ASR_URL, files={"file": open(audio_dir, 'rb')}, timeout=7200).json()
    client = openai.OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )
    if ai_check:
        chat = client.chat.completions.create(model="gpt-3.5-turbo", messages=[
            {"role": "system", "content": ASR_CHECK_PROMPT},
            {"role": "user", "content": f"以下是需要校对的字幕文本：{subtitle_res}"}
        ])
        subtitle_res = chat.choices[0].message.content
    return subtitle_res


if __name__ == '__main__':
    # 既没有手工字幕也没有AI字幕
    # url = "https://www.bilibili.com/video/BV1wy4y1D7JT/?p=3&spm_id_from=333.788.top_right_bar_window_history.content.click&vd_source=51187f45b082dafba052581f0233ba2e"
    # 只有AI字幕
    # url = "https://www.bilibili.com/video/BV1PT4y1e7UU/?spm_id_from=333.788.player.player_end_recommend_autoplay&vd_source=51187f45b082dafba052581f0233ba2e"
    # 英文
    # url = "https://www.bilibili.com/video/BV1G54y1o7RP/?spm_id_from=333.337.search-card.all.click&vd_source=51187f45b082dafba052581f0233ba2e"
    # 都有
    url = "https://www.bilibili.com/video/BV1pv411H78e/?spm_id_from=333.337.search-card.all.click&vd_source=51187f45b082dafba052581f0233ba2e"
    bv_number, p_number = extract_bv_and_p_from_url(url)
    meta_data = get_video_info(bv_number)
    cid, aid = get_video_cid_aid(meta_data, p_number)
    subtitles = get_subtitle_from_bilibili(aid, cid, BILIBILI_COOKIE)
    print(subtitles)

    # audio_path = "./bilibili_video/BV1wy4y1D7JT_p3_audio.mp3"
    # res = get_subtitle_from_ai(audio_path)
    # print(res)