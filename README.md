# PNG Tools

一个轻量的图片背景抠除工具。默认处理 `input/` 目录里的图片，并把透明背景 PNG 输出到 `output/`。

## 安装

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

音频裁剪功能需要系统已安装 `ffmpeg`，并且 `ffmpeg` 可在 `PATH` 中直接执行。

## 使用

启动 Web 工具台：

```bash
python3 run_web.py
```

默认会监听 `0.0.0.0:8000`，同一局域网设备可以用本机 IP 访问，例如：

```text
http://192.168.113.225:8000/
```

如果只想本机访问：

```bash
.venv/bin/python -m uvicorn web_app:app --reload --host 127.0.0.1 --port 8000
```

网页支持上传图片一键去背景、裁剪 / 扩图 / 压缩 / 调整图片尺寸、上传 sprite sheet 预览序列帧动画，也支持在浏览器本地上传视频、选择片段并生成 sprite sheet。扩图沿用裁剪选区，超出原图的区域会补成透明像素。音频工具支持 MP3、WAV、FLAC、M4A、AAC、OGG、OPUS，上传后可查看音量波形、裁剪片段，并以原始格式导出。

处理默认目录：

```bash
python3 remove_bg.py
```

处理单张图片：

```bash
python3 remove_bg.py input/example.jpg output/example.png
```

处理整个目录：

```bash
python3 remove_bg.py input output
```

压缩 PNG 图片（最多 256 色调色板，有损量化；不填输出路径时原地压缩 PNG）：

```bash
python3 compress_images.py input/example.png
```

压缩目录并输出到另一个目录：

```bash
python3 compress_images.py input output-compressed
```

## 常用参数

默认只抠除和图片边缘连通的白色背景，更适合保留主体内部的白色区域。程序会根据图片边缘自动放宽白色阈值，用来清理灰白棋盘格、压缩噪点和轻微渐变这类不够纯白的背景。

```bash
python3 remove_bg.py input output --threshold 245
```

如果想完全复刻参考脚本的效果，抠除全图所有接近白色的像素：

```bash
python3 remove_bg.py input output --mode all --threshold 245
```

指定其他背景色：

```bash
python3 remove_bg.py input output --bg-color "#f7f7f7" --tolerance 18
```

支持的输入格式：`.png`、`.jpg`、`.jpeg`、`.webp`、`.bmp`、`.tif`、`.tiff`。输出统一为 `.png`。

## Web API

去背景接口：

```bash
curl -X POST http://127.0.0.1:8000/api/remove-background \
  -F "image=@input/example.jpg" \
  -F "mode=edge" \
  -F "threshold=245" \
  --output output/example.png
```

接口返回 `image/png`，并在 `X-Pixels-Removed` 响应头里返回本次新抠除的像素数。未指定背景色时，`X-Effective-Threshold` 会返回实际使用的白色阈值。

批量去背景接口返回 ZIP：

```bash
curl -X POST http://127.0.0.1:8000/api/remove-background/batch \
  -F "images=@input/a.jpg" \
  -F "images=@input/b.webp" \
  -F "mode=edge" \
  -F "threshold=245" \
  --output output/transparent-images.zip
```

裁剪、扩图、压缩或调整尺寸接口：

```bash
curl -X POST http://127.0.0.1:8000/api/process-image \
  -F "image=@input/example.png" \
  -F "crop_enabled=true" \
  -F "crop_x=40" \
  -F "crop_y=20" \
  -F "crop_width=512" \
  -F "crop_height=512" \
  -F "compress_enabled=true" \
  -F "png_mode=palette" \
  -F "palette_colors=256" \
  --output output/example-processed.png
```

扩图时在 `/api/process-image` 请求中增加 `expand_enabled=true`，并使用负数 `crop_x` / `crop_y` 或大于原图的裁剪宽高；超出原图的部分输出为透明像素。

音频裁剪接口会保留上传文件的格式（MP3、WAV、FLAC、M4A、AAC、OGG、OGA 或 OPUS）：

```bash
curl -X POST http://127.0.0.1:8000/api/convert-audio \
  -F "audio=@input/example.wav" \
  -F "quality=small" \
  -F "start_time=1.5" \
  -F "end_time=4.8" \
  --output output/example.wav
```

`quality` 支持 `small`（默认，更小体积）、`balanced`、`clear` 三档。`start_time` 默认为 `0`，不传 `end_time` 时会转换到音频末尾。
