# 基于深度学习的图像分类识别系统（花卉 102 类）

《智能系统设计与实践》课程项目：构建一个基于深度模型的图像分类与识别系统。

- 前端：Web 页面，支持上传图像、选择不同深度模型、Top-5 识别结果展示、识别历史浏览
- 后端：模型训练与微调、特征向量存储、识别记录存储、后台管理界面
- 数据集：Oxford 102 Category Flower（102 类、8189 张），按 6:2:2 划分训练/验证/测试集
- 模型：ResNet18 / ResNet34 / MobileNetV3-Large / EfficientNet-B0 迁移学习微调对比
- 结果分析：准确率、混淆矩阵、类别敏感度分析（图表齐全）

## 目录结构
```
├── app/            # Flask 后端 + 前端页面
│   ├── app.py      # 服务入口（API + 页面路由）
│   ├── db.py       # SQLite 存储层
│   ├── templates/  # index.html / admin.html
│   └── static/     # css / js
├── scripts/        # 数据构建、训练、评估、图表、演示录制脚本
├── data/           # 数据集（flower102）与数据库
├── models/         # 训练好的模型权重
├── results/        # 评估指标 JSON
├── figures/        # 分析图表
├── runs/           # 训练日志、截图、演示视频
├── uploads/        # 用户上传图像
└── docs/           # 设计报告
```

## 快速开始
```bash
# 1. 安装依赖
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python torch torchvision
uv pip install --python .venv/bin/python -r requirements.txt

# 2. 构建数据集（需先下载 data/102flowers.tgz 与 data/imagelabels.mat）
.venv/bin/python scripts/build_dataset.py

# 3. 训练模型
.venv/bin/python scripts/train.py --model resnet18 --epochs 15
.venv/bin/python scripts/train.py --model efficientnet_b0 --epochs 15

# 4. 评估并生成图表
.venv/bin/python scripts/evaluate.py --models resnet18,resnet34,mobilenet_v3_large,efficientnet_b0

# 5. 启动系统
.venv/bin/python app/app.py          # http://127.0.0.1:8000
```
识别台：http://127.0.0.1:8000/ 　管理后台：http://127.0.0.1:8000/admin

## 数据集来源
Oxford 102 Category Flower Dataset
https://www.robots.ox.ac.uk/~vgg/data/flowers/102/
