from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2.ext import debug
from pydantic import BaseModel
import os
import json
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from settings import ALGO_PORT, ALGO_HOST
from components.processVideo import download_video, extract_bv_and_p_from_url, get_video_info, get_video_cid_aid, video2audio
from components.getSubtitle import get_subtitle_from_bilibili, get_subtitle_from_ai
from components.getAIContent import get_ai_notes, get_ai_quiz
from components.dbOperations import (
    get_course_series, create_course_series, 
    get_course_parts, create_course_part, update_course_part
)

def get_file_path(filename):
    """Get absolute path for a file in the project"""
    return os.path.join(project_root, filename)

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

async def ensure_bilibili_video_exists(bv_number: str, meta_data: dict) -> str:
    """确保课程系列和分P信息存在于数据库中"""
    series = get_course_series(unique_id=bv_number)
    if not series:
        series = create_course_series(
            unique_id=bv_number,
            title=meta_data['title'],
            description=meta_data['desc'],
            pic=meta_data['pic'],
            owner=meta_data['owner']['name'],
            face=meta_data['owner']['face'],
            source='bilibili'
        )
        series_id = series['series_id']
        for page in meta_data['pages']:
            create_course_part(
                series_id=series_id,
                title=page['part'],
                page=page['page'],
                status=0
            )
    else:
        series_id = series[0]['series_id']
    return series_id

async def get_part_info(series_id: str, page_number: int) -> dict:
    parts = get_course_parts(series_id=series_id)
    for part in parts:
        if part['page'] == page_number:
            return part
    return None

@app.get("/")
async def hello():
    return {
        'status': 'ok',
        'message': 'Server is running'
    }

@app.post("/video")
async def get_video(request: URLRequest):
    try:
        if request.url.startswith('https://www.bilibili.com/video/'):
            bv_number, p_number = extract_bv_and_p_from_url(request.url)
            file_suffix = f"_p{p_number}" if p_number > 1 else ""
            video_path = get_file_path(f"bilibili_video/{bv_number}{file_suffix}.mp4")
            meta_data = get_video_info(bv_number)
            series_id = await ensure_bilibili_video_exists(bv_number, meta_data)
            part_info = await get_part_info(series_id, p_number)
            if not part_info:
                raise HTTPException(status_code=404, detail="未找到对应的分P信息")
            if part_info['status'] == 2 and os.path.exists(video_path):  # 已下载
                print(f"视频已存在，直接返回: {video_path}")
                return FileResponse(video_path, media_type='video/mp4')
            update_course_part(part_info['part_id'], {'status': 1})
            print(f"视频不存在或未下载完成，开始下载: {request.url}")
            if download_video(request.url, request.cookie):
                update_course_part(part_info['part_id'], {'status': 2})
                return FileResponse(video_path, media_type='video/mp4')
            update_course_part(part_info['part_id'], {'status': 0})
            raise HTTPException(status_code=500, detail="视频下载失败")
    except Exception as e:
        if 'part_info' in locals() and part_info:
            update_course_part(part_info['part_id'], {'status': 0})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subtitle")
async def get_subtitle(request: URLRequest):
    try:
        bv_number, p_number = extract_bv_and_p_from_url(request.url)
        file_suffix = f"_p{p_number}" if p_number > 1 else ""
        series = get_course_series(unique_id=bv_number)
        if not series:
            meta_data = get_video_info(bv_number)
            series_id = await ensure_bilibili_video_exists(bv_number, meta_data)
        else:
            series_id = series[0]['series_id']
            
        part_info = await get_part_info(series_id, p_number)
        if not part_info:
            raise HTTPException(status_code=404, detail="未找到对应的分P信息")
            
        # 检查数据库中是否已有字幕
        if part_info.get('subtitle'):
            return json.loads(part_info['subtitle'])
            
        # 获取字幕
        meta_data = get_video_info(bv_number)
        cid, aid = get_video_cid_aid(meta_data, p_number)
        subtitle = get_subtitle_from_bilibili(aid, cid, request.cookie)
        
        if not subtitle:
            video_path = get_file_path(f"bilibili_video/{bv_number}{file_suffix}.mp4")
            if not os.path.exists(video_path):
                if not download_video(request.url, request.cookie):
                    raise HTTPException(status_code=500, detail="视频下载失败")
            audio_path = video2audio(video_path)
            subtitle = get_subtitle_from_ai(audio_path)
            
        if not subtitle:
            raise HTTPException(status_code=404, detail="无法获取字幕")
            
        # 更新数据库中的字幕信息
        update_course_part(part_info['part_id'], {
            'subtitle': json.dumps(subtitle, ensure_ascii=False)  # 直接存储整个字幕数据
        })
        
        return subtitle  # 直接返回字幕数据
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quiz")
async def get_quiz(request: URLRequest):
    try:
        bv_number, p_number = extract_bv_and_p_from_url(request.url)
        series = get_course_series(unique_id=bv_number)
        if not series:
            meta_data = get_video_info(bv_number)
            series_id = await ensure_bilibili_video_exists(bv_number, meta_data)
        else:
            series_id = series[0]['series_id']

        part_info = await get_part_info(series_id, p_number)
        if not part_info:
            raise HTTPException(status_code=404, detail="未找到对应的分P信息")

        # 确保有字幕
        if not part_info.get('subtitle'):
            await get_subtitle(request)
            part_info = await get_part_info(series_id, p_number)

        subtitle_data = json.loads(part_info['subtitle'])
        quizzes = get_ai_quiz(subtitle_data)
        return {"quizzes": quizzes}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notes")
async def get_notes(request: URLRequest):
    try:
        bv_number, p_number = extract_bv_and_p_from_url(request.url)
        series = get_course_series(unique_id=bv_number)
        if not series:
            meta_data = get_video_info(bv_number)
            series_id = await ensure_bilibili_video_exists(bv_number, meta_data)
        else:
            series_id = series[0]['series_id']
        part_info = await get_part_info(series_id, p_number)
        if not part_info:
            raise HTTPException(status_code=404, detail="未找到对应的分P信息")
        if part_info.get('default_note'):
            return {"notes": part_info['default_note']}
        if not part_info.get('subtitle'):
            await get_subtitle(request)
            part_info = await get_part_info(series_id, p_number)
        subtitle_data = json.loads(part_info['subtitle'])
        notes = get_ai_notes(subtitle_data)
        update_course_part(part_info['part_id'], {
            'default_note': notes
        })
        return {"notes": notes}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    # 确保必要的文件夹存在
    if not os.path.exists(get_file_path("bilibili_video")):
        os.makedirs(get_file_path("bilibili_video"))

    import uvicorn
    uvicorn.run(app, host=ALGO_HOST, port=ALGO_PORT, log_level="info")
