# Game Tools

一个游戏开发中用到的小工具。
包括:
- 轻量的图片背景抠除工具。默认处理 `input/` 目录里的图片，并把透明背景 PNG 输出到 `output/`。

## 安装

```bash
python3 -m pip install -r requirements.txt

.venv/bin/python -m pip install -r requirements.txt
```

## 使用

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

## 常用参数

默认只抠除和图片边缘连通的白色背景，更适合保留主体内部的白色区域。

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
