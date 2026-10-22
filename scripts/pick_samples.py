# -*- coding: utf-8 -*-
"""为演示挑选每个类别中模型置信度最高的测试图像，输出 samples.json"""
import os, json, glob, torch, torchvision
from PIL import Image
from torchvision import transforms

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "runs", "samples.json")
tf = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
                         transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
ck = torch.load(os.path.join(ROOT, "models", "resnet18_best.pt"), map_location="cpu")
classes = ck["classes"]
m = torchvision.models.resnet18(weights=None)
m.fc = torch.nn.Linear(m.fc.in_features, len(classes))
m.load_state_dict(ck["state_dict"])
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
m.to(DEV).eval()

want = ["rose","sunflower","siam tulip","water lily","hibiscus","daffodil",
        "canna lily","gazania","columbine","snapdragon","tiger lily","fritillary"]
chosen = []
for cls in want:
    d = os.path.join(ROOT, "data", "flower102", "test", cls)
    if not os.path.isdir(d):
        continue
    files = sorted(glob.glob(os.path.join(d, "*.jpg")))
    best_score, best_file, best_top = -1, None, None
    for f in files:
        img = Image.open(f).convert("RGB")
        with torch.no_grad():
            out = m(tf(img).unsqueeze(0).to(DEV))
            p = torch.softmax(out, 1)[0]
        pred = classes[int(p.argmax())]
        if pred == cls and float(p.max()) > best_score:
            best_score, best_file, best_top = float(p.max()), f, [(classes[i], float(p[i])) for i in p.argsort(descending=True)[:5]]
    if best_file:
        chosen.append({"class": cls, "path": best_file, "top1_prob": best_score, "top5": best_top})
        print(f"{cls:16s} {os.path.basename(best_file)} {best_score:.3f}")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(chosen, f, ensure_ascii=False, indent=2)
print("saved", OUT, "n =", len(chosen))
