# -*- coding: utf-8 -*-
"""
2048 小游戏 · Python 版
=========================================================
运行：python 2048小游戏.py
（在同一目录下双击也可以，或命令行输入上面这行）

运行后会自动打开浏览器窗口开始玩，页面里有两个页面可切换：
    1) 棋局    —— 方向键 / WASD / 鼠标拖动 / 方向按钮 都能操作
    2) 战绩榜  —— 最高分、总局数、最大方块、累计步数、排行榜、最近对局

战绩由这个 Python 程序保存在脚本同目录的 2048_stats.json 里，
换浏览器、清缓存都不会丢。关闭：回到命令行窗口按 Ctrl+C。
=========================================================
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_PATH = os.path.join(BASE_DIR, "2048_stats.json")

DEFAULT_STATS = {
    "best": 0,
    "games": 0,
    "totalScore": 0,
    "totalMoves": 0,
    "maxTile": 0,
    "history": [],
}


def load_stats():
    """读取战绩文件；文件不存在或坏了就给默认值"""
    try:
        with open(STATS_PATH, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, dict):
            data = dict(DEFAULT_STATS)
            data.update(obj)
            data["history"] = data.get("history") or []
            return data
    except (OSError, ValueError):
        pass
    return dict(DEFAULT_STATS)


def save_stats(data):
    """先写临时文件再替换，避免写一半损坏存档"""
    tmp = STATS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATS_PATH)


class Handler(BaseHTTPRequestHandler):
    server_version = "Game2048/1.0"

    def log_message(self, *args):
        pass  # 不刷屏

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            stats = load_stats()
            page = HTML_PAGE.replace(
                "__STATS_JSON__", json.dumps(stats, ensure_ascii=False)
            )
            self._send(200, page.encode("utf-8"))
        elif path == "/api/stats":
            body = json.dumps(load_stats(), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
        elif path == "/favicon.ico":
            self._send(204, b"")
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):
        if urlparse(self.path).path != "/api/stats":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("payload must be object")
            clean = dict(DEFAULT_STATS)
            clean.update(data)
            clean["history"] = (clean.get("history") or [])[:20]
            save_stats(clean)
            self._send(200, b'{"ok":true}', "application/json; charset=utf-8")
        except Exception:
            self._send(400, b'{"ok":false}', "application/json; charset=utf-8")


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2048 · 棋局与战绩</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23171a21'/%3E%3Ctext x='32' y='43' font-size='26' font-family='system-ui,sans-serif' font-weight='700' fill='%23f2c249' text-anchor='middle'%3E2048%3C/text%3E%3C/svg%3E">
<style>
:root{
  --bg:#0e1014;
  --panel:#171a21;
  --panel-2:#1c2029;
  --line:#262b36;
  --text:#e9edf5;
  --muted:#8b93a5;
  --gold:#f2c249;
  --cell:#232833;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--bg);
  color:var(--text);
  font-family:system-ui,-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  min-height:100vh;
  display:flex;
  justify-content:center;
  padding:18px 14px 30px;
  -webkit-tap-highlight-color:transparent;
}
body::before{
  content:"";
  position:fixed;
  inset:-20% -10% auto -10%;
  height:340px;
  background:radial-gradient(60% 100% at 50% 0%,rgba(242,194,73,.10),rgba(242,194,73,0) 70%);
  pointer-events:none;
  z-index:0;
}
.app{width:100%;max-width:480px;position:relative;z-index:1;display:flex;flex-direction:column;gap:16px}

/* ===== 顶栏 ===== */
.topbar{display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{display:flex;align-items:baseline;gap:8px}
.brand h1{margin:0;font-size:26px;letter-spacing:.12em;font-weight:800;font-variant-numeric:tabular-nums}
.brand .dot{width:6px;height:6px;border-radius:50%;background:var(--gold);align-self:center}
.brand .sub{font-size:11px;color:var(--muted);letter-spacing:.16em}
.tabs{display:flex;gap:4px;background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:4px}
.tab{
  display:flex;align-items:center;justify-content:center;
  min-height:36px;padding:0 16px;border-radius:999px;
  font-size:13px;color:var(--muted);text-decoration:none;
  transition:color .18s ease,background .18s ease;
}
.tab.active{color:var(--text);background:var(--panel-2);box-shadow:inset 0 0 0 1px var(--line)}
.tab.active span{color:var(--gold)}

/* ===== 记分 ===== */
.hud{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.stat{
  background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:10px 12px;
}
.stat .label{font-size:11px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}
.stat .value{
  margin-top:2px;font-size:24px;font-weight:700;
  font-variant-numeric:tabular-nums;
  letter-spacing:.02em;
}
.stat.best .value{color:var(--gold)}
.stat .unit{font-size:11px;color:var(--muted);margin-left:4px;font-weight:400}

/* ===== 工具栏 ===== */
.toolbar{display:grid;grid-template-columns:1fr 1fr 44px;gap:8px}
.btn{
  min-height:44px;border-radius:10px;border:1px solid var(--line);
  background:var(--panel);color:var(--text);
  font-size:13px;font-family:inherit;cursor:pointer;
  display:flex;align-items:center;justify-content:center;gap:6px;
  transition:transform .12s ease,border-color .18s ease,background .18s ease;
}
.btn:hover{border-color:#3a4152;background:var(--panel-2)}
.btn:active{transform:translateY(1px)}
.btn.primary{background:var(--gold);color:#211a08;border-color:var(--gold);font-weight:700}
.btn.primary:hover{background:#f7cf6b}
.btn.icon{padding:0}
.btn:disabled{opacity:.4;cursor:not-allowed}

/* ===== 棋盘 ===== */
.board{
  position:relative;
  width:100%;
  aspect-ratio:1/1;
  background:var(--panel-2);
  border:1px solid var(--line);
  border-radius:14px;
  overflow:hidden;
  touch-action:none;
  user-select:none;
}
.cell,.tile{
  position:absolute;top:0;left:0;
  border-radius:8px;
  will-change:transform;
}
.cell{background:var(--cell);transition:none}
.tiles{position:absolute;inset:0}
.tile{transition:transform .13s cubic-bezier(.22,.61,.3,1)}
.tile-inner{
  width:100%;height:100%;
  display:flex;align-items:center;justify-content:center;
  border-radius:8px;
  font-weight:800;
  font-variant-numeric:tabular-nums;
  line-height:1;
  background:#efeada;color:#2b2d33;
  transition:background .15s ease,color .15s ease;
}
.tile-inner.spawn{animation:spawn .16s cubic-bezier(.2,.9,.3,1.2) both}
.tile-inner.pop{animation:pop .2s ease}
.tile-inner.outfade{animation:outfade .17s ease forwards}
@keyframes spawn{from{transform:scale(.25);opacity:.4}to{transform:scale(1);opacity:1}}
@keyframes pop{0%{transform:scale(1)}45%{transform:scale(1.14)}100%{transform:scale(1)}}
@keyframes outfade{to{transform:scale(.9);opacity:0}}

/* ===== 方向键 ===== */
.pad{margin-top:-2px;display:flex;flex-direction:column;align-items:center;gap:6px}
.pad-row{display:flex;gap:6px}
.pad-btn{
  width:56px;height:44px;border-radius:10px;
  border:1px solid var(--line);background:var(--panel);color:var(--muted);
  font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;
}
.pad-btn:hover{color:var(--text);border-color:#3a4152}
.pad-btn:active{background:var(--panel-2);color:var(--gold)}
.tips{font-size:12px;color:var(--muted);text-align:center;line-height:1.7;margin:0}
.tips kbd{
  font-family:inherit;font-size:11px;color:var(--text);
  background:var(--panel);border:1px solid var(--line);
  border-radius:4px;padding:1px 5px;
}

/* ===== 遮罩 ===== */
.modal{
  position:absolute;inset:0;z-index:20;
  display:none;align-items:center;justify-content:center;
  background:rgba(8,10,14,.82);
  backdrop-filter:blur(2px);
  border-radius:14px;
  padding:20px;
}
.modal.show{display:flex;animation:fadein .2s ease}
@keyframes fadein{from{opacity:0}to{opacity:1}}
.modal-box{text-align:center;max-width:300px}
.modal-box h3{margin:0 0 6px;font-size:22px;letter-spacing:.04em;color:var(--gold)}
.modal-box p{margin:0 0 16px;font-size:13px;color:var(--muted);line-height:1.7}
.modal-actions{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
.modal-actions .btn{min-width:104px;padding:0 14px}

/* ===== 战绩页 ===== */
.view{display:flex;flex-direction:column;gap:16px}
.hide{display:none !important}
.section-title{
  display:flex;align-items:center;justify-content:space-between;
  font-size:12px;letter-spacing:.14em;color:var(--muted);
}
.section-title b{color:var(--text);font-weight:600;letter-spacing:.1em}
.grid-4{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.mini{
  background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px;
}
.mini .k{font-size:11px;color:var(--muted);letter-spacing:.1em}
.mini .v{margin-top:4px;font-size:22px;font-weight:700;font-variant-numeric:tabular-nums}
.mini.accent .v{color:var(--gold)}

.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.rank-list{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:6px}
.rank-item{
  display:grid;grid-template-columns:30px 1fr auto;
  align-items:center;gap:10px;
  padding:9px 10px;border-radius:8px;background:var(--panel-2);
  font-variant-numeric:tabular-nums;
}
.rank-item .no{
  font-size:12px;font-weight:700;color:var(--muted);
  text-align:center;height:22px;line-height:22px;border-radius:5px;
}
.rank-item .no.top1{background:var(--gold);color:#211a08}
.rank-item .no.top2{background:#8f97a8;color:#14161b}
.rank-item .no.top3{background:#b4763f;color:#14161b}
.rank-item .meta{font-size:11px;color:var(--muted);margin-top:2px}
.rank-item .sc{font-size:16px;font-weight:700}
.empty{
  padding:22px 0;text-align:center;font-size:13px;color:var(--muted);line-height:1.8;
}
table{width:100%;border-collapse:collapse;table-layout:fixed;margin-top:10px}
col.c1{width:34%}col.c2{width:22%}col.c3{width:24%}col.c4{width:20%}
th{
  font-size:11px;color:var(--muted);font-weight:500;letter-spacing:.08em;
  text-align:left;padding:0 6px 6px;border-bottom:1px solid var(--line);
}
td{
  font-size:13px;padding:8px 6px;border-bottom:1px solid #20242d;
  font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
td.num{text-align:right;padding-right:8px}
th.num{text-align:right;padding-right:8px}
th:last-child,td:last-child{text-align:right}
.rank-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}

@media (max-width:380px){
  .brand h1{font-size:22px}
  .tab{padding:0 12px;font-size:12px}
  .pad-btn{width:50px}
}
@media (min-width:768px){
  body{padding-top:34px}
  .app{max-width:520px;gap:18px}
  .grid-4{grid-template-columns:repeat(4,1fr)}
  .stat .value{font-size:26px}
}
</style>
</head>
<body>
<div class="app">

  <header class="topbar">
    <div class="brand">
      <h1>2048</h1><span class="dot"></span><span class="sub">棋局 / 战绩</span>
    </div>
    <nav class="tabs">
      <a class="tab active" data-view="game" href="#game">棋局</a>
      <a class="tab" data-view="rank" href="#rank">战绩榜</a>
    </nav>
  </header>

  <!-- ===== 视图：棋局 ===== -->
  <main id="view-game" class="view">
    <div class="hud">
      <div class="stat">
        <div class="label">本局得分</div>
        <div class="value" id="score">0</div>
      </div>
      <div class="stat best">
        <div class="label">历史最高</div>
        <div class="value" id="best">0</div>
      </div>
    </div>

    <div class="toolbar">
      <button class="btn primary" id="btn-new" type="button">开新局</button>
      <button class="btn" id="btn-undo" type="button">回退一步</button>
      <button class="btn icon" id="btn-tip" type="button" title="玩法说明">?</button>
    </div>

    <div class="board" id="board" aria-label="2048 棋盘">
      <div class="tiles" id="cells"></div>
      <div class="tiles" id="tiles"></div>
      <div class="modal" id="modal">
        <div class="modal-box">
          <h3 id="modal-title">本局结束</h3>
          <p id="modal-text"></p>
          <div class="modal-actions" id="modal-actions"></div>
        </div>
      </div>
    </div>

    <div class="pad">
      <div class="pad-row"><button class="pad-btn" type="button" data-dir="up">↑</button></div>
      <div class="pad-row">
        <button class="pad-btn" type="button" data-dir="left">←</button>
        <button class="pad-btn" type="button" data-dir="down">↓</button>
        <button class="pad-btn" type="button" data-dir="right">→</button>
      </div>
    </div>

    <p class="tips">
      方向键 / <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> 移动，手机可直接在棋盘上滑动<br>
      <kbd>Z</kbd> 回退一步 · 相同数字相撞即合并
    </p>
  </main>

  <!-- ===== 视图：战绩榜 ===== -->
  <main id="view-rank" class="view hide">
    <div class="grid-4">
      <div class="mini accent"><div class="k">最高分</div><div class="v" id="r-best">0</div></div>
      <div class="mini"><div class="k">总局数</div><div class="v" id="r-games">0</div></div>
      <div class="mini"><div class="k">最大方块</div><div class="v" id="r-tile">0</div></div>
      <div class="mini"><div class="k">累计步数</div><div class="v" id="r-moves">0</div></div>
    </div>

    <section>
      <div class="section-title"><b>个人排行榜</b><span>本地前 8 局</span></div>
      <div class="panel">
        <ul class="rank-list" id="rank-list"></ul>
        <div class="empty" id="rank-empty">还没有战绩，去棋局开一局吧。</div>
      </div>
    </section>

    <section>
      <div class="section-title"><b>最近对局</b><span>保留最近 20 局</span></div>
      <div class="panel">
        <table>
          <colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"></colgroup>
          <thead>
            <tr><th>时间</th><th class="num">得分</th><th class="num">最大方块</th><th class="num">步数</th></tr>
          </thead>
          <tbody id="history-body"></tbody>
        </table>
        <div class="empty" id="history-empty">暂无记录。</div>
      </div>
    </section>

    <div class="rank-actions">
      <button class="btn primary" id="btn-back" type="button">继续下棋</button>
      <button class="btn" id="btn-clear" type="button">清空战绩</button>
    </div>
  </main>
</div>

<script>window.__STATS__ = __STATS_JSON__;</script>
<script>
(function(){
  'use strict';

  var SIZE = 4;
  var KEY = 'game2048.stats.v1';

  var PALETTE = {
    2:['#efeada','#2b2d33'], 4:['#e7ddc6','#2b2d33'], 8:['#f6bd6b','#2a2118'],
    16:['#f2a05a','#2a2118'], 32:['#ee813f','#fff6ea'], 64:['#e35f34','#fff6ea'],
    128:['#d5453a','#ffffff'], 256:['#c03359','#ffffff'], 512:['#a72d7c','#ffffff'],
    1024:['#7e2f9f','#ffffff'], 2048:['#f2c249','#211a08'], 4096:['#3a4bb0','#ffffff'],
    8192:['#2a3d8f','#ffffff'], 16384:['#1e2b63','#ffffff']
  };

  var boardEl   = document.getElementById('board');
  var cellsEl   = document.getElementById('cells');
  var tilesEl   = document.getElementById('tiles');
  var scoreEl   = document.getElementById('score');
  var bestEl    = document.getElementById('best');
  var modal     = document.getElementById('modal');
  var modalTitle= document.getElementById('modal-title');
  var modalText = document.getElementById('modal-text');
  var modalActs = document.getElementById('modal-actions');

  var tiles = [];
  var dying = [];
  var nextId = 1;
  var score = 0;
  var moves = 0;
  var won = false;
  var winShown = false;
  var keepPlaying = false;
  var over = false;
  var recorded = false;
  var startTime = 0;
  var undoStack = [];
  var tileEls = new Map();
  var cellEls = [];
  var stats = loadStats();

  /* ---------- 存档 ---------- */
  // 战绩由 Python 服务端读写：页面打开时注入 window.__STATS__
  function loadStats(){
    var s = window.__STATS__;
    if(s && typeof s === 'object'){
      s.history = s.history || [];
      return s;
    }
    return {best:0, games:0, totalScore:0, totalMoves:0, maxTile:0, history:[]};
  }
  function saveStats(){
    try{
      fetch('/api/stats', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(stats)
      });
    }catch(e){}
  }

  /* ---------- 棋盘绘制 ---------- */
  for(var i=0;i<SIZE*SIZE;i++){
    var cell = document.createElement('div');
    cell.className = 'cell';
    cellsEl.appendChild(cell);
    cellEls.push(cell);
  }

  function metrics(){
    var w = boardEl.clientWidth || 320;
    var gap = Math.round(w * 0.026);
    var cell = (w - gap * (SIZE + 1)) / SIZE;
    return {gap:gap, cell:cell};
  }

  function placeTile(el, t, cell, gap){
    el.style.width = cell + 'px';
    el.style.height = cell + 'px';
    el.style.transform = 'translate(' + (gap + t.c * (cell + gap)) + 'px,' + (gap + t.r * (cell + gap)) + 'px)';
    var inner = el.firstElementChild;
    inner.textContent = t.value;
    var pal = PALETTE[t.value] || PALETTE[16384];
    inner.style.background = pal[0];
    inner.style.color = pal[1];
    var digits = String(t.value).length;
    var ratio = digits <= 2 ? 0.44 : digits === 3 ? 0.36 : digits === 4 ? 0.29 : 0.23;
    inner.style.fontSize = Math.round(cell * ratio) + 'px';
    inner.style.boxShadow = t.value >= 2048 ? '0 0 0 2px rgba(242,194,73,.35) inset' : 'none';
  }

  function ensureTileEl(t, isNew){
    var el = tileEls.get(t.id);
    if(!el){
      el = document.createElement('div');
      el.className = 'tile';
      var inner = document.createElement('div');
      inner.className = 'tile-inner';
      el.appendChild(inner);
      tilesEl.appendChild(el);
      tileEls.set(t.id, el);
      if(isNew) inner.classList.add('spawn');
    }
    return el;
  }

  function render(){
    if(boardEl.clientWidth === 0) return;
    var m = metrics();
    for(var k=0;k<SIZE*SIZE;k++){
      var r = Math.floor(k / SIZE), c = k % SIZE;
      var cel = cellEls[k];
      cel.style.width = m.cell + 'px';
      cel.style.height = m.cell + 'px';
      cel.style.transform = 'translate(' + (m.gap + c * (m.cell + m.gap)) + 'px,' + (m.gap + r * (m.cell + m.gap)) + 'px)';
    }
    var live = {};
    tiles.forEach(function(t){
      var el = ensureTileEl(t, t.isNew);
      live[t.id] = 1;
      placeTile(el, t, m.cell, m.gap);
      t.isNew = false;
    });
    dying.forEach(function(t){
      var el = tileEls.get(t.id);
      if(el){ live[t.id] = 1; placeTile(el, t, m.cell, m.gap); }
    });
    var stale = [];
    tileEls.forEach(function(el, id){ if(!live[id]) stale.push(id); });
    stale.forEach(function(id){
      var el = tileEls.get(id);
      if(el) el.remove();
      tileEls.delete(id);
    });
  }

  /* ---------- 游戏逻辑 ---------- */
  function tileAt(r, c){
    for(var i=0;i<tiles.length;i++){
      if(tiles[i].r === r && tiles[i].c === c) return tiles[i].value;
    }
    return 0;
  }

  function maxValue(){
    var m = 0;
    tiles.forEach(function(t){ if(t.value > m) m = t.value; });
    return m;
  }

  function destPos(dir, i, k){
    if(dir === 'left')  return [i, k];
    if(dir === 'right') return [i, SIZE - 1 - k];
    if(dir === 'up')    return [k, i];
    return [SIZE - 1 - k, i];
  }

  function spawnTile(){
    var empty = [];
    for(var r=0;r<SIZE;r++){
      for(var c=0;c<SIZE;c++){
        if(!tileAt(r, c)) empty.push([r, c]);
      }
    }
    if(!empty.length) return null;
    var pick = empty[Math.floor(Math.random() * empty.length)];
    var t = {id: nextId++, r: pick[0], c: pick[1], value: Math.random() < 0.9 ? 2 : 4, isNew: true};
    tiles.push(t);
    return t;
  }

  function snapshot(){
    return {
      tiles: tiles.map(function(t){ return {id:t.id, r:t.r, c:t.c, value:t.value}; }),
      score: score, moves: moves, won: won, keepPlaying: keepPlaying, over: over, nextId: nextId
    };
  }

  function restore(s){
    dying.forEach(function(t){ removeEl(t.id); });
    tiles = s.tiles.map(function(t){ return {id:t.id, r:t.r, c:t.c, value:t.value, isNew:false}; });
    score = s.score; moves = s.moves; won = s.won;
    keepPlaying = s.keepPlaying; over = s.over; nextId = s.nextId;
    dying = [];
    dyList = [];
  }

  function doMove(dir){
    if(over) return false;
    var before = snapshot();

    var grid = [];
    for(var r=0;r<SIZE;r++){
      grid.push([null,null,null,null]);
    }
    tiles.forEach(function(t){ grid[t.r][t.c] = t; t.merged = false; });

    var moved = false;
    var mergedAway = [];
    var popList = [];

    for(var i=0;i<SIZE;i++){
      var line = [];
      for(var j=0;j<SIZE;j++){
        var t;
        if(dir === 'left')       t = grid[i][j];
        else if(dir === 'right') t = grid[i][SIZE-1-j];
        else if(dir === 'up')    t = grid[j][i];
        else                     t = grid[SIZE-1-j][i];
        if(t) line.push(t);
      }
      var out = [];
      var lineMerged = [];
      for(var n=0;n<line.length;n++){
        var cur = line[n];
        var last = out[out.length-1];
        if(last && !last.merged && last.value === cur.value){
          last.value *= 2;
          last.merged = true;
          score += last.value;
          cur.dying = true;
          cur.mergeIndex = out.length - 1;
          lineMerged.push(cur);
          popList.push(last);
          moved = true;
        }else{
          out.push(cur);
        }
      }
      for(var p=0;p<out.length;p++){
        var d = destPos(dir, i, p);
        if(out[p].r !== d[0] || out[p].c !== d[1]) moved = true;
        out[p].r = d[0];
        out[p].c = d[1];
      }
      for(var q=0;q<lineMerged.length;q++){
        var dd = destPos(dir, i, lineMerged[q].mergeIndex);
        lineMerged[q].r = dd[0];
        lineMerged[q].c = dd[1];
      }
      mergedAway = mergedAway.concat(lineMerged);
    }

    if(!moved){
      tiles.forEach(function(t){ t.merged = false; });
      return false;
    }

    undoStack.push(before);
    if(undoStack.length > 5) undoStack.shift();

    var fadeList = mergedAway.map(function(t){
      return {id:t.id, r:t.r, c:t.c, value:t.value};
    });
    tiles = tiles.filter(function(t){ return !t.dying; });
    tiles.forEach(function(t){ t.dying = false; });
    dying = fadeList;

    moves++;
    var winNow = false;
    if(!won && maxValue() >= 2048){ won = true; winNow = true; }

    spawnTile();
    render();
    triggerPop(popList);
    flushDying(fadeList);
    updateHUD();

    if(!hasMoves()){
      endGame();
    }else if(winNow && !winShown){
      winShown = true;
      showModal('2048 达成', '本局得分 ' + score + '，棋盘最大方块 ' + maxValue() + '。要不要继续冲更高？',
        [{label:'继续挑战', primary:true, onClick:function(){ keepPlaying = true; }},
         {label:'开新局', onClick:function(){ newGame(); }}]);
    }
    return true;
  }

  var dyList = [];
  function flushDying(list){
    list.forEach(function(t){
      var el = tileEls.get(t.id);
      if(el) el.firstElementChild.classList.add('outfade');
    });
    dyList = list;
    setTimeout(function(){
      list.forEach(function(t){ removeEl(t.id); });
      if(dying === list) dying = [];
      dyList = [];
    }, 175);
  }
  function removeEl(id){
    var el = tileEls.get(id);
    if(el){ el.remove(); }
    tileEls.delete(id);
  }

  function triggerPop(list){
    list.forEach(function(t){
      var el = tileEls.get(t.id);
      if(!el) return;
      var inner = el.firstElementChild;
      inner.classList.remove('pop');
      void inner.offsetWidth;
      inner.classList.add('pop');
    });
  }

  function hasMoves(){
    if(tiles.length < SIZE * SIZE) return true;
    for(var r=0;r<SIZE;r++){
      for(var c=0;c<SIZE;c++){
        var v = tileAt(r, c);
        if(!v) return true;
        if(c + 1 < SIZE && v === tileAt(r, c + 1)) return true;
        if(r + 1 < SIZE && v === tileAt(r + 1, c)) return true;
      }
    }
    return false;
  }

  function updateHUD(){
    scoreEl.textContent = score;
    bestEl.textContent = Math.max(stats.best || 0, score);
    var undoBtn = document.getElementById('btn-undo');
    undoBtn.disabled = undoStack.length === 0;
  }

  function newGame(){
    recordGame();
    tiles = [];
    dying = [];
    score = 0; moves = 0; won = false; winShown = false; keepPlaying = false; over = false;
    recorded = false; undoStack = []; nextId = 1;
    tileEls.forEach(function(el){ el.remove(); });
    tileEls.clear();
    spawnTile(); spawnTile();
    startTime = Date.now();
    hideModal();
    render();
    updateHUD();
  }

  function recordGame(){
    if(recorded || score <= 0) return;
    recorded = true;
    stats.games = (stats.games || 0) + 1;
    stats.totalScore = (stats.totalScore || 0) + score;
    stats.totalMoves = (stats.totalMoves || 0) + moves;
    stats.maxTile = Math.max(stats.maxTile || 0, maxValue());
    stats.best = Math.max(stats.best || 0, score);
    var dur = startTime ? Math.round((Date.now() - startTime) / 1000) : 0;
    stats.history.unshift({score:score, maxTile:maxValue(), moves:moves, date:new Date().toISOString(), duration:dur});
    stats.history = stats.history.slice(0, 20);
    saveStats();
    renderRank();
  }

  function endGame(){
    over = true;
    recordGame();
    showModal('本局结束', '得分 ' + score + ' · 最大方块 ' + maxValue() + ' · 步数 ' + moves,
      [{label:'再来一局', primary:true, onClick:function(){ newGame(); }}]);
  }

  function undo(){
    if(!undoStack.length) return;
    var s = undoStack.pop();
    restore(s);
    over = false;
    hideModal();
    render();
    updateHUD();
  }

  /* ---------- 弹窗 ---------- */
  function showModal(title, text, actions){
    modalTitle.textContent = title;
    modalText.textContent = text;
    modalActs.innerHTML = '';
    (actions || []).forEach(function(a){
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn' + (a.primary ? ' primary' : '');
      b.textContent = a.label;
      b.addEventListener('click', function(){
        hideModal();
        if(a.onClick) a.onClick();
      });
      modalActs.appendChild(b);
    });
    modal.classList.add('show');
  }
  function hideModal(){ modal.classList.remove('show'); }

  /* ---------- 战绩页 ---------- */
  function fmtDate(iso){
    var d = new Date(iso);
    if(isNaN(d.getTime())) return '—';
    var p = function(n){ return n < 10 ? '0' + n : '' + n; };
    return p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  function renderRank(){
    document.getElementById('r-best').textContent  = Math.max(stats.best || 0, score);
    document.getElementById('r-games').textContent = stats.games || 0;
    document.getElementById('r-tile').textContent  = stats.maxTile || 0;
    document.getElementById('r-moves').textContent = stats.totalMoves || 0;

    var history = stats.history || [];
    var listEl = document.getElementById('rank-list');
    var emptyEl = document.getElementById('rank-empty');
    listEl.innerHTML = '';
    if(!history.length){
      emptyEl.style.display = 'block';
    }else{
      emptyEl.style.display = 'none';
      var top = history.slice().sort(function(a, b){ return b.score - a.score; }).slice(0, 8);
      top.forEach(function(h, idx){
        var li = document.createElement('li');
        li.className = 'rank-item';
        var no = document.createElement('div');
        no.className = 'no' + (idx < 3 ? ' top' + (idx + 1) : '');
        no.textContent = idx + 1;
        var mid = document.createElement('div');
        mid.innerHTML = '<div>' + fmtDate(h.date) + '</div><div class="meta">最大方块 ' + h.maxTile + ' · ' + h.moves + ' 步</div>';
        var sc = document.createElement('div');
        sc.className = 'sc';
        sc.textContent = h.score;
        li.appendChild(no); li.appendChild(mid); li.appendChild(sc);
        listEl.appendChild(li);
      });
    }

    var body = document.getElementById('history-body');
    var hEmpty = document.getElementById('history-empty');
    body.innerHTML = '';
    if(!history.length){
      hEmpty.style.display = 'block';
    }else{
      hEmpty.style.display = 'none';
      history.forEach(function(h){
        var tr = document.createElement('tr');
        tr.innerHTML =
          '<td>' + fmtDate(h.date) + '</td>' +
          '<td class="num">' + h.score + '</td>' +
          '<td class="num">' + h.maxTile + '</td>' +
          '<td class="num">' + h.moves + '</td>';
        body.appendChild(tr);
      });
    }
  }

  /* ---------- 路由 ---------- */
  function route(){
    var v = (location.hash || '#game').replace('#', '');
    if(v !== 'rank') v = 'game';
    document.getElementById('view-game').classList.toggle('hide', v !== 'game');
    document.getElementById('view-rank').classList.toggle('hide', v !== 'rank');
    var tabs = document.querySelectorAll('.tab');
    for(var i=0;i<tabs.length;i++){
      tabs[i].classList.toggle('active', tabs[i].getAttribute('data-view') === v);
    }
    if(v === 'game'){
      requestAnimationFrame(function(){ render(); });
    }else{
      renderRank();
    }
  }

  /* ---------- 交互 ---------- */
  document.addEventListener('keydown', function(e){
    var k = e.key;
    var map = {ArrowLeft:'left', ArrowRight:'right', ArrowUp:'up', ArrowDown:'down',
               a:'left', d:'right', w:'up', s:'down', A:'left', D:'right', W:'up', S:'down'};
    if(map[k]){
      e.preventDefault();
      doMove(map[k]);
    }else if(k === 'z' || k === 'Z'){
      e.preventDefault();
      undo();
    }
  });

  var touchX = 0, touchY = 0, touching = false;
  boardEl.addEventListener('touchstart', function(e){
    if(e.touches.length !== 1) return;
    touchX = e.touches[0].clientX;
    touchY = e.touches[0].clientY;
    touching = true;
  }, {passive:true});
  boardEl.addEventListener('touchend', function(e){
    if(!touching) return;
    touching = false;
    var dx = e.changedTouches[0].clientX - touchX;
    var dy = e.changedTouches[0].clientY - touchY;
    if(Math.abs(dx) < 24 && Math.abs(dy) < 24) return;
    if(Math.abs(dx) > Math.abs(dy)) doMove(dx > 0 ? 'right' : 'left');
    else doMove(dy > 0 ? 'down' : 'up');
  }, {passive:true});

  var padBtns = document.querySelectorAll('.pad-btn');
  for(var i=0;i<padBtns.length;i++){
    padBtns[i].addEventListener('click', function(){
      doMove(this.getAttribute('data-dir'));
    });
  }

  document.getElementById('btn-new').addEventListener('click', function(){
    if(score > 0 && !over){
      showModal('放弃本局？', '当前得分 ' + score + '，这一局会被记入战绩榜。',
        [{label:'开新局', primary:true, onClick:function(){ newGame(); }},
         {label:'继续玩', onClick:function(){}}]);
    }else{
      newGame();
    }
  });

  document.getElementById('btn-undo').addEventListener('click', undo);

  document.getElementById('btn-tip').addEventListener('click', function(){
    showModal('玩法说明', '方向键或滑动移动所有方块，相同数字相撞合并翻倍。每步会随机生成 2 或 4，拼到 2048 即通关，可继续挑战更高分。',
      [{label:'知道了', primary:true, onClick:function(){}}]);
  });

  document.getElementById('btn-back').addEventListener('click', function(){
    location.hash = '#game';
  });

  document.getElementById('btn-clear').addEventListener('click', function(){
    if(!stats.history.length && !stats.games){
      showModal('没有可清空的数据', '战绩榜还是空的。', [{label:'好', primary:true, onClick:function(){}}]);
      return;
    }
    showModal('清空全部战绩？', '排行榜、最近对局和统计数据都会被删除，不可恢复。',
      [{label:'确认清空', primary:true, onClick:function(){
        stats = {best:0, games:0, totalScore:0, totalMoves:0, maxTile:0, history:[]};
        saveStats();
        renderRank();
        updateHUD();
      }},
       {label:'取消', onClick:function(){}}]);
  });

  window.addEventListener('hashchange', route);
  var rzTimer = null;
  window.addEventListener('resize', function(){
    if(rzTimer) clearTimeout(rzTimer);
    rzTimer = setTimeout(function(){
      if((location.hash || '#game') !== '#rank') render();
    }, 120);
  });

  /* ---------- 启动 ---------- */
  route();
  newGame();
  render();
})();
</script>
</body>
</html>
"""


def main():
    # 端口交给系统分配，避免被占用
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    url = "http://127.0.0.1:%d/#game" % port

    print("=" * 52)
    print("  2048 小游戏已启动，浏览器马上会弹出")
    print("  地址：%s" % url)
    print("  页面：棋局 / 战绩榜（右上角切换）")
    print("  战绩文件：%s" % STATS_PATH)
    print("  关闭：回到这个窗口按 Ctrl+C")
    print("=" * 52)

    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已关闭，战绩已经保存好了。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
