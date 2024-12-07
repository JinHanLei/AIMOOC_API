import os, re
from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from pathlib import Path
from datetime import timedelta
from funasr import AutoModel
import torch
import shutil
from pydub import AudioSegment
from settings import ASR_HOST, ASR_PORT

TMPDIR=Path(os.path.dirname(__file__)+"/tmp").as_posix()
Path(TMPDIR).mkdir(exist_ok=True)
device="cuda:0" if torch.cuda.is_available() else "cpu"

# asr_model_path = "./SenseVoiceSmall"
# seg_model_path = "./punc_ct-transformer_cn-en-common-vocab471067-large"
asr_model_path = "iic/SenseVoiceSmall"
seg_model_path = "fsmn-vad"

model = AutoModel(model=asr_model_path, punc_model="ct-punc", disable_update=True, device=device,disable_log=True,disable_pbar=True)
vm = AutoModel(model=seg_model_path,max_single_segment_time=20000,max_end_silence_time=250,disable_update=True,device=device,disable_log=True,disable_pbar=True)
app = FastAPI()

def ms_to_time_string(*, ms=0, seconds=None):
    # 计算小时、分钟、秒和毫秒
    if seconds is None:
        td = timedelta(milliseconds=ms)
    else:
        td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    time_string = f"{hours}:{minutes}:{seconds},{milliseconds}"
    return format_time(time_string, ',')

def format_time(s_time="", separate=','):
    if not s_time.strip():
        return f'00:00:00{separate}000'
    hou, min, sec,ms = 0, 0, 0,0
    tmp = s_time.strip().split(':')
    if len(tmp) >= 3:
        hou,min,sec = tmp[-3].strip(),tmp[-2].strip(),tmp[-1].strip()
    elif len(tmp) == 2:
        min,sec = tmp[0].strip(),tmp[1].strip()
    elif len(tmp) == 1:
        sec = tmp[0].strip()
    if re.search(r',|\.', str(sec)):
        t = re.split(r',|\.', str(sec))
        sec = t[0].strip()
        ms=t[1].strip()
    else:
        ms = 0
    hou = f'{int(hou):02}'[-2:]
    min = f'{int(min):02}'[-2:]
    sec = f'{int(sec):02}'
    ms = f'{int(ms):03}'[-3:]
    return f"{hou}:{min}:{sec}{separate}{ms}"

def remove_unwanted_characters(text: str) -> str:
    # 保留中文、日文、韩文、英文、数字和常见符号，去除其他字符
    allowed_characters = re.compile(r'[^\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af'
                                    r'a-zA-Z0-9\s.,!@#$%^&*()_+\-=\[\]{};\'"\\|<>/?，。！｛｝【】；‘’“”《》、（）￥]+')
    return re.sub(allowed_characters, '', text)

@app.get("/", response_class=HTMLResponse)
async def root():
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset=utf-8>
            <title>ASR API</title>
        </head>
        <body>
            api 地址为 http://{ASR_HOST}:{ASR_PORT}/asr
        </body>
    </html>
    """

@app.post("/asr")
async def asr(file: UploadFile):
    # 创建一个临时文件路径
    temp_file_path = f"{TMPDIR}/{file.filename}"
    ## 将上传的文件保存到临时路径
    with open(temp_file_path, "wb") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
    segments = vm.generate(input=temp_file_path)
    audiodata = AudioSegment.from_file(temp_file_path)    
    
    # 存储所有字幕片段
    subtitle_segments = []
    
    for seg in segments[0]['value']:
        chunk = audiodata[seg[0]:seg[1]]
        filename = f"{TMPDIR}/{seg[0]}-{seg[1]}.wav"
        chunk.export(filename)
        res = model.generate(
            input=filename,
            language="auto",
            use_itn=True
        )
        text = remove_unwanted_characters(rich_transcription_postprocess(res[0]["text"]))
        # 将每个片段转换为字幕格式
        subtitle_segments.append({
            "from": seg[0] / 1000,  # 转换为秒
            "to": seg[1] / 1000,    # 转换为秒
            "location": 2,          # 固定底部位置
            "content": text.strip()
        })
    
    # 构建最终的字幕数据
    subtitle_data = [{
        "lan": "AI生成",
        "subtitle": subtitle_segments
    }]
    
    return subtitle_data


if __name__=='__main__':
    import uvicorn
    uvicorn.run(app, host=ASR_HOST,port=ASR_PORT, log_level="info")
