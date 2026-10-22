let selectedModel = "resnet18";
let currentFile = null;

const $ = (s) => document.querySelector(s);

async function loadModels() {
  const res = await fetch("/api/models");
  const models = await res.json();
  const list = $("#modelList");
  list.innerHTML = "";
  models.forEach((m, i) => {
    const div = document.createElement("div");
    div.className = "model-card" + (i === 0 ? " selected" : "");
    const acc = m.top1 != null ? (m.top1 * 100).toFixed(1) + "%" : "—";
    div.innerHTML = `<div class="name">${m.name}</div>
      <span class="tag">${m.classes} 类</span>
      <div class="metric">测试集 Top-1：<b>${acc}</b><br>参数：${m.params_M ?? "—"}M · 单张 ${m.infer_ms ?? "—"}ms</div>
      <span class="check">✔</span>`;
    div.onclick = () => {
      document.querySelectorAll(".model-card").forEach(c => c.classList.remove("selected"));
      div.classList.add("selected");
      selectedModel = m.name;
    };
    list.appendChild(div);
  });
  if (models.length) selectedModel = models[0].name;
}

const dz = $("#dropZone"), fi = $("#fileInput"), preview = $("#preview"), dropInner = $("#dropInner"), clearBtn = $("#clearBtn");
dz.onclick = (e) => { if (e.target !== clearBtn) fi.click(); };
fi.onchange = () => { if (fi.files[0]) setFile(fi.files[0]); };
["dragover","dragenter"].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add("drag"); }));
["dragleave","drop"].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove("drag"); }));
dz.addEventListener("drop", e => { if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); });
clearBtn.onclick = (e) => { e.stopPropagation(); setFile(null); };

function setFile(f) {
  currentFile = f;
  if (!f) {
    preview.classList.add("hidden"); dropInner.classList.remove("hidden");
    clearBtn.classList.add("hidden"); fi.value = ""; return;
  }
  const url = URL.createObjectURL(f);
  preview.src = url; preview.classList.remove("hidden");
  dropInner.classList.add("hidden"); clearBtn.classList.remove("hidden");
}

$("#classifyBtn").onclick = async () => {
  if (!currentFile) { setStatus("⚠ 请先选择一张图像", true); return; }
  const btn = $("#classifyBtn"); btn.disabled = true;
  setStatus("⏳ 模型推理中……");
  const fd = new FormData();
  fd.append("image", currentFile);
  fd.append("model", selectedModel);
  try {
    const res = await fetch("/api/classify", { method: "POST", body: fd });
    const data = await res.json();
    if (res.ok) {
      renderResult(data);
      setStatus("✅ 识别完成，结果已存入后台数据库");
      loadHistory();
    } else setStatus("⚠ " + (data.error || "识别失败"), true);
  } catch (err) {
    setStatus("⚠ 网络错误：" + err.message, true);
  }
  btn.disabled = false;
};

function renderResult(data) {
  const panel = $("#resultPanel");
  panel.classList.remove("hidden");
  const top = data.top5[0];
  $("#top1Badge").textContent = `${top.label}  ${(top.prob * 100).toFixed(2)}%`;
  $("#meta").textContent = `模型：${selectedModel} · 记录编号 #${data.record_id} · 推理耗时 ${data.cost_ms} ms · 已保存特征向量`;
  const bars = $("#bars");
  bars.innerHTML = "";
  data.top5.forEach((r, i) => {
    const row = document.createElement("div");
    row.className = "bar-row" + (i === 0 ? " top" : "");
    row.innerHTML = `<div class="lbl">${r.label}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${(r.prob * 100).toFixed(2)}%"></div></div>
      <div class="pct">${(r.prob * 100).toFixed(2)}%</div>`;
    bars.appendChild(row);
  });
  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function setStatus(msg, warn = false) {
  const s = $("#status");
  s.textContent = msg; s.style.color = warn ? "var(--bad)" : "";
}

async function loadHistory() {
  try {
    const res = await fetch("/api/records?limit=40");
    const rows = await res.json();
    const h = $("#history");
    if (!rows.length) { h.innerHTML = '<div class="empty">暂无识别记录，快去上传第一张图像吧！</div>'; return; }
    h.innerHTML = "";
    rows.forEach(r => {
      const card = document.createElement("div");
      card.className = "hist-card";
      card.innerHTML = `<img src="/${r.stored_path}" alt="${r.top1}">
        <div class="info">
          <div class="r1" title="${r.top1}">${r.top1}</div>
          <div class="r2"><span class="p">${(r.top1_prob * 100).toFixed(1)}%</span> · ${r.model}</div>
          <div class="r2">${r.created_at.slice(5, 16)}</div>
        </div>`;
      h.appendChild(card);
    });
  } catch (e) { console.error(e); }
}

loadModels();
loadHistory();
