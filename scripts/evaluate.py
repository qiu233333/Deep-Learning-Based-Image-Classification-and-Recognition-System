# -*- coding: utf-8 -*-
"""测试集评估：准确率/Top-5/混淆矩阵/各类别指标/推理延迟 + 图表生成"""
import os, json, time, argparse
import numpy as np
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "flower102")
MODELS_DIR = os.path.join(ROOT, "models")
RUNS_DIR = os.path.join(ROOT, "runs")
RESULTS = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
os.makedirs(RESULTS, exist_ok=True); os.makedirs(FIG, exist_ok=True)

# 中文字体
for cand in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc",
             "/System/Library/Fonts/Hiragino Sans GB.ttc", "/Library/Fonts/Arial Unicode.ttf"]:
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
        print("font:", cand)
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "Heiti SC"]
plt.rcParams["axes.unicode_minus"] = False

import torchvision

def build_model(name, num_classes):
    mf = {
        "resnet18": (torchvision.models.resnet18, torchvision.models.ResNet18_Weights.IMAGENET1K_V1),
        "resnet34": (torchvision.models.resnet34, torchvision.models.ResNet34_Weights.IMAGENET1K_V1),
        "mobilenet_v3_large": (torchvision.models.mobilenet_v3_large, torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V1),
        "efficientnet_b0": (torchvision.models.efficientnet_b0, torchvision.models.EfficientNet_B0_Weights.IMAGENET1K_V1),
        "densenet121": (torchvision.models.densenet121, torchvision.models.DenseNet121_Weights.IMAGENET1K_V1),
    }
    fn, weights = mf[name]
    model = fn(weights=weights)
    if name.startswith("resnet"):
        model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    elif name.startswith("mobilenet_v3"):
        model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, num_classes)
    elif name.startswith("efficientnet"):
        model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)
    else:
        model.classifier = torch.nn.Linear(model.classifier.in_features, num_classes)
    return model

