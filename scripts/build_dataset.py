# -*- coding: utf-8 -*-
"""构建花卉102细粒度图像分类数据集：解压、类别命名、6:2:2分层划分"""
import os, json, shutil, tarfile
import numpy as np
from scipy.io import loadmat
from sklearn.model_selection import train_test_split
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TGZ = os.path.join(DATA, "102flowers.tgz")
LABELS_MAT = os.path.join(DATA, "imagelabels.mat")
RAW_DIR = os.path.join(DATA, "flowers_raw")
OUT_DIR = os.path.join(DATA, "flower102")
STATS_JSON = os.path.join(DATA, "flower102_stats.json")

# Flowers-102 官方类别名称 (类别编号 1..102)
CLASS_NAMES = [
    "pink primrose","hard-leaved pocket orchid","canterbury bells","sweet pea",
    "english marigold","tiger lily","moon orchid","bird of paradise","monkshood",
    "globe thistle","snapdragon","colt's foot","king protea","spear thistle",
    "yellow iris","globe-flower","purple coneflower","peruvian lily","balloon flower",
    "giant white arum lily","fire lily","pincushion flower","fritillary","red ginger",
    "grape hyacinth","corn poppy","prince of wales feathers","stemless gentian",
    "artichoke","sweet william","carnation","garden phlox","love in the mist",
    "mexican aster","alpine sea holly","ruby-lipped cattleya","cape flower",
    "great masterwort","siam tulip","lenten rose","barbeton daisy","daffodil",
    "sword lily","poinsettia","bolero deep blue","wallflower","marigold","buttercup",
    "oxeye daisy","common dandelion","petunia","wild pansy","primula","sunflower",
    "pelargonium","bishop of llandaff","gaura","geranium","orange dahlia",
    "pink-yellow dahlia","cautleya spicata","japanese anemone","black-eyed susan",
    "silverbush","californian poppy","osteospermum","spring crocus","bearded iris",
    "windflower","tree poppy","gazania","azalea","water lily","rose","thorn apple",
    "morning glory","passion flower","lotus","toad lily","anthurium","frangipani",
    "clematis","hibiscus","columbine","desert-rose","tree mallow","magnolia",
    "cyclamen","watercress","canna lily","hippeastrum","bee balm","ball moss",
    "foxglove","bougainvillea","camellia","mallow","mexican petunia","bromelia",
    "blanket flower","trumpet creeper","blackberry lily",
]

def main():
    # 1) 解压
    if not os.path.isdir(RAW_DIR):
        os.makedirs(RAW_DIR, exist_ok=True)
        print("extracting", TGZ)
        with tarfile.open(TGZ) as tf:
            tf.extractall(RAW_DIR)
    jpg_dir = os.path.join(RAW_DIR, "jpg")
    assert os.path.isdir(jpg_dir), "jpg dir missing"
    n_images = len([f for f in os.listdir(jpg_dir) if f.endswith(".jpg")])
    print("images:", n_images)

    # 2) 标签
    labels = loadmat(LABELS_MAT)["labels"].ravel().astype(int)   # 1..102, 按文件名编号
    assert labels.shape[0] == n_images, (labels.shape, n_images)

    # 3) 目录
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    for split in ("train", "val", "test"):
        os.makedirs(os.path.join(OUT_DIR, split), exist_ok=True)
        for name in CLASS_NAMES:
            os.makedirs(os.path.join(OUT_DIR, split, name), exist_ok=True)

    # 4) 按类别分层 6:2:2 划分（固定随机种子保证可复现）
    idx_by_class = {c: [] for c in range(1, 103)}
    for i, c in enumerate(labels):
        idx_by_class[int(c)].append(i)
    stats = {"total": n_images, "num_classes": 102,
             "split": {"train": 0, "val": 0, "test": 0},
             "per_class": {}}
    rng = np.random.default_rng(2026)
    for c in range(1, 103):
        ids = idx_by_class[c]
        rng.shuffle(ids)
        n = len(ids)
        n_tr = round(n * 0.6); n_va = round(n * 0.2)
        tr, va, te = ids[:n_tr], ids[n_tr:n_tr + n_va], ids[n_tr + n_va:]
        name = CLASS_NAMES[c - 1]
        counts = {"total": len(ids), "train": len(tr), "val": len(va), "test": len(te)}
        stats["per_class"][name] = counts
        for split, part in (("train", tr), ("val", va), ("test", te)):
            stats["split"][split] += len(part)
            dst = os.path.join(OUT_DIR, split, name)
            for i in part:
                src = os.path.join(jpg_dir, "image_%05d.jpg" % (i + 1))
                shutil.copy(src, os.path.join(dst, "image_%05d.jpg" % (i + 1)))
        print(f"class {c:3d} {name:30s} n={len(ids):4d}")

    with open(STATS_JSON, "w", encoding="utf-8") as f:
        json.dump({"class_names": CLASS_NAMES, **stats}, f, ensure_ascii=False, indent=2)
    print("split:", stats["split"])
    print("saved:", STATS_JSON)

if __name__ == "__main__":
    main()
