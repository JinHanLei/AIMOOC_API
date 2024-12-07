import json
import openai
from openai import OpenAI
import os
import sys

from sympy.physics.units import temperature

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from settings import NOTES_PROMPT, QUIZ_PROMPT, OPENAI_API_KEY, OPENAI_BASE_URL


def subtitle2text(subtitles, min_length=10, use_timestamp=True):
    """
    将字幕转换为文本，合并过短的字幕
    
    Args:
        subtitles (list): 字幕数据列表
        min_length (int): 最小字幕长度（字符数）
        use_timestamp (bool): 是否在文本中包含时间戳
    
    Returns:
        str: 处理后的字幕文本
    """
    if not subtitles:
        return ""
    if min_length == 0:
        return "\n".join(
            f"[{sub['from']:.2f}] {sub['content']}" if use_timestamp else sub['content']
            for sub in subtitles
        )
    result = []
    current_text = ""
    current_start = None
    
    def add_to_result(start_time, text):
        if use_timestamp:
            result.append(f"[{start_time:.2f}] {text}")
        else:
            result.append(text)
    
    for sub in subtitles:
        text = sub['content'].strip()
        start_time = float(sub['from'])
        # 初始化当前片段
        if current_text == "":
            current_text = text
            current_start = start_time
            continue
        # 在文本太短时合并
        if len(current_text) < min_length:
            current_text = f"{current_text} {text}"
        else:
            add_to_result(current_start, current_text)
            current_text = text
            current_start = start_time
    if current_text:
        add_to_result(current_start, current_text)
    return "\n".join(result)


def chat_with_subtitle(subtitle_data: list, prompt: str, temperature=0.7) -> str:
    """
    使用OpenAI API处理字幕内容
    """
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
    )
    
    subtitles = subtitle_data[0]['subtitle']
    subtitle_text = subtitle2text(subtitles, min_length=20)
    prompt = prompt.format(subtitle_text)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    return response.choices[0].message.content


def get_ai_notes(subtitle_data):
    """生成AI笔记"""
    return chat_with_subtitle(subtitle_data, NOTES_PROMPT, temperature=0.3)


def get_ai_quiz(subtitle_data):
    """生成AI题目"""
    return chat_with_subtitle(subtitle_data, QUIZ_PROMPT)


if __name__ == '__main__':
    # 测试字幕处理
    test_path = "bilibili_video/BV1G54y1o7RP_p2_subtitle.json"
    with open(test_path, 'r', encoding='utf-8') as f:
        subtitle_data = json.load(f)
    print("\n=== 合并后的字幕 ===")
    print(subtitle2text(subtitle_data[0]['subtitle'], min_length=30))
    
    print("\n=== 生成的内容 ===")
    notes = get_ai_quiz(subtitle_data)
    print(notes)