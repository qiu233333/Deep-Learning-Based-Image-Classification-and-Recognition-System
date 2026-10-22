# -*- coding: utf-8 -*-
"""基于深度学习的图像分类识别系统 —— Flask 后端服务"""
import os, io, json, time, threading, subprocess, sys, datetime
from PIL import Image
import torch
from torchvision import transforms
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import db

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, "models")
RUNS_DIR = os.path.join(ROOT, "runs")
RESULTS_DIR = os.path.join(ROOT, "results")
UPLOAD_DIR = os.path.join(ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
db.init_db()

app = Flask(__name__)
CORS(app)

IMAGE_SIZE = 224
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

def build_model(name, num_classes):
    import torchvision
    mf = {
        "resnet18": (torchvision.models.resnet18, torchvision.models.ResNet18_Weights.IMAGENET1K_V1),
        "resnet34": (torchvision.models.resnet34, torchvision.models.ResNet34_Weights.IMAGENET1K_V1),
        "mobilenet_v3_large": (torchvision.models.mobilenet_v3_large, torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V1),
        "efficientnet_b0": (torchvision.models.efficientnet_b0, torchvision.models.EfficientNet_B0_Weights.IMAGENET1K_V1),
        "densenet121": (torchvision.models.densenet121, torchvision.models.DenseNet121_Weights.IMAGENET1K_V1),
    }
    fn, weights = mf[name]
    m = fn(weights=weights)
    if name.startswith("resnet"):
        m.fc = torch.nn.Linear(m.fc.in_features, num_classes)
    elif name.startswith("mobilenet_v3"):
        m.classifier[3] = torch.nn.Linear(m.classifier[3].in_features, num_classes)
    elif name.startswith("efficientnet"):
        m.classifier[1] = torch.nn.Linear(m.classifier[1].in_features, num_classes)
    else:
        m.classifier = torch.nn.Linear(m.classifier.in_features, num_classes)
    return m

REGISTRY = {}          # name -> {model, classes, meta}
KNOWN_MODELS = {"resnet18", "resnet34", "mobilenet_v3_large", "efficientnet_b0", "densenet121"}
def load_registry():
    global REGISTRY
    REGISTRY = {}
    for f in sorted(os.listdir(MODELS_DIR)):
        if not f.endswith("_best.pt"):
            continue
        name = f[:-len("_best.pt")]
        if name not in KNOWN_MODELS:
            continue
        ck = torch.load(os.path.join(MODELS_DIR, f), map_location="cpu")
        model = build_model(name, len(ck["classes"]))
        model.load_state_dict(ck["state_dict"])
        model.to(DEVICE).eval()
        eval_file = os.path.join(RESULTS_DIR, f"eval_{name}.json")
        metrics = {}
        if os.path.exists(eval_file):
            metrics = json.load(open(eval_file, encoding="utf-8"))
        REGISTRY[name] = {"model": model, "classes": ck["classes"], "val_acc": ck.get("val_acc", 0), "metrics": metrics}
    print("registry:", list(REGISTRY.keys()))

def extract_feature(model, name, x):
    """通过前向 hook 获取分类层之前的特征向量（特征存储）"""
    head = model.fc if name.startswith("resnet") else model.classifier
    feat = {}
    def hook(module, inp, out):
        feat["v"] = inp[0].detach().cpu().numpy()
    h = head.register_forward_hook(hook)
    with torch.no_grad():
        model(x)
    h.remove()
    return feat["v"][0]

TF = transforms.Compose([
    transforms.Resize(int(IMAGE_SIZE * 1.14)),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])

def predict(model_name, pil_image):
    reg = REGISTRY[model_name]
    model = reg["model"]
    x = TF(pil_image.convert("RGB")).unsqueeze(0).to(DEVICE)
    feat = extract_feature(model, model_name, x)
    with torch.no_grad():
        with torch.autocast(device_type=DEVICE, dtype=torch.float16, enabled=(DEVICE == "mps")):
            out = model(x)
        probs = torch.softmax(out, dim=1).cpu().numpy()[0]
    order = probs.argsort()[::-1][:5]
    top5 = [{"label": reg["classes"][i], "prob": round(float(probs[i]), 4)} for i in order]
    feature = [round(float(v), 4) for v in feat.tolist()]
    return top5, feature

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/uploads/<path:fn>")
def uploaded(fn):
    return send_from_directory(UPLOAD_DIR, fn)

@app.get("/api/models")
def api_models():
    out = []
    for name, reg in REGISTRY.items():
        m = reg.get("metrics", {})
        out.append({"name": name, "classes": len(reg["classes"]),
                    "val_acc": round(float(reg["val_acc"]), 4),
                    "top1": m.get("top1"), "top5": m.get("top5"),
                    "params_M": m.get("params_M"), "infer_ms": m.get("infer_ms")})
    return jsonify(out)

@app.post("/api/classify")
def api_classify():
    if "image" not in request.files:
        return jsonify({"error": "缺少图像文件"}), 400
    model_name = request.form.get("model", "resnet18")
    if model_name not in REGISTRY:
        return jsonify({"error": f"模型 {model_name} 未加载"}), 400
    f = request.files["image"]
    if f.filename == "":
        return jsonify({"error": "空文件名"}), 400
    try:
        pil = Image.open(io.BytesIO(f.read())).convert("RGB")
    except Exception:
        return jsonify({"error": "无法解析图像"}), 400
    t0 = time.time()
    top5, feature = predict(model_name, pil)
    cost_ms = (time.time() - t0) * 1000
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    ext = (f.filename.rsplit(".", 1)[-1] or "jpg").lower()
    if ext not in ("jpg", "jpeg", "png", "webp", "bmp"):
        ext = "jpg"
    stored = f"{stamp}.{ext}"
    pil.save(os.path.join(UPLOAD_DIR, stored))
    rid = db.add_record(f.filename, f"uploads/{stored}", model_name, top5[0]["label"], top5[0]["prob"],
                        top5, f"{pil.size[0]}x{pil.size[1]}", request.remote_addr or "local")
    db.add_feature(rid, model_name, feature)
    return jsonify({"record_id": rid, "top5": top5, "top1": top5[0],
                    "cost_ms": round(cost_ms, 1), "stored": f"/uploads/{stored}"})

@app.get("/api/records")
def api_records():
    model = request.args.get("model", "all")
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))
    return jsonify(db.list_records(model, limit, offset))