def load_ckpt(name, device):
    ck = torch.load(os.path.join(MODELS_DIR, f"{name}_best.pt"), map_location="cpu")
    classes = ck["classes"]
    model = build_model(name, len(classes))
    model.load_state_dict(ck["state_dict"])
    model.to(device).eval()
    return model, classes, ck

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="resnet18,resnet34,mobilenet_v3_large,efficientnet_b0")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--image-size", type=int, default=224)
    args = ap.parse_args()
    names = [m.strip() for m in args.models.split(",") if m.strip()]
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print("device:", device)

    eval_tf = transforms.Compose([
        transforms.Resize(int(args.image_size * 1.14)),
        transforms.CenterCrop(args.image_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    test_ds = datasets.ImageFolder(os.path.join(DATA, "test"), eval_tf)
    test_ld = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True)
    print("test images:", len(test_ds))

    summary = {}
    for name in names:
        model, classes, ck = load_ckpt(name, device)
        n_params = sum(p.numel() for p in model.parameters())
        y_true, y_pred, y_score = [], [], []
        latency = []
        with torch.no_grad():
            for x, y in test_ld:
                x = x.to(device)
                t0 = time.time()
                with torch.autocast(device_type=device, dtype=torch.float16, enabled=(device == "mps")):
                    out = model(x)
                if device == "mps":
                    torch.mps.synchronize()
                latency.append(time.time() - t0)
                y_true.extend(y.tolist()); y_pred.extend(out.argmax(1).cpu().tolist())
                y_score.extend(out.cpu().numpy())
        y_true = np.array(y_true); y_pred = np.array(y_pred); y_score = np.array(y_score)
        top1 = accuracy_score(y_true, y_pred)
        top5 = np.mean([1 if t in s.argsort()[::-1][:5] else 0 for t, s in zip(y_true, y_score)])
        cm = confusion_matrix(y_true, y_pred, labels=list(range(len(classes))))
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=list(range(len(classes))), zero_division=0)
        lat = np.array(latency); per_img = lat.sum() / len(test_ds) * 1000
        rec = {
            "model": name, "top1": float(top1), "top5": float(top5),
            "params_M": round(n_params / 1e6, 2),
            "ckpt_MB": round(os.path.getsize(os.path.join(MODELS_DIR, f"{name}_best.pt")) / 1e6, 2),
            "infer_ms": float(per_img), "val_acc": float(ck.get("val_acc", 0)),
            "per_class": {classes[i]: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f1[i])} for i in range(len(classes))},
            "confusion_matrix": cm.tolist(),
            "history_file": f"runs/{name}_history.json",
        }
        with open(os.path.join(RESULTS, f"eval_{name}.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        summary[name] = rec
        print(f"{name}: top1={top1:.4f} top5={top5:.4f} params={n_params/1e6:.2f}M infer={per_img:.1f}ms")

        # ---- 混淆矩阵热力图 ----
        plt.figure(figsize=(24, 21), dpi=150)
        plt.imshow(cm, cmap="viridis", interpolation="nearest")
        plt.colorbar(fraction=0.046, pad=0.04, label="样本数")
        plt.title(f"{name} 测试集混淆矩阵（102类，Top-1 准确率 {top1*100:.2f}%）", fontsize=20)
        plt.xlabel("预测类别", fontsize=16); plt.ylabel("真实类别", fontsize=16)
        n = len(classes)
        step = max(1, n // 34)
        ticks = list(range(0, n, step))
        plt.xticks(ticks, [classes[i][:12] for i in ticks], rotation=90, fontsize=8)
        plt.yticks(ticks, [classes[i][:12] for i in ticks], fontsize=8)
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"cm_{name}.png"), bbox_inches="tight")
        plt.close()

        # ---- 类别准确率 ----
        ca = np.diag(cm) / np.maximum(cm.sum(1), 1)
        order = np.argsort(ca)
        plt.figure(figsize=(14, 8), dpi=150)
        plt.barh([classes[i] for i in order][:20], ca[order][:20], color="tab:red", label="最低20类")
        plt.barh([classes[i] for i in order][-20:], ca[order][-20:], color="tab:blue", label="最高20类")
        plt.axvline(top1, ls="--", c="k", label=f"整体 {top1*100:.1f}%")
        plt.xlabel("类别准确率", fontsize=13); plt.title(f"{name}：各类别准确率（最低20 vs 最高20）", fontsize=15)
        plt.legend(fontsize=12); plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"class_acc_{name}.png"), bbox_inches="tight")
        plt.close()

    with open(os.path.join(RESULTS, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("summary saved")

    # ---- 训练曲线汇总 ----
    plt.figure(figsize=(16, 6), dpi=150)
    for i, name in enumerate(names, 1):
        hist = json.load(open(os.path.join(RUNS_DIR, f"{name}_history.json")))
        plt.subplot(1, 2, 1)
        plt.plot(hist["epoch"], hist["train_loss"], marker="o", ms=3, label=f"{name}")
        plt.subplot(1, 2, 2)
        plt.plot(hist["epoch"], [a * 100 for a in hist["val_acc"]], marker="o", ms=3, label=f"{name}")
    plt.subplot(1, 2, 1); plt.xlabel("Epoch"); plt.ylabel("训练损失"); plt.title("训练损失曲线"); plt.legend()
    plt.subplot(1, 2, 2); plt.xlabel("Epoch"); plt.ylabel("验证集准确率(%)"); plt.title("验证集准确率曲线"); plt.legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "training_curves.png"), bbox_inches="tight"); plt.close()

    # ---- 模型对比图 ----
    plt.figure(figsize=(14, 5), dpi=150)
    accs = [summary[n]["top1"] * 100 for n in names]
    params = [summary[n]["params_M"] for n in names]
    lats = [summary[n]["infer_ms"] for n in names]
    x = np.arange(len(names)); w = 0.38
    ax = plt.subplot(1, 3, 1); ax.bar(x - w / 2, accs, w, label="Top-1", color="tab:blue")
    ax.bar(x + w / 2, [summary[n]["top5"] * 100 for n in names], w, label="Top-5", color="tab:orange")
    ax.set_xticks(x, names, rotation=20, fontsize=8); ax.set_ylabel("准确率(%)"); ax.set_title("测试集准确率对比"); ax.legend()
    plt.subplot(1, 3, 2); plt.bar(x, params, w, color="tab:green"); plt.xticks(x, names, rotation=20, fontsize=8); plt.ylabel("参数量(M)"); plt.title("模型参数量对比")
    plt.subplot(1, 3, 3); plt.bar(x, lats, w, color="tab:purple"); plt.xticks(x, names, rotation=20, fontsize=8); plt.ylabel("单张推理耗时(ms)"); plt.title("推理延迟对比(MPS)")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "model_compare.png"), bbox_inches="tight"); plt.close()
    print("figures saved")

if __name__ == "__main__":
    main()
