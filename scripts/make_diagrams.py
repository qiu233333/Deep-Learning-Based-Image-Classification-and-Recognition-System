# -*- coding: utf-8 -*-
"""绘制系统架构图与目录结构图"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)
for cand in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc",
             "/System/Library/Fonts/Hiragino Sans GB.ttc", "/Library/Fonts/Arial Unicode.ttf"]:
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "Heiti SC"]
plt.rcParams["axes.unicode_minus"] = False

def architecture():
    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=160)
    ax.set_xlim(0, 13); ax.set_ylim(0, 8.5); ax.axis("off")
    def box(x, y, w, h, text, fc, sub=None):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", fc=fc, ec="#334155", lw=1.4)
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2 + (0.55 if sub else 0), text, ha="center", va="center",
                fontsize=12.5, fontweight="bold", color="#0f172a")
        if sub:
            ax.text(x + w / 2, y + h / 2 - 0.5, sub, ha="center", va="center", fontsize=8.6, color="#334155")
    def arrow(x1, y1, x2, y2, label=None, color="#475569"):
        a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18, lw=2, color=color)
        ax.add_patch(a)
        if label:
            ax.text((x1 + x2) / 2 + 0.15, (y1 + y2) / 2 + 0.12, label, fontsize=9.5, color="#475569")
    # 表现层
    box(0.4, 6.2, 12.2, 1.9, "表现层（浏览器）",
        "#bfdbfe", "HTML/CSS/JavaScript：图像上传 · 模型选择 · Top-5 结果展示 · 历史记录")
    box(3.2, 6.55, 3.1, 1.15, "识别台页面\n/", "#dbeafe", None)
    box(7.0, 6.55, 3.1, 1.15, "管理后台页面\n/admin", "#dbeafe", None)
    # 服务层
    box(0.4, 3.4, 12.2, 2.2, "服务层（Flask + PyTorch）",
        "#bbf7d0", "REST API · 图像预处理 · 模型注册表 · 推理引擎(MPS) · 特征提取 · 训练任务调度")
    box(0.8, 3.75, 4.0, 1.3, "Flask 路由与 API\n/api/classify /api/models\n/api/train /api/stats", "#dcfce7", None)
    box(5.2, 3.75, 3.2, 1.3, "模型注册表\nResNet18 / ResNet34\nMobileNetV3 / EffNet-B0", "#dcfce7", None)
    box(8.8, 3.75, 3.4, 1.3, "训练管理模块\n后台线程 · 实时日志\n自动重载模型", "#dcfce7", None)
    # 数据层
    box(0.4, 0.8, 12.2, 2.0, "数据层",
        "#fed7aa", "文件系统：上传图像 / 数据集 / 模型权重 / 日志     SQLite：识别记录 · 特征向量 · 训练任务")
    box(0.8, 1.15, 4.6, 1.15, "文件存储\nuploads/ · data/ · models/", "#ffedd5", None)
    box(5.9, 1.15, 4.6, 1.15, "SQLite 数据库 system.db\nrecords · features · train_jobs", "#ffedd5", None)
    # 箭头
    arrow(6.5, 6.2, 6.5, 5.6, "HTTP 请求 / JSON 响应")
    arrow(6.5, 3.4, 6.5, 2.8, "SQL 读写 · 文件存取")
    arrow(8.0, 5.9, 9.5, 5.9, "训练指令")
    ax.set_title("基于深度学习的图像分类识别系统——总体架构", fontsize=15, pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "architecture.png"), bbox_inches="tight")
    plt.close(fig)
    print("architecture ok")

def structure():
    tree = """智能系统设计与实践/
├── app/                     # Web 服务
│   ├── app.py               # Flask 入口：页面路由与 REST API
│   ├── db.py                # SQLite 存储层（记录/特征/训练任务）
│   ├── templates/
│   │   ├── index.html       # 识别台页面
│   │   └── admin.html       # 管理后台页面
│   └── static/
│       ├── style.css        # 全局样式
│       ├── app.js           # 识别台交互逻辑
│       └── admin.js         # 管理后台交互逻辑
├── scripts/
│   ├── build_dataset.py     # 数据集解压、命名与 6:2:2 分层划分
│   ├── train.py             # 迁移学习训练与微调
│   ├── evaluate.py          # 测试集评估与图表生成
│   ├── make_figures_extra.py# 数据示例图/预测样例图
│   └── capture_demo.py      # 系统截图与演示视频录制
├── data/
│   ├── flower102/           # 数据集：train/val/test 各 102 类
│   └── system.db            # SQLite 业务数据库
├── models/                  # 训练好的模型权重（*_best.pt）
├── results/                 # 评估指标 JSON
├── figures/                 # 分析图表
├── runs/                    # 训练日志、页面截图、演示视频
├── uploads/                 # 用户上传图像
└── docs/                    # 设计报告"""
    fig, ax = plt.subplots(figsize=(11.5, 9.5), dpi=160)
    ax.axis("off")
    ax.text(0.02, 0.98, tree, va="top", ha="left", fontsize=11.5, family="monospace", linespacing=1.35)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "structure.png"), bbox_inches="tight")
    plt.close(fig)
    print("structure ok")

if __name__ == "__main__":
    architecture()
    structure()
