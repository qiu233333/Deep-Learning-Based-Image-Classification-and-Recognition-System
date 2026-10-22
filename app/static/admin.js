const $ = (s) => document.querySelector(s);
async function loadStats() {
  const s = await (await fetch("/api/stats")).json();
  $("#statCards").innerHTML = `
    <div class="stat-card"><div class="num">${s.dataset.total ?? "—"}</div><div class="lbl">数据集图像总数（${s.dataset.num_classes ?? "—"} 类）</div></div>
    <div class="stat-card"><div class="num">${s.models}</div><div class="lbl">已加载深度模型</div></div>
    <div class="stat-card"><div class="num">${s.records}</div><div class="lbl">识别记录总数（今日 +${s.today}）</div></div>
    <div class="stat-card"><div class="num">${s.features}</div><div class="lbl">已存储特征向量</div></div>`;
  const ds = s.dataset;
  if (ds && ds.split) {
    $("#datasetStats").textContent = `训练集 ${ds.split.train} 张（60%）｜ 验证集 ${ds.split.val} 张（20%）｜ 测试集 ${ds.split.test} 张（20%）｜ 共 ${ds.total} 张`;
  }
  const sel = $("#recordModel");
  const models = await (await fetch("/api/models")).json();
  models.forEach(m => sel.insertAdjacentHTML("beforeend", `<option value="${m.name}">${m.name}</option>`));
}
async function loadRecords() {
  const m = $("#recordModel").value;
  const rows = await (await fetch("/api/records?model=" + m + "&limit=100")).json();
  const tb = $("#recordRows");
  tb.innerHTML = "";
  rows.forEach(async r => {
    const detail = await (await fetch("/api/record/" + r.id)).json();
    const dim = detail.features?.length ? detail.features[0].dim : "—";
    tb.insertAdjacentHTML("beforeend", `<tr>
      <td>#${r.id}</td><td style="max-width:220px;overflow:hidden;text-overflow:ellipsis">${r.filename}</td>
      <td>${r.model}</td><td>${r.top1}</td><td>${(r.top1_prob*100).toFixed(2)}%</td>
      <td>${r.image_size}</td><td>${dim} 维</td><td>${r.created_at}</td></tr>`);
  });
}
async function loadJobs() {
  const jobs = await (await fetch("/api/train_jobs")).json();
  const tb = $("#jobsTable tbody");
  tb.innerHTML = "";
  jobs.forEach(j => {
    const cls = j.status === "done" ? "tag-ok" : j.status === "failed" ? "tag-fail" : "tag-run";
    tb.insertAdjacentHTML("beforeend", `<tr>
      <td>#${j.id}</td><td>${j.model}</td><td>${j.epochs}</td>
      <td class="${cls}">${j.status}</td>
      <td>${j.best_val_acc != null ? (j.best_val_acc*100).toFixed(2)+"%" : "—"}</td>
      <td>${j.started_at || "—"}</td></tr>`);
  });
  const last = jobs[0];
  if (last) $("#trainLog").textContent = last.log || "（运行中……）";
}
$("#trainBtn").onclick = async () => {
  const model = $("#trainModel").value, epochs = $("#trainEpochs").value;
  $("#trainLog").textContent = "正在提交训练任务……";
  const res = await fetch("/api/train", { method: "POST", headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ model, epochs: +epochs }) });
  const d = await res.json();
  $("#trainLog").textContent = d.message;
  poll();
};
let pollTimer = null;
function poll() { clearInterval(pollTimer); pollTimer = setInterval(async () => {
  const jobs = await (await fetch("/api/train_jobs")).json();
  const running = jobs.some(j => j.status === "running");
  const last = jobs[0];
  if (last) $("#trainLog").textContent = last.log || "（运行中……）";
  loadJobs(); loadStats();
  if (!running) clearInterval(pollTimer);
}, 2500); }
$("#recordRefresh").onclick = loadRecords;
$("#recordModel").onchange = loadRecords;
loadStats(); loadRecords(); loadJobs(); poll();
