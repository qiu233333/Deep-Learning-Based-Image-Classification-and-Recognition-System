# -*- coding: utf-8 -*-
"""用 Playwright 录制系统演示视频并截取页面截图（需服务已启动）"""
import os, sys, glob, time, shutil
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "runs")
SCREENS = os.path.join(RUNS, "screens")
os.makedirs(SCREENS, exist_ok=True)
BASE = "http://127.0.0.1:8000"

def pick_samples():
    import json as _json
    sj = os.path.join(ROOT, "runs", "samples.json")
    if os.path.exists(sj):
        data = _json.load(open(sj, encoding="utf-8"))
        return [(d["class"], d["path"]) for d in data]
    test = os.path.join(ROOT, "data", "flower102", "test")
    picks = []
    for cls in ["rose", "sunflower", "siam tulip", "water lily", "hibiscus", "daffodil"]:
        d = os.path.join(test, cls)
        if os.path.isdir(d):
            fs = sorted(glob.glob(os.path.join(d, "*.jpg")))
            if fs:
                picks.append((cls, fs[0]))
    return picks

def main():
    samples = pick_samples()
    print("samples:", [(c, os.path.basename(p)) for c, p in samples[:6]])
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800},
                                  record_video_dir=RUNS,
                                  record_video_size={"width": 1280, "height": 800})
        page = ctx.new_page()
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(2600)
        page.screenshot(path=os.path.join(SCREENS, "01_index_initial.png"), full_page=True)

        # 显式选中 resnet18 模型卡片
        for card in page.query_selector_all(".model-card"):
            if "resnet18" in card.inner_text():
                card.click()
                break
        page.wait_for_timeout(500)
        # 上传第一张
        cls, path = samples[0]
        page.set_input_files("#fileInput", path)
        page.wait_for_timeout(1400)
        page.screenshot(path=os.path.join(SCREENS, "02_uploaded.png"), full_page=True)
        page.click("#classifyBtn")
        page.wait_for_selector("#resultPanel:not(.hidden)", timeout=30000)
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(SCREENS, "03_result_resnet18.png"), full_page=True)

        # 切换模型
        for i, (cls, path) in enumerate(samples[1:5], 1):
            model = ["efficientnet_b0", "mobilenet_v3_large", "resnet34", "resnet18"][i - 1]
            for card in page.query_selector_all(".model-card"):
                if model in card.inner_text():
                    card.click()
                    break
            page.wait_for_timeout(900)
            page.set_input_files("#fileInput", path)
            page.wait_for_timeout(1300)
            page.click("#classifyBtn")
            page.wait_for_timeout(3400)
            if i == 1:
                page.screenshot(path=os.path.join(SCREENS, "04_result_efficientnet.png"), full_page=True)
        page.wait_for_timeout(1200)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1800)
        page.screenshot(path=os.path.join(SCREENS, "05_history.png"), full_page=True)

        # 管理后台
        page.goto(BASE + "/admin", wait_until="networkidle")
        page.wait_for_timeout(2600)
        page.screenshot(path=os.path.join(SCREENS, "06_admin_top.png"), full_page=True)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1600)
        page.screenshot(path=os.path.join(SCREENS, "07_admin_records.png"), full_page=True)
        page.wait_for_timeout(1800)
        ctx.close()
        browser.close()

    videos = sorted(glob.glob(os.path.join(RUNS, "*.webm")), key=os.path.getmtime)
    if videos:
        dst = os.path.join(RUNS, "demo.webm")
        shutil.move(videos[-1], dst)
        print("video saved:", dst)
    print("screens in", SCREENS)

if __name__ == "__main__":
    main()
