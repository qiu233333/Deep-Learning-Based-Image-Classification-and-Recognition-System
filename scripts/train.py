# -*- coding: utf-8 -*-
"""迁移学习训练/微调脚本：支持多种深度模型，记录训练曲线，保存最优权重"""
import os, json, time, argparse
import torch
import torch.nn as nn
import torchvision
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "flower102")
MODELS_DIR = os.path.join(ROOT, "models")
RUNS_DIR = os.path.join(ROOT, "runs")
os.makedirs(MODELS_DIR, exist_ok=True); os.makedirs(RUNS_DIR, exist_ok=True)

MODEL_FNS = {
    "resnet18": (torchvision.models.resnet18, torchvision.models.ResNet18_Weights.IMAGENET1K_V1, "fc", 512),
    "resnet34": (torchvision.models.resnet34, torchvision.models.ResNet34_Weights.IMAGENET1K_V1, "fc", 512),
    "mobilenet_v3_large": (torchvision.models.mobilenet_v3_large, torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V1, "classifier", None),
    "efficientnet_b0": (torchvision.models.efficientnet_b0, torchvision.models.EfficientNet_B0_Weights.IMAGENET1K_V1, "classifier", None),
    "densenet121": (torchvision.models.densenet121, torchvision.models.DenseNet121_Weights.IMAGENET1K_V1, "classifier", None),
}

def get_model(name, num_classes):
    fn, weights, head, dim = MODEL_FNS[name]
    model = fn(weights=weights)
    if name.startswith("resnet"):
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif name.startswith("mobilenet_v3"):
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)
    elif name.startswith("efficientnet"):
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    else:
        model.classifier = nn.Linear(model.classifier.in_features, num_classes)
    return model

def replace_head(model, name, num_classes):
    if name.startswith("resnet"):
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif name.startswith("mobilenet_v3"):
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)
    elif name.startswith("efficientnet"):
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    else:
        model.classifier = nn.Linear(model.classifier.in_features, num_classes)
    return model

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="resnet18")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--head-epochs", type=int, default=3, help="仅训练分类头的前N个epoch")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--image-size", type=int, default=224)
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--tag", default="", help="输出文件后缀（在线训练时用于隔离，避免覆盖主权重）")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print("device:", device)

    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(args.image_size, scale=(0.6, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.2, 0.2, 0.2, 0.05),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(int(args.image_size * 1.14)),
        transforms.CenterCrop(args.image_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    train_ds = datasets.ImageFolder(os.path.join(DATA, "train"), train_tf)
    val_ds = datasets.ImageFolder(os.path.join(DATA, "val"), eval_tf)
    classes = train_ds.classes
    num_classes = len(classes)
    print("num_classes:", num_classes)
    train_ld = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, pin_memory=True)
    val_ld = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, pin_memory=True)

    model = get_model(args.model, num_classes).to(device)
    # 第一阶段冻结骨干，仅训练分类头
    replace_head(model, args.model, num_classes)
    head = model.fc if args.model.startswith("resnet") else model.classifier
    head.to(device)
    if args.head_epochs > 0:
        for p in model.parameters():
            p.requires_grad = False
        for p in head.parameters():
            p.requires_grad = True

    optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr * 3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    history = {"epoch": [], "train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "lr": [], "minutes_per_epoch": []}
    best_acc, best_state = 0.0, None

    for epoch in range(1, args.epochs + 1):
        if epoch == args.head_epochs + 1:
            print(f"== epoch {epoch}: 解冻骨干，全量微调 ==")
            for p in model.parameters():
                p.requires_grad = True
            optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)
        model.train()
        t0 = time.time(); tot = corr = 0; losses = []
        for x, y in train_ld:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device, dtype=torch.float16, enabled=(device == "mps")):
                out = model(x)
                loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            tot += y.size(0); corr += (out.argmax(1) == y).sum().item(); losses.append(loss.item())
        train_acc, train_loss = corr / tot, sum(losses) / len(losses)
        model.eval(); vlosses = []; vcorr = vtot = 0
        with torch.no_grad():
            for x, y in val_ld:
                x, y = x.to(device), y.to(device)
                with torch.autocast(device_type=device, dtype=torch.float16, enabled=(device == "mps")):
                    out = model(x)
                vlosses.append(criterion(out, y).item())
                vtot += y.size(0); vcorr += (out.argmax(1) == y).sum().item()
        val_acc, val_loss = vcorr / vtot, sum(vlosses) / len(vlosses)
        scheduler.step(val_acc)
        mpe = (time.time() - t0) / 60
        history["epoch"].append(epoch); history["train_loss"].append(train_loss); history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss); history["val_acc"].append(val_acc)
        history["lr"].append(optimizer.param_groups[0]["lr"]); history["minutes_per_epoch"].append(mpe)
        print(f"[{args.model}] ep {epoch:2d} train_loss {train_loss:.4f} train_acc {train_acc:.4f} | val_loss {val_loss:.4f} val_acc {val_acc:.4f} | {mpe:.2f} min")
        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    suffix = f"_{args.tag}" if args.tag else ""
    torch.save({"model": args.model, "state_dict": best_state, "classes": classes,
                "val_acc": best_acc, "history": history, "image_size": args.image_size},
               os.path.join(MODELS_DIR, f"{args.model}{suffix}_best.pt"))
    torch.save(model.state_dict(), os.path.join(MODELS_DIR, f"{args.model}{suffix}_last.pt"))
    with open(os.path.join(RUNS_DIR, f"{args.model}{suffix}_history.json"), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"best val acc = {best_acc:.4f}")

if __name__ == "__main__":
    main()
