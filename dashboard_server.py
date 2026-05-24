#!/usr/bin/env python3
"""
dashboard_server.py — etbot Web Dashboard
URL:      http://maxhive.cloud:8080/etbot
Password: etbot2026
"""

import json, os, subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from config import STATE_FILE, DASHBOARD_PORT, DASHBOARD_PASS, SERVER_HOST

def load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f: return json.load(f)
    except Exception: pass
    return {"main_balance":1000,"profit_pool":0,"total_profit":0,"total_loss":0,
            "total_trades":0,"daily_pnl":0,"available_for_withdrawal":0,
            "bot_paused":False,"open_trades":{},"trade_history":[]}

def bot_running():
    try:
        return subprocess.run(["pgrep","-f","etbot.py"],capture_output=True).returncode==0
    except: return False

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>etbot Dashboard | maxhive.cloud</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#060d1a;--bg2:#0a1628;--bg3:#0f2040;--cyan:#00d4ff;--green:#00ff88;--red:#ff4466;--yellow:#f0b429;--text:#c8e6f5;--text2:#5d8fa8;--border:rgba(0,180,255,0.12)}
body{background:var(--bg);font-family:'JetBrains Mono',monospace;color:var(--text);min-height:100vh}
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh}
.login-box{background:var(--bg2);border:1px solid rgba(0,180,255,0.25);border-radius:16px;padding:40px;width:320px;text-align:center}
.logo{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;color:var(--cyan);letter-spacing:3px;margin-bottom:4px}
.logo-sub{font-size:9px;color:var(--text2);letter-spacing:1px;margin-bottom:28px}
input{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:12px;color:var(--text);font-family:'JetBrains Mono',monospace;font-size:13px;margin-bottom:12px;outline:none}
input:focus{border-color:var(--cyan)}
.btn{width:100%;background:linear-gradient(135deg,#006699,#004477);border:none;border-radius:8px;padding:12px;color:var(--cyan);font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;letter-spacing:2px;cursor:pointer}
.btn:hover{opacity:.85}.err{color:var(--red);font-size:11px;margin-top:8px}
.dash{padding:14px;display:none}
.header{display:flex;align-items:center;justify-content:space-between;background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:12px 20px;margin-bottom:10px;flex-wrap:wrap;gap:10px}
.logo2{font-family:'Syne',sans-serif;font-weight:800;font-size:18px;color:var(--cyan);letter-spacing:2px}
.logo2-sub{font-size:9px;color:var(--text2);letter-spacing:1px}
.hstats{display:flex;gap:16px;flex-wrap:wrap}
.hstat{text-align:center}.hval{font-size:13px;font-weight:600;color:var(--cyan)}.hlbl{font-size:8px;color:var(--text2);letter-spacing:1px;text-transform:uppercase}
.pill{display:flex;align-items:center;gap:7px;border-radius:20px;padding:6px 14px;font-size:11px;font-weight:600;letter-spacing:1px}
.pill-g{background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.25);color:var(--green)}
.pill-r{background:rgba(255,68,102,.08);border:1px solid rgba(255,68,102,.25);color:var(--red)}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(0,255,136,.4)}50%{box-shadow:0 0 0 6px rgba(0,255,136,0)}}
.dot{width:8px;height:8px;border-radius:50%}.dot-g{background:var(--green);animation:pulse 2s infinite}.dot-r{background:var(--red)}
.mkt-bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.tag{background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:4px 10px;font-size:9px;white-space:nowrap}
.metrics{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:10px}
.metric{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.mv{font-family:'Syne',sans-serif;font-size:18px;font-weight:700}.ml{font-size:9px;color:var(--text2);letter-spacing:1px;text-transform:uppercase;margin-top:2px}.ms{font-size:10px;margin-top:3px;color:var(--text2)}
.grid2{display:grid;grid-template-columns:1.8fr 1fr;gap:12px;margin-bottom:10px}
.grid3{display:grid;grid-template-columns:1.6fr 1fr .85fr;gap:12px}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:16px;position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#006699,transparent);opacity:.5}
.ct{font-size:9px;letter-spacing:2px;color:var(--text2);text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.cd{width:5px;height:5px;background:var(--cyan);border-radius:50%}
table{width:100%;border-collapse:collapse}th{font-size:9px;color:var(--text2);letter-spacing:1px;text-transform:uppercase;padding:5px 7px;border-bottom:1px solid var(--border);text-align:left}td{font-size:11px;padding:6px 7px;border-bottom:1px solid rgba(0,180,255,.04)}tr:hover td{background:rgba(0,180,255,.03)}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:9px;font-weight:600}
.b-tp{background:rgba(0,255,136,.1);color:var(--green);border:1px solid rgba(0,255,136,.2)}
.b-sl{background:rgba(255,68,102,.1);color:var(--red);border:1px solid rgba(255,68,102,.2)}
.b-rsi{background:rgba(0,212,255,.1);color:var(--cyan);border:1px solid rgba(0,212,255,.2)}
.b-sma{background:rgba(240,180,41,.1);color:var(--yellow);border:1px solid rgba(240,180,41,.2)}
.tabs{display:flex;gap:8px;margin-bottom:10px}
.tab{background:transparent;border:1px solid var(--border);color:var(--text2);padding:4px 12px;border-radius:6px;font-size:10px;cursor:pointer;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:1px}
.tab.active{background:rgba(0,212,255,.12);border-color:rgba(0,212,255,.3);color:var(--cyan)}
.news-item{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid rgba(0,180,255,.07)}
.ns{min-width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700}
.ns-p{background:rgba(0,255,136,.1);color:var(--green);border:1px solid rgba(0,255,136,.2)}
.ns-n{background:rgba(255,68,102,.1);color:var(--red);border:1px solid rgba(255,68,102,.2)}
.ns-0{background:rgba(0,180,255,.06);color:var(--text2);border:1px solid var(--border)}
.sec-row{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid rgba(0,180,255,.07)}
.cfg-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(0,180,255,.07);font-size:10px}
.alloc-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid rgba(0,180,255,.07);font-size:10px}
.adot{width:8px;height:8px;border-radius:2px;margin-right:6px;display:inline-block}
.chart-wrap{height:170px;margin-top:8px}
.rb{text-align:center;font-size:9px;color:var(--text2);padding:8px 0;letter-spacing:.5px}
footer{text-align:center;padding:12px;font-size:9px;color:var(--text2);letter-spacing:1px;margin-top:8px}
::-webkit-scrollbar{width:3px}::-webkit-scrollbar-thumb{background:#006699;border-radius:2px}
@media(max-width:1100px){.metrics{grid-template-columns:repeat(3,1fr)}.grid2,.grid3{grid-template-columns:1fr}}
@media(max-width:600px){.metrics{grid-template-columns:1fr 1fr}.hstats{display:none}}
</style>
</head>
<body>
<div class="login-wrap" id="LW">
  <div class="login-box">
    <div class="logo">🏦 ETBOT</div>
    <div class="logo-sub">MAXHIVE.CLOUD · TRADING DASHBOARD</div>
    <input type="password" id="pw" placeholder="Password...">
    <button class="btn" onclick="login()">▶ ACCESS DASHBOARD</button>
    <div class="err" id="er"></div>
  </div>
</div>
<div class="dash" id="D">
  <div class="header">
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:34px;height:34px;background:linear-gradient(135deg,#00d4ff,#006699);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:17px">🏦</div>
      <div><div class="logo2">ETBOT</div><div class="logo2-sub">@ETORO_ET_BOT · MAXHIVE.CLOUD</div></div>
    </div>
    <div class="hstats" id="hs"></div>
    <div class="pill pill-g" id="sp"><div class="dot dot-g"></div><span>LOADING</span></div>
  </div>
  <div class="mkt-bar" id="mb"></div>
  <div class="metrics" id="mx"></div>
  <div class="grid2">
    <div class="card">
      <div class="ct"><span class="cd"></span>Capital History</div>
      <div style="display:flex;gap:16px;margin-bottom:6px">
        <span style="font-family:Syne;font-size:17px;font-weight:700;color:#00ff88" id="hp">+$0.00</span>
        <span style="font-size:10px;color:#5d8fa8;align-self:center">profit</span>
        <span style="font-family:Syne;font-size:17px;font-weight:700;color:#ff4466" id="hl">-$0.00</span>
        <span style="font-size:10px;color:#5d8fa8;align-self:center">loss</span>
      </div>
      <div class="chart-wrap"><canvas id="pc"></canvas></div>
    </div>
    <div class="card">
      <div class="ct"><span class="cd"></span>Sector P&L</div>
      <div id="sec"></div>
      <div style="margin-top:14px"><div class="ct"><span class="cd"></span>Bot Rules</div><div id="rl"></div></div>
    </div>
  </div>
  <div class="grid3">
    <div class="card">
      <div class="ct"><span class="cd"></span>Positions</div>
      <div class="tabs">
        <button class="tab active" onclick="st('o',this)">Open Trades</button>
        <button class="tab" onclick="st('h',this)">History</button>
      </div>
      <div style="overflow-x:auto" id="tt"></div>
    </div>
    <div class="card">
      <div class="ct"><span class="cd"></span>News · 6h Report</div>
      <div style="overflow-y:auto;max-height:400px" id="nb"></div>
    </div>
    <div class="card">
      <div class="ct"><span class="cd"></span>Allocation</div>
      <div style="display:flex;justify-content:center;padding:6px 0 12px">
        <div style="position:relative;width:90px;height:90px">
          <canvas id="ac" width="90" height="90"></canvas>
          <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center">
            <div style="font-family:Syne;font-size:16px;font-weight:700;color:#00d4ff" id="dp">70%</div>
            <div style="font-size:8px;color:#5d8fa8;letter-spacing:1px">DEPLOY</div>
          </div>
        </div>
      </div>
      <div id="al"></div>
      <div style="margin-top:12px"><div class="ct"><span class="cd"></span>Config</div><div id="cr"></div></div>
    </div>
  </div>
  <div class="rb" id="rb">⟳ Auto-refresh every 10s</div>
  <footer>ETBOT © 2026 · @ETORO_ET_BOT · MAXHIVE.CLOUD · EXECUTE TRADES MANUALLY ON ETORO</footer>
</div>
<script>
const PW="PASS_PH";let pc=null,ac=null,tab="o",S=null;
const $=id=>document.getElementById(id);
const G=v=>v>=0?"#00ff88":"#ff4466";
const F=(v,d=2)=>(v>=0?"+":"")+v.toFixed(d);

function login(){
  if($("pw").value===PW){sessionStorage.setItem("eb","1");show();}
  else $("er").textContent="Wrong password";
}
$("pw").addEventListener("keydown",e=>{if(e.key==="Enter")login()});
function show(){$("LW").style.display="none";$("D").style.display="block";init();load();setInterval(load,10000);}
if(sessionStorage.getItem("eb")==="1")show();

async function load(){
  try{S=await(await fetch("/api/state")).json();render();$("rb").textContent="⟳ Auto-refresh every 10s · Last: "+new Date().toLocaleTimeString();}
  catch{$("rb").textContent="⚠️ Connection error — retrying...";}
}

function render(){
  if(!S)return;
  const net=S.total_profit-S.total_loss,cap=(S.main_balance||1000)+(S.profit_pool||0);
  const ot=Object.entries(S.open_trades||{}),hist=S.trade_history||[];
  const wr=hist.length?Math.round(hist.filter(t=>t.pnl>0).length/hist.length*100):0;
  const run=S.bot_running!==false,paused=S.bot_paused;
  $("sp").className="pill "+(run&&!paused?"pill-g":"pill-r");
  $("sp").innerHTML=`<div class="dot ${run&&!paused?"dot-g":"dot-r"}"></div><span>${paused?"PAUSED":run?"ACTIVE":"STOPPED"}</span>`;
  $("hs").innerHTML=[["$"+cap.toFixed(2),"Capital"],[F(net,2)+"$","Net P&L"],[S.total_trades,"Trades"],[wr+"%","Win"],[ot.length+"/5","Open"]].map(([v,l])=>`<div class="hstat"><div class="hval">${v}</div><div class="hlbl">${l}</div></div>`).join("");
  const now=new Date(),et=new Date(now.toLocaleString("en-US",{timeZone:"America/New_York"}));
  const h=et.getHours(),m=et.getMinutes(),wd=et.getDay();
  const open=wd>0&&wd<6&&(h>9||(h===9&&m>=30))&&h<16;
  $("mb").innerHTML=[[open?"🟢":"🔴",open?"NYSE OPEN":"NYSE CLOSED"],["⏰",open?"Closes 16:00 ET":"Opens Mon 09:30 ET"],["📰","News every 6h"],["🔍","Scan: 2min (mkt hrs)"],["⚡","Exit: 30s always"],["🕐",now.toUTCString().slice(0,25)]].map(([i,t])=>`<div class="tag">${i} ${t}</div>`).join("");
  $("hp").textContent="+$"+S.total_profit.toFixed(2);$("hl").textContent="-$"+S.total_loss.toFixed(2);
  const dp=S.daily_pnl||0;
  $("mx").innerHTML=[["$"+cap.toFixed(2),"Capital","Pool: $"+(S.profit_pool||0).toFixed(2),"var(--cyan)"],[F(S.total_profit,2)+"$","Profit","-$"+S.total_loss.toFixed(2)+" loss","#00ff88"],[F(net,2)+"$","Net P&L","All-time",G(net)],["$"+(S.available_for_withdrawal||0).toFixed(2),"Withdrawable","20% of profits","var(--yellow)"],[S.total_trades,"Total Trades","Win: "+wr+"%","var(--cyan)"],[F(dp,2)+"$","Today P&L","Risk/trade: 0.25%",G(dp)]].map(([v,l,s,c])=>`<div class="metric"><div class="mv" style="color:${c}">${v}</div><div class="ml">${l}</div><div class="ms">${s}</div></div>`).join("");
  const p=S.total_profit||0;
  $("sec").innerHTML=[{n:"Stocks",v:p*.6,c:"#00d4ff"},{n:"ETFs",v:p*.25,c:"#0099cc"},{n:"Commodities",v:p*.15,c:"#f0b429"}].map(s=>`<div class="sec-row"><div style="width:90px;font-size:10px">${s.n}</div><div style="flex:1;height:6px;background:#0f2040;border-radius:3px;overflow:hidden"><div style="height:100%;width:${Math.abs(s.v)*6}%;background:${s.v>=0?s.c:"#ff4466"};border-radius:3px"></div></div><div style="width:52px;text-align:right;font-size:11px;font-weight:600;color:${G(s.v)}">${F(s.v,2)}$</div></div>`).join("");
  $("rl").innerHTML=[["Stop Loss","0.10%","#ff4466"],["TP RSI","2.00%","#00ff88"],["TP SMA","1.50%","#00ff88"],["Risk","0.25%","#00d4ff"],["Strong News","1.5×","#f0b429"],["Min Signal","80%","#00d4ff"]].map(([l,v,c])=>`<div class="cfg-row"><span style="color:#5d8fa8">${l}</span><span style="color:${c};font-weight:600">${v}</span></div>`).join("");
  rT(ot,hist);
  const dPct=open?70:50;$("dp").textContent=dPct+"%";
  $("al").innerHTML=[["Deploy","#00d4ff",dPct+"%","$"+Math.round(cap*dPct/100)],["Reserve","rgba(0,255,136,.6)",(100-dPct)+"%","$"+Math.round(cap*(100-dPct)/100)],["Withdraw","#f0b429","20% profit","$"+(S.available_for_withdrawal||0).toFixed(2)]].map(([l,c,pp,v])=>`<div class="alloc-row"><div><span class="adot" style="background:${c}"></span>${l}</div><div style="text-align:right"><div style="font-size:11px;font-weight:600;color:${c}">${v}</div><div style="font-size:9px;color:#5d8fa8">${pp}</div></div></div>`).join("");
  if(ac){ac.data.datasets[0].data=[dPct,100-dPct];ac.update("none");}
  const news=S.last_news||[];
  $("nb").innerHTML=news.length?news.map(n=>`<div class="news-item"><div class="ns ${n.score>0?'ns-p':n.score<0?'ns-n':'ns-0'}">${n.score>0?"+":""}${n.score}</div><div style="flex:1"><div style="font-size:9px;color:#00d4ff;font-weight:600;letter-spacing:1px;margin-bottom:2px">${n.sym||"MACRO"}</div><div style="font-size:10px;line-height:1.4">${n.text||""}</div><div style="font-size:9px;color:#5d8fa8;margin-top:2px">${n.time||""}</div></div></div>`).join(""):`<div style="font-size:10px;color:#5d8fa8;padding:8px 0">News arrives every 6h automatically.<br>Send <b style="color:#00d4ff">/et_news</b> on Telegram for instant report.</div>`;
  $("cr").innerHTML=[["Stop Loss","0.10%","#ff4466"],["TP RSI","2.00%","#00ff88"],["TP SMA","1.50%","#00ff88"],["Risk/Trade","0.25%","#00d4ff"],["Max Trades","5","#c8e6f5"],["Scan Interval","2 min","#5d8fa8"]].map(([l,v,c])=>`<div class="cfg-row"><span style="color:#5d8fa8">${l}</span><span style="color:${c};font-weight:600">${v}</span></div>`).join("");
  uPC(S);
}

function rT(ot,hist){
  if(tab==="o"){
    if(!ot.length){$("tt").innerHTML='<div style="font-size:11px;color:#5d8fa8;padding:16px 0">No open trades right now.</div>';return;}
    $("tt").innerHTML=`<table><thead><tr>${["Asset","Entry","SL","TP","Shares","Signal","Strategy","News","Size"].map(h=>`<th>${h}</th>`).join("")}</tr></thead><tbody>${ot.map(([s,t])=>`<tr><td style="color:#00d4ff;font-weight:600">${s}</td><td>$${(t.entry_price||0).toFixed(2)}</td><td style="color:#ff4466">$${(t.stop_loss||0).toFixed(4)}</td><td style="color:#00ff88">$${(t.take_profit||0).toFixed(4)}</td><td>${t.shares||0}</td><td>${Math.round((t.signal_strength||0)*100)}%</td><td><span class="badge ${t.strategy==='RSI_OVERSOLD'?'b-rsi':'b-sma'}">${t.strategy==='RSI_OVERSOLD'?'RSI':'SMA'}</span></td><td style="color:${G(t.news_score||0)}">${t.news_score>0?"+":""}${t.news_score||0}</td><td style="color:#f0b429">${t.position_mult||1}×</td></tr>`).join("")}</tbody></table>`;
  }else{
    if(!hist.length){$("tt").innerHTML='<div style="font-size:11px;color:#5d8fa8;padding:16px 0">No trade history yet.</div>';return;}
    $("tt").innerHTML=`<table><thead><tr>${["Asset","P&L","%","Result","News","Size","Time"].map(h=>`<th>${h}</th>`).join("")}</tr></thead><tbody>${hist.slice(-15).reverse().map(h=>`<tr><td style="color:#00d4ff;font-weight:600">${h.symbol}</td><td style="color:${G(h.pnl)};font-weight:600">${F(h.pnl,2)}$</td><td style="color:${G(h.pnl_pct)}">${F(h.pnl_pct,2)}%</td><td><span class="badge ${h.pnl>=0?'b-tp':'b-sl'}">${h.pnl>=0?'TP ✓':'SL ✗'}</span></td><td style="color:${G(h.news_score||0)}">${h.news_score>0?"+":""}${h.news_score||0}</td><td style="color:#5d8fa8">${h.pos_mult||1}×</td><td style="font-size:9px;color:#5d8fa8">${(h.timestamp||"").slice(5,16)}</td></tr>`).join("")}</tbody></table>`;
  }
}
function st(t,el){tab=t;document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));el.classList.add("active");if(S)rT(Object.entries(S.open_trades||{}),S.trade_history||[]);}
function init(){
  const ctx=$("pc").getContext("2d"),g=ctx.createLinearGradient(0,0,0,170);
  g.addColorStop(0,"rgba(0,212,255,.25)");g.addColorStop(1,"rgba(0,212,255,0)");
  pc=new Chart(ctx,{type:"line",data:{labels:[],datasets:[{data:[],borderColor:"#00d4ff",borderWidth:2,backgroundColor:g,fill:true,tension:.4,pointRadius:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:"#0f2040",borderColor:"rgba(0,180,255,.25)",borderWidth:1,titleFont:{family:"JetBrains Mono"},bodyFont:{family:"JetBrains Mono",size:11}}},scales:{x:{grid:{color:"rgba(0,180,255,.05)"},ticks:{color:"#5d8fa8",font:{family:"JetBrains Mono",size:9}}},y:{grid:{color:"rgba(0,180,255,.05)"},ticks:{color:"#5d8fa8",font:{family:"JetBrains Mono",size:9}}}}}});
  ac=new Chart($("ac").getContext("2d"),{type:"doughnut",data:{datasets:[{data:[70,30],backgroundColor:["#00d4ff","rgba(0,255,136,.4)"],borderWidth:0}]},options:{responsive:false,cutout:"72%",plugins:{legend:{display:false},tooltip:{enabled:false}}}});
}
function uPC(s){
  if(!pc)return;
  let r=1000;const pts=[{l:"Start",v:1000}];
  (s.trade_history||[]).slice().reverse().slice(-20).reverse().forEach(t=>{r+=t.pnl||0;pts.push({l:(t.timestamp||"").slice(5,10),v:parseFloat(r.toFixed(2))});});
  pts.push({l:"Now",v:parseFloat(((s.main_balance||1000)+(s.profit_pool||0)).toFixed(2))});
  pc.data.labels=pts.map(p=>p.l);pc.data.datasets[0].data=pts.map(p=>p.v);pc.update("none");
}
</script>
</body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/state":
            s = load_state()
            s["bot_running"] = bot_running()
            body = json.dumps(s).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(body)
        elif path in ("/etbot","/etbot.html","/",""):
            body = HTML.replace("PASS_PH", DASHBOARD_PASS).encode()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(302)
            self.send_header("Location","/etbot")
            self.end_headers()

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  etbot Dashboard")
    print(f"  URL:      http://{SERVER_HOST}:{DASHBOARD_PORT}/etbot")
    print(f"  Password: {DASHBOARD_PASS}")
    print(f"{'='*50}\n")
    try:
        HTTPServer(("0.0.0.0", DASHBOARD_PORT), Handler).serve_forever()
    except OSError as e:
        print(f"Port busy. Kill with: fuser -k {DASHBOARD_PORT}/tcp && python3 dashboard_server.py")