@app.get("/api/record/<int:rid>")
def api_record(rid):
    r = db.get_record(rid)
    return jsonify(r) if r else (jsonify({"error": "not found"}), 404)

@app.get("/api/stats")
def api_stats():
    s = db.stats()
    dataset = {}
    stats_file = os.path.join(ROOT, "data", "flower102_stats.json")
    if os.path.exists(stats_file):
        ds = json.load(open(stats_file, encoding="utf-8"))
        dataset = {"total": ds["total"], "num_classes": ds["num_classes"], "split": ds["split"]}
    return jsonify({**s, "dataset": dataset, "models": len(REGISTRY)})

@app.post("/api/train")
def api_train():
    data = request.get_json(force=True)
    model_name = data.get("model", "resnet18")
    epochs = min(int(data.get("epochs", 5)), 30)
    jid = db.add_train_job(model_name, epochs)
    def run():
        script = os.path.join(ROOT, "scripts", "train.py")
        venv_py = os.path.join(ROOT, ".venv", "bin", "python")
        py = venv_py if os.path.exists(venv_py) else sys.executable
        log = ""
        try:
            proc = subprocess.Popen([py, script, "--model", model_name, "--epochs", str(epochs), "--tag", f"job{jid}"],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
            for line in proc.stdout:
                log += line
                db.update_train_job(jid, "running", log[-4000:])
            proc.wait()
            best = None
            ck_path = os.path.join(MODELS_DIR, f"{model_name}_job{jid}_best.pt")
            if proc.returncode == 0 and os.path.exists(ck_path):
                best = float(torch.load(ck_path, map_location="cpu").get("val_acc", 0))
            db.update_train_job(jid, "done" if proc.returncode == 0 else "failed", log[-4000:], best)
            load_registry()
        except Exception as e:
            db.update_train_job(jid, "failed", str(e))
    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": jid, "message": "训练任务已启动，请到日志区查看进度"})

@app.get("/api/train_jobs")
def api_train_jobs():
    return jsonify(db.list_train_jobs(20))

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "device": DEVICE, "models": list(REGISTRY.keys())})

load_registry()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False, threaded=True)
