# AIMOOC——AI 驱动的互动式在线学习平台

项目完全实现本地化。 
- 前端：基于 React 和 NextJS。 
- 后端：本仓库，基于 python-FASTAPIAIMOOC_API，更适合开发深度学习套件。 
- 数据库：supabase负责用户验证和课程相关信息；upstash负责聊天记录等。

# Quick Start

1. 启动本地大模型：[api-for-open-llm](https://github.com/xusenlinzy/api-for-open-llm)

2. 启动asr服务，用于字幕识别：

```bash
# 安装依赖
pip install -r requirements.txt
python asr_api.py
```

3. 启动app：

```bash
# 运行
python app.py
```

# 技术要点

## ASR字幕生成
- 下载视频，并提取音频。
- 先利用语音分割技术，将音频分割为多个片段。
- 后对于每个片段，利用语音识别模型生成文字。
- 最后转化为字幕json格式。
- TODO: 识别存在些许错误，拟采用[VideoLingo](https://github.com/Huanshere/VideoLingo)的方案进行优化。

## AI总结和出题
- 利用字幕进行总结和出题。
- TODO: 优化提示词，提高总结和出题质量。
- TODO: 利用视频多模态模型，提高对视频的理解能力。

## 聊天机器人
- 利用大模型的内在能力，进行用户问题的解答。
- TODO: 将教学视频转化为知识图谱，结合知识提高解答的专业性和准确性。

## 数据库
- 使用sql.txt在[supabase](https://supabase.com/)中创建表格。

## FASTAPI后端
- TODO: 打包为docker镜像。

# Thanks
- [VideoLingo](https://github.com/Huanshere/VideoLingo)
- [api-for-open-llm](https://github.com/xusenlinzy/api-for-open-llm)
- [supabase](https://supabase.com/)
- [upstash](https://upstash.com/)