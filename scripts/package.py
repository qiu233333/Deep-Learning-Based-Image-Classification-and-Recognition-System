# -*- coding: utf-8 -*-
"""打包提交材料：源码+数据集+模型+图表+视频+报告（排除 .venv 与原始压缩包）"""
import os, zipfile, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "智能系统设计与实践-提交材料.zip")
OUT_TMP = os.path.join("/tmp", "submit_package_tmp.zip")
OUT_NAME = os.path.basename(OUT)

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", "flowers_raw", "jpg"}
EXCLUDE_FILES = {"102flowers.tgz", "download_tgz.log", "download_labels.log", "download_setid.log",
                 "system.db-journal", OUT_NAME}

def should_include(root, name):
    if name in EXCLUDE_DIRS or name.startswith(".") or name.endswith(".pyc"):
        return False
    if name in EXCLUDE_FILES:
        return False
    # 排除训练中间权重，仅保留最优权重
    if name.endswith("_last.pt"):
        return False
    return True

NO_COMPRESS = {".jpg", ".jpeg", ".png", ".webp", ".pt", ".webm", ".mp4"}
with zipfile.ZipFile(OUT_TMP, "w", zipfile.ZIP_DEFLATED) as z:
    n = 0
    for base in ("app", "scripts", "data", "models", "results", "figures", "runs", "docs", "uploads"):
        p = os.path.join(ROOT, base)
        if not os.path.isdir(p):
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if should_include(root, d)]
            for f in files:
                if not should_include(root, f):
                    continue
                full = os.path.join(root, f)
                if os.path.getsize(full) > 900 * 1024 * 1024:
                    continue
                rel = os.path.relpath(full, ROOT)
                ext = os.path.splitext(f)[1].lower()
                z.write(full, rel, compress_type=zipfile.ZIP_STORED if ext in NO_COMPRESS else zipfile.ZIP_DEFLATED)
                n += 1
    for f in ("README.md", "requirements.txt"):
        z.write(os.path.join(ROOT, f), f)
        n += 1
if os.path.exists(OUT):
    os.remove(OUT)
os.replace(OUT_TMP, OUT)
print("packed", n, "files ->", OUT)
print("size MB:", round(os.path.getsize(OUT) / 1e6, 1))
