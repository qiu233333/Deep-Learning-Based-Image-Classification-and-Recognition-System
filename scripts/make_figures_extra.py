# -*- coding: utf-8 -*-
"""额外图表：数据集示例网格 + 模型预测样例（正确/错误）+ 类别样本分布"""
import os, json, glob, random
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "flower102")
FIG = os.path.join(ROOT, "figures")
MODELS_DIR = os.path.join(ROOT, "models")
os.makedirs(FIG, exist_ok=True)
for cand in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc",
             "/System/Library/Fonts/Hiragino Sans GB.ttc", "/Library/Fonts/Arial Unicode.ttf"]:
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "Heiti SC"]
plt.rcParams["axes.unicode_minus"] = False

def dataset_grid():
    classes = sorted(os.listdir(os.path.join(DATA, "train")))
    sel = classes[:25]
    fig, axes = plt.subplots(5, 5, figsize=(16, 15), dpi=160)
    rng = random.Random(7)
    for ax, cls in zip(axes.ravel(), sel):
        files = sorted(glob.glob(os.path.join(DATA, "train", cls, "*.jpg")))
        f = rng.choice(files)
        ax.imshow(Image.open(f))
        ax.set_title(cls, fontsize=12)
        ax.axis("off")
    fig.suptitle("数据集示例：25 个花卉类别（每类随机 1 张训练图像）", fontsize=18, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(FIG, "dataset_samples.png"), bbox_inches="tight")
    plt.close(fig)
    print("dataset grid ok")

def dist_plot():
    stats = json.load(open(os.path.join(ROOT, "data", "flower102_stats.json")))
    names = stats["class_names"]
    per = stats["per_class"]
    tot = [per[n]["total"] for n in names]
    order = np.argsort(tot)
    fig, axes = plt.subplots(1, 2, figsize=(17, 6), dpi=150)
    axes[0].barh(range(len(names)), [tot[i] for i in order], color="tab:cyan")
    axes[0].set_yticks(range(len(names)))
    axes[0].set_yticklabels([names[i] for i in order], fontsize=7)
    axes[0].set_xlabel("图像数量（总）")
    axes[0].set_title("各花卉类别图像数量分布（102 类）")
    axes[1].pie([stats["split"]["train"], stats["split"]["val"], stats["split"]["test"]],
                labels=["训练集 60%", "验证集 20%", "测试集 20%"], autopct="%1.1f%%",
                colors=["#4dabf7", "#69db7c", "#ffa94d"], startangle=90,
                textprops={"fontsize": 13})
    axes[1].set_title(f"6:2:2 数据集划分（共 {stats['total']} 张）")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "dataset_dist.png"), bbox_inches="tight")
    plt.close(fig)
    print("dist ok")

def build_model(name, num_classes):
    import torchvision
    mf = {
        "resnet18": (torchvision.models.resnet18, torchvision.models.ResNet18_Weights.IMAGENET1K_V1),
        "resnet34": (torchvision.models.resnet34, torchvision.models.ResNet34_Weights.IMAGENET1K_V1),
        "mobilenet_v3_large": (torchvision.models.mobilenet_v3_large, torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V1),
        "efficientnet_b0": (torchvision.models.efficientnet_b0, torchvision.models.EfficientNet_B0_Weights.IMAGENET1K_V1),
        "densenet121": (torchvision.models.densenet121, torchvision.models.DenseNet121_Weights.IMAGENET1K_V1),
    }
    fn, w = mf[name]
    m = fn(weights=w)
    if name.startswith("resnet"): m.fc = torch.nn.Linear(m.fc.in_features, num_classes)
    elif name.startswith("mobilenet_v3"): m.classifier[3] = torch.nn.Linear(m.classifier[3].in_features, num_classes)
    elif name.startswith("efficientnet"): m.classifier[1] = torch.nn.Linear(m.classifier[1].in_features, num_classes)
    else: m.classifier = torch.nn.Linear(m.classifier.in_features, num_classes)
    return m

def pred_grid(model_name):
    ck = torch.load(os.path.join(MODELS_DIR, f"{model_name}_best.pt"), map_location="cpu")
    classes = ck["classes"]
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    m = build_model(model_name, len(classes)); m.load_state_dict(ck["state_dict"]); m.to(device).eval()
    tf = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
                             transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    test_dir = os.path.join(DATA, "test")
    cls_list = sorted(os.listdir(test_dir))
    correct, wrong = [], []
    rng = random.Random(3)
    files = [os.path.join(test_dir, c, f) for c in cls_list for f in os.listdir(os.path.join(test_dir, c))]
    rng.shuffle(files)
    for path in files:
        if len(correct) >= 6 and len(wrong) >= 6:
            break
        true = cls_list.index(os.path.basename(os.path.dirname(path)))
        img = Image.open(path).convert("RGB")
        x = tf(img).unsqueeze(0).to(device)
        with torch.no_grad():
            out = m(x)
            p = torch.softmax(out, 1)[0]
        pred = int(p.argmax())
        prob = float(p.max())
        item = (path, true, pred, prob)
        if pred == true and len(correct) < 6: correct.append(item)
        if pred != true and len(wrong) < 6: wrong.append(item)
    fig, axes = plt.subplots(2, 6, figsize=(20, 7), dpi=150)
    for ax, (path, t, p, prob) in zip(axes[0], correct):
        ax.imshow(Image.open(path)); ax.axis("off")
        ax.set_title(f"真实:{classes[t]}\n预测:{classes[p]} {prob*100:.1f}%", fontsize=10, color="green")
    for ax, (path, t, p, prob) in zip(axes[1], wrong):
        ax.imshow(Image.open(path)); ax.axis("off")
        ax.set_title(f"真实:{classes[t]}\n预测:{classes[p]} {prob*100:.1f}%", fontsize=10, color="red")
    fig.suptitle(f"{model_name} 识别样例（上：正确 / 下：错误）", fontsize=16, y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, f"samples_{model_name}.png"), bbox_inches="tight")
    plt.close(fig)
    print("pred grid ok:", model_name)

if __name__ == "__main__":
    dataset_grid()
    dist_plot()
    pred_grid("resnet18")
    pred_grid("efficientnet_b0")
