# -*- coding: utf-8 -*-
"""SQLite 存储层：识别记录、特征向量、训练任务"""
import os, sqlite3, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "system.db")

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS records(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT, stored_path TEXT, model TEXT,
            top1 TEXT, top1_prob REAL, top5 TEXT,
            image_size TEXT, user_ip TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS features(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER, model TEXT, dim INTEGER, vector TEXT,
            FOREIGN KEY(record_id) REFERENCES records(id));
        CREATE TABLE IF NOT EXISTS train_jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT, epochs INTEGER, status TEXT, log TEXT,
            best_val_acc REAL, started_at TEXT, finished_at TEXT);
        """)

def add_record(filename, stored_path, model, top1, top1_prob, top5, image_size, user_ip):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn() as c:
        cur = c.execute("INSERT INTO records(filename,stored_path,model,top1,top1_prob,top5,image_size,user_ip,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (filename, stored_path, model, top1, top1_prob, json.dumps(top5, ensure_ascii=False), image_size, user_ip, now))
        return cur.lastrowid

def add_feature(record_id, model, vector):
    with conn() as c:
        c.execute("INSERT INTO features(record_id,model,dim,vector) VALUES(?,?,?,?)",
                  (record_id, model, len(vector), json.dumps(vector)))

def list_records(model=None, limit=100, offset=0):
    q = "SELECT * FROM records"; args = []
    if model and model != "all":
        q += " WHERE model=?"; args.append(model)
    q += " ORDER BY id DESC LIMIT ? OFFSET ?"; args += [limit, offset]
    with conn() as c:
        rows = [dict(r) for r in c.execute(q, args).fetchall()]
    for r in rows:
        r["top5"] = json.loads(r["top5"])
    return rows

def get_record(rid):
    with conn() as c:
        r = c.execute("SELECT * FROM records WHERE id=?", (rid,)).fetchone()
        if not r: return None
        d = dict(r); d["top5"] = json.loads(d["top5"])
        feats = c.execute("SELECT id,model,dim,vector FROM features WHERE record_id=?", (rid,)).fetchall()
        d["features"] = [{"id": f["id"], "model": f["model"], "dim": f["dim"],
                          "vector": json.loads(f["vector"])} for f in feats]
        return d

def stats():
    with conn() as c:
        n_records = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        n_features = c.execute("SELECT COUNT(*) FROM features").fetchone()[0]
        today = datetime.date.today().isoformat()
        n_today = c.execute("SELECT COUNT(*) FROM records WHERE created_at LIKE ?", (today + "%",)).fetchone()[0]
        by_model = {r["model"]: r["n"] for r in c.execute("SELECT model, COUNT(*) n FROM records GROUP BY model").fetchall()}
        return {"records": n_records, "features": n_features, "today": n_today, "by_model": by_model}

def add_train_job(model, epochs):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn() as c:
        cur = c.execute("INSERT INTO train_jobs(model,epochs,status,log,started_at) VALUES(?,?,'running','',?)", (model, epochs, now))
        return cur.lastrowid

def update_train_job(jid, status, log=None, best=None):
    with conn() as c:
        if best is not None:
            c.execute("UPDATE train_jobs SET status=?, log=?, best_val_acc=?, finished_at=? WHERE id=?",
                      (status, log, best, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), jid))
        else:
            c.execute("UPDATE train_jobs SET log=? WHERE id=?", (log, jid))

def list_train_jobs(limit=20):
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM train_jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
