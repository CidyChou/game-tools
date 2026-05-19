# PNG Tools

一个轻量的图片背景抠除工具。默认处理 `input/` 目录里的图片，并把透明背景 PNG 输出到 `output/`。

## 安装

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

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

网页支持上传图片一键去背景、上传 sprite sheet 预览序列帧动画，也支持在浏览器本地上传视频、选择片段并生成 sprite sheet。

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
