from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

from settings import ALGO_PORT, ALGO_HOST
from src.processVideo import download_video, extract_bv_and_p_from_url, get_video_info, get_video_cid_aid, video2audio
from src.getSubtitle import get_subtitle_from_bilibili, get_subtitle_from_ai
import json

# 定义请求模型
class URLRequest(BaseModel):
    url: str
    cookie: str

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def hello():
    return {
        'status': 'ok',
        'message': 'Server is running'
    }

@app.post("/bili")
async def handle_bili(request: URLRequest, range: Optional[str] = Header(None)):
    try:
        url = request.url
        cookie = request.cookie
        bv_number, p_number = extract_bv_and_p_from_url(url)
        file_suffix = f"_p{p_number}" if p_number > 1 else ""
        video_path = f"bilibili_video/{bv_number}{file_suffix}.mp4"

        # 如果视频不存在，先下载
        if not os.path.exists(video_path):
            print(f"视频不存在，开始下载: {url}")
            if not download_video(url, cookie):
                raise HTTPException(status_code=500, detail="视频下载失败")

        file_size = os.path.getsize(video_path)

        # 处理范围请求
        if range:
            try:
                start_str = range.replace("bytes=", "").split("-")[0]
                start = int(start_str)
                # 每次返回1MB数据
                chunk_size = 1024 * 1024
                end = min(start + chunk_size, file_size - 1)
            except ValueError:
                start = 0
                end = file_size - 1

            # 构建响应头
            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(end - start + 1),
                'Content-Type': 'video/mp4',
            }

            # 返回指定范围的视频数据
            async def range_stream():
                with open(video_path, mode="rb") as video:
                    video.seek(start)
                    chunk = video.read(end - start + 1)
                    yield chunk

            return StreamingResponse(
                range_stream(),
                status_code=206,
                headers=headers,
                media_type="video/mp4"
            )

        # 如果没有范围请求，返回完整视频
        async def normal_stream():
            with open(video_path, mode="rb") as video:
                while chunk := video.read(8192):  # 8KB chunks
                    yield chunk

        headers = {
            'Accept-Ranges': 'bytes',
            'Content-Length': str(file_size),
            'Content-Type': 'video/mp4',
        }

        return StreamingResponse(
            normal_stream(),
            headers=headers,
            media_type="video/mp4"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subtitle")
async def get_subtitle(request: URLRequest):
    try:
        url = request.url
        cookie = request.cookie
        if 'bilibili.com' not in url:
            raise HTTPException(status_code=400, detail="不是有效的B站链接")

        bv_number, p_number = extract_bv_and_p_from_url(url)
        file_suffix = f"_p{p_number}" if p_number > 1 else ""
        subtitle_path = f"bilibili_video/{bv_number}{file_suffix}_subtitle.json"

        if os.path.exists(subtitle_path):
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                subtitle_data = json.load(f)
            return subtitle_data

        try:
            meta_data = get_video_info(bv_number)
            cid, aid = get_video_cid_aid(meta_data, p_number)
            subtitle = get_subtitle_from_bilibili(aid, cid, cookie)
            if not subtitle:
                video_path = fr"bilibili_video/{bv_number}{file_suffix}.mp4"
                audio_path = video2audio(video_path)
                subtitle = get_subtitle_from_ai(audio_path)
            if subtitle:
                with open(subtitle_path, 'w', encoding='utf-8') as f:
                    json.dump(subtitle, f, ensure_ascii=False, indent=2)
                return subtitle
        except Exception as e:
            print(f"获取字幕失败: {str(e)}")
            raise HTTPException(status_code=404, detail="字幕文件不存在且无法从B站获取")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    # 确保必要的文件夹存在
    if not os.path.exists("../bilibili_video"):
        os.makedirs("../bilibili_video")

    import uvicorn
    uvicorn.run(app, host=ALGO_HOST, port=ALGO_PORT, log_level="info")
