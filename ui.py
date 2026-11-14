"""HTML for ddyno pages. Plain strings, no build step."""

CSS = """
:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--fg:#e6edf3;--mute:#8b949e;--acc:#58a6ff;--up:#3fb950;--down:#f0883e;--warn:#d29922}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:760px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:2rem;line-height:1.2;margin:0 0 6px}h2{font-size:1.05rem;margin:0 0 12px}h3{margin:0 0 6px;font-size:1.05rem}
p.sub{color:var(--mute);margin:0 0 24px}a{color:var(--acc)}
a.back{color:var(--mute);text-decoration:none;font-size:.9rem;display:inline-block;margin-bottom:14px}
.cat{color:var(--acc);font-size:.8rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin:0 0 4px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
a.card{text-decoration:none;color:inherit;display:block}a.card:hover{border-color:var(--acc)}
.card p{margin:0;color:var(--mute);font-size:.93rem}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}
.chip{background:#21262d;border:1px solid var(--line);color:var(--mute);border-radius:99px;padding:6px 14px;font-size:.88rem;cursor:pointer}
.chip.on{background:var(--acc);border-color:var(--acc);color:#04111f;font-weight:600}
.sec{margin:0 0 26px}.sec>h2{color:var(--mute);font-size:.8rem;letter-spacing:.06em;text-transform:uppercase}
button{font:inherit;cursor:pointer}
textarea{width:100%;min-height:110px;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit}
.btn{background:var(--acc);color:#04111f;border:0;border-radius:8px;padding:10px 18px;font-weight:600;margin-top:10px}
.btn:disabled{opacity:.6}
.bar{background:#21262d;border-radius:6px;height:10px;overflow:hidden}.bar i{display:block;height:100%;background:var(--acc)}
.row{margin:14px 0}.row b{display:flex;justify-content:space-between}

/* model page */
.teams{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
.col h2{display:flex;align-items:center;gap:6px}.dot{width:9px;height:9px;border-radius:50%;background:var(--acc)}
.col.away .dot{background:var(--down)}
.f{margin:0 0 16px}.f:last-child{margin-bottom:0}
.fh{display:flex;justify-content:space-between;align-items:center;gap:8px;min-height:38px}
.fh label{font-size:.9rem;line-height:1.25}.fh small{color:var(--mute)}
.num{width:66px;flex:none;background:#0d1117;color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:6px 4px;font:inherit;font-weight:600;text-align:center}
.num:focus{outline:2px solid var(--acc);outline-offset:0}
.f p{margin:2px 0 0;color:var(--mute);font-size:.76rem;line-height:1.35}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:34px;background:transparent;margin:2px 0 0;touch-action:pan-y}
input[type=range]::-webkit-slider-runnable-track{height:6px;border-radius:3px;background:#30363d}
input[type=range]::-moz-range-track{height:6px;border-radius:3px;background:#30363d}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:28px;height:28px;border-radius:50%;background:var(--acc);border:3px solid #0d1117;margin-top:-11px}
input[type=range]::-moz-range-thumb{width:24px;height:24px;border-radius:50%;background:var(--acc);border:3px solid #0d1117}
.away input[type=range]::-webkit-slider-thumb{background:var(--down)}.away input[type=range]::-moz-range-thumb{background:var(--down)}
.actions{display:flex;gap:10px;margin:14px 0 22px}
#dyno{flex:1;background:linear-gradient(135deg,#58a6ff,#3fb950);color:#04111f;border:0;border-radius:12px;padding:16px;font-size:1.25rem;font-weight:800;letter-spacing:.04em}
#dyno:disabled{opacity:.6}#reset{background:transparent;color:var(--mute);border:1px solid var(--line);border-radius:12px;padding:0 16px}
#result{margin-bottom:22px}
.big{font-size:3.2rem;font-weight:800;line-height:1.05}.big small{font-size:1rem;font-weight:500;color:var(--mute);margin-left:6px}
.rng{position:relative;height:38px;margin:18px 0 6px}
.rng .trk{position:absolute;left:0;right:0;top:15px;height:8px;border-radius:4px;background:#21262d}
.rng .b95{position:absolute;top:11px;height:16px;border-radius:8px;background:rgba(88,166,255,.25)}
.rng .b80{position:absolute;top:8px;height:22px;border-radius:11px;background:rgba(88,166,255,.6)}
.rng .pt{position:absolute;top:2px;width:4px;height:34px;margin-left:-2px;border-radius:2px;background:#fff}
.rng .tick{position:absolute;top:0;height:38px;border-left:2px dashed var(--mute)}.rng .tick.ln{border-color:var(--warn)}
.ends{display:flex;justify-content:space-between;color:var(--mute);font-size:.78rem}
.legend{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;margin-top:12px;font-size:.9rem}
.legend span{color:var(--mute);display:block;font-size:.76rem}
.sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:baseline}
.lean{margin-top:14px;padding:10px 12px;border-radius:10px;background:#21262d;font-size:.95rem}
.drv{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr) 46px;gap:8px;align-items:center;margin:9px 0;font-size:.88rem}
.drv .nm small{color:var(--mute);display:block;font-size:.76rem}
.drv .tr{position:relative;height:12px;background:#21262d;border-radius:6px}
.drv .tr:before{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;border-left:1px solid var(--mute)}
.drv .tr i{position:absolute;top:0;height:12px;border-radius:6px}
.drv .v{text-align:right;font-weight:600;font-variant-numeric:tabular-nums}
.up{color:var(--up)}.dn{color:var(--down)}
.warn{border:1px solid var(--warn);background:rgba(210,153,34,.1);border-radius:10px;padding:10px 12px;margin-top:14px;font-size:.88rem}
.warn ul{margin:4px 0 0;padding-left:18px}
.blk{margin-top:20px}.blk h3{font-size:.8rem;color:var(--mute);letter-spacing:.06em;text-transform:uppercase}
.blk p{margin:0}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
summary{cursor:pointer;font-weight:600}details ul{padding-left:20px;margin:8px 0 16px}details li{margin:0 0 8px;font-size:.93rem}
details h3{margin-top:16px}
table{width:100%;border-collapse:collapse;font-size:.88rem;margin:8px 0}th,td{text-align:right;padding:7px 4px;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}th{color:var(--mute);font-weight:500;font-size:.78rem}
tr.me td{font-weight:700}.note{color:var(--mute);font-size:.8rem;margin:6px 0 0}
footer{color:var(--mute);font-size:.8rem;margin-top:22px;text-align:center}
@media(max-width:420px){.card{padding:12px}.big{font-size:2.7rem}.fh label{font-size:.84rem}.num{width:58px}}
"""

HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>""" + CSS + """</style></head><body><main>"""

HUB = HEAD.replace("__TITLE__", "ddyno · ML-powered apps") + """
<h1>ddyno</h1><p class="sub">Small ML models you can poke at. Set the inputs, press Dyno, see what the model thinks and why.</p>
<div class="chips" id="chips"></div><div id="list"></div>
<script>
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
let models=[],cat='All';
function draw(){
  const chips=document.getElementById('chips'),list=document.getElementById('list');chips.replaceChildren();list.replaceChildren();
  const cats=[...new Set(models.map(m=>m.category))];
  ['All',...cats].forEach(c=>{const b=el('button','chip'+(c===cat?' on':''),c);b.onclick=()=>{cat=c;draw()};chips.appendChild(b)});
  cats.filter(c=>cat==='All'||c===cat).forEach(c=>{
    const s=el('section','sec');s.appendChild(el('h2',null,c));const g=el('div','grid');
    models.filter(m=>m.category===c).forEach(m=>{const a=el('a','card');a.href=m.url;a.appendChild(el('h3',null,m.name));a.appendChild(el('p',null,m.summary));g.appendChild(a)});
    s.appendChild(g);list.appendChild(s)});
}
fetch('/api/models').then(r=>r.json()).then(d=>{models=d.models;draw()}).catch(()=>{document.getElementById('list').textContent='Could not load models. Try refreshing.'});
</script></main></body></html>"""

MODEL = HEAD.replace("__TITLE__", "__NAME__ · ddyno") + """
<a class="back" href="/">&larr; ddyno</a>
<p class="cat" id="cat"></p><h1 id="name">__NAME__</h1><p class="sub" id="summary"></p>
<div class="teams" id="teams"></div>
<div class="card" id="shared" style="margin-bottom:10px"></div>
<div class="card" id="cmp" hidden></div>
<div class="actions"><button id="dyno">DYNO</button><button id="reset">Reset</button></div>
<div class="card" id="result" hidden></div>
<details id="about"><summary>About this model</summary><div id="aboutBody"></div></details>
<footer id="foot"></footer>
<script>
const SLUG="__SLUG__";
const $=id=>document.getElementById(id);
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const n1=v=>(Math.round(v*10)/10).toString(), n0=v=>Math.round(v).toString();
const sg=v=>(v>0?'+':'')+n1(v);
let meta,vals={},ctl={},lineInput;

function field(f){
  const w=el('div','f'),h=el('div','fh'),lab=el('label',null,f.label);
  if(f.unit){lab.appendChild(document.createTextNode(' '));lab.appendChild(el('small',null,f.unit))}
  const num=el('input','num');num.type='number';num.inputMode='decimal';num.step=f.step;num.min=f.hard_min;num.max=f.hard_max;
  const rng=el('input');rng.type='range';rng.min=f.min;rng.max=f.max;rng.step=f.step;
  lab.htmlFor=num.id='n_'+f.name;rng.setAttribute('aria-label',f.label);
  const set=(v,from)=>{v=Math.min(f.hard_max,Math.max(f.hard_min,v));vals[f.name]=v;if(from!=='num')num.value=v;if(from!=='rng')rng.value=v};
  rng.oninput=()=>set(parseFloat(rng.value),'rng');
  num.oninput=()=>{const v=parseFloat(num.value);if(!isNaN(v))set(v,'num')};
  num.onblur=()=>{num.value=vals[f.name]};
  ctl[f.name]=set;set(f.default);
  h.appendChild(lab);h.appendChild(num);w.appendChild(h);w.appendChild(rng);w.appendChild(el('p',null,f.description));
  return w;
}
function build(){
  $('cat').textContent=meta.category;$('name').textContent=meta.name;$('summary').textContent=meta.summary;
  const sides=[['home','Home'],['away','Away']].filter(s=>meta.features.some(f=>f.side===s[0]));
  if(!sides.length)$('teams').hidden=true;
  sides.forEach(([k,title])=>{const c=el('div','card col '+k),h=el('h2');h.appendChild(el('span','dot'));h.appendChild(document.createTextNode(title));
    c.appendChild(h);meta.features.filter(f=>f.side===k).forEach(f=>c.appendChild(field(f)));$('teams').appendChild(c)});
  const sh=meta.features.filter(f=>f.side==='shared');
  if(sh.length){$('shared').appendChild(el('h2',null,sides.length?'Game context':'Inputs'));sh.forEach(f=>$('shared').appendChild(field(f)))}else $('shared').hidden=true;
  if(meta.compare_line){const c=$('cmp');c.hidden=false;c.style.marginBottom='10px';const w=el('div','f'),h=el('div','fh'),lab=el('label',null,meta.compare_line.label);
    lineInput=el('input','num');lineInput.type='number';lineInput.inputMode='decimal';lineInput.step=meta.compare_line.step;lineInput.placeholder='–';lineInput.id='line';lab.htmlFor='line';
    h.appendChild(lab);h.appendChild(lineInput);w.appendChild(h);c.appendChild(w)}
  about();$('foot').textContent=meta.card.disclaimer||'';
}
function about(){
  const c=meta.card,b=$('aboutBody');
  b.appendChild(el('h3',null,'What the model learned'));
  const ul=el('ul');c.findings.forEach(t=>ul.appendChild(el('li',null,t)));b.appendChild(ul);
  b.appendChild(el('h3',null,'How accurate is it?'));
  b.appendChild(el('p','note','Tested on the '+c.holdout_label+'.'));
  const t=el('table'),hr=el('tr');['Method','Average miss','RMSE','R²'].forEach(x=>hr.appendChild(el('th',null,x)));t.appendChild(hr);
  c.accuracy.forEach((a,i)=>{const r=el('tr',i?'':'me');[a.name,a.mae.toFixed(1)+' pts',a.rmse.toFixed(1),a.r2.toFixed(2)].forEach(x=>r.appendChild(el('td',null,x)));t.appendChild(r)});
  b.appendChild(t);
  b.appendChild(el('p','note','Average miss is how far off the prediction was on a typical game. RMSE is similar but punishes big misses more. R² is the share of game-to-game differences the method explains (1.00 would be perfect).'));
  b.appendChild(el('h3',null,'Can you trust the range?'));
  b.appendChild(el('p',null,'In the test games, the real final score landed inside the 80% range '+Math.round(c.coverage['80']*100)+'% of the time and inside the 95% range '+Math.round(c.coverage['95']*100)+'% of the time. That is what honest ranges should do.'));
  b.appendChild(el('h3',null,'Limitations'));
  const ul2=el('ul');c.limitations.forEach(t=>ul2.appendChild(el('li',null,t)));b.appendChild(ul2);
  b.appendChild(el('p','note','Linear regression trained on '+c.n_games.toLocaleString()+' games from the '+c.seasons[0]+' to '+c.seasons[1]+' seasons, after testing '+c.candidates_tested+' candidate inputs. Last trained '+c.trained_on+'. Data: nflverse.'));
}
function render(r){
  const u=meta.target.unit||'',box=$('result');box.replaceChildren();box.hidden=false;
  box.appendChild(el('p','cat','Expected '+meta.target.label.toLowerCase()));
  const big=el('div','big',n1(r.prediction));big.appendChild(el('small',null,u));box.appendChild(big);
  const i80=r.intervals['80'],i95=r.intervals['95'];
  let a=Math.min(i95.low,r.floor??i95.low),b=i95.high;
  if(r.compare){a=Math.min(a,r.compare.line);b=Math.max(b,r.compare.line)}
  const pad=(b-a)*0.06;a-=pad;b+=pad;const pos=v=>((v-a)/(b-a)*100)+'%',wid=(x,y)=>((y-x)/(b-a)*100)+'%';
  const g=el('div','rng');g.appendChild(el('div','trk'));
  const b95=el('div','b95');b95.style.left=pos(i95.low);b95.style.width=wid(i95.low,i95.high);g.appendChild(b95);
  const b80=el('div','b80');b80.style.left=pos(i80.low);b80.style.width=wid(i80.low,i80.high);g.appendChild(b80);
  if(r.floor!=null){const t=el('div','tick');t.style.left=pos(r.floor);g.appendChild(t)}
  if(r.compare){const t=el('div','tick ln');t.style.left=pos(r.compare.line);g.appendChild(t)}
  const pt=el('div','pt');pt.style.left=pos(r.prediction);g.appendChild(pt);box.appendChild(g);
  const ends=el('div','ends');ends.appendChild(el('span',null,n0(a)));ends.appendChild(el('span',null,n0(b)));box.appendChild(ends);
  const lg=el('div','legend');
  const item=(color,title,text,dashed)=>{const d=el('div'),s=el('span');const sw=el('i','sw');
    if(dashed){sw.style.width='0';sw.style.borderLeft='2px dashed '+color;sw.style.height='12px'}else sw.style.background=color;
    s.appendChild(sw);s.appendChild(document.createTextNode(title));d.appendChild(s);d.appendChild(document.createTextNode(text));lg.appendChild(d)};
  item('rgba(88,166,255,.75)','Likely range (80%)',n0(i80.low)+' to '+n0(i80.high)+' '+u);
  item('rgba(88,166,255,.3)','Almost certain (95%)',n0(i95.low)+' to '+n0(i95.high)+' '+u);
  if(r.floor!=null)item('#8b949e',meta.floor.label.replace(/^./,c=>c.toUpperCase()),n1(r.floor)+' '+u,true);
  if(r.compare)item('#d29922','Line you entered',n1(r.compare.line)+' '+u,true);
  box.appendChild(lg);
  if(r.compare){const c=r.compare,l=el('div','lean');
    l.textContent=Math.abs(c.gap)<1.5?'Right on the line. No real lean either way ('+Math.round(c.p_over*100)+'% chance of going over).'
      :'Model leans '+c.lean.toUpperCase()+' by '+n1(Math.abs(c.gap))+' '+u+'. About '+Math.round(c.p_over*100)+'% chance of going over.';
    box.appendChild(l)}
  const why=el('div','blk');why.appendChild(el('h3',null,'The short version'));why.appendChild(el('p',null,r.synopsis));box.appendChild(why);
  if(r.warnings.length){const w=el('div','warn');w.appendChild(el('b',null,'Unusual inputs'));const ul=el('ul');r.warnings.forEach(t=>ul.appendChild(el('li',null,t)));w.appendChild(ul);box.appendChild(w)}
  const d=el('div','blk');d.appendChild(el('h3',null,'What moved this prediction'));
  d.appendChild(el('p','note','Start from an average game ('+n1(r.baseline)+' '+u+'). Each bar shows how many points your input adds or removes.'));
  const mx=Math.max(1,...r.drivers.map(x=>Math.abs(x.effect)));
  r.drivers.forEach(x=>{const row=el('div','drv'),nm=el('div','nm',(x.side?x.side+' ':'')+x.label.toLowerCase().replace(/^./,c=>x.side?c:c.toUpperCase()));
    nm.appendChild(el('small',null,n1(x.value)+(x.unit?' '+x.unit:'')+(x.computed?' (computed)':'')+' · typical '+n1(x.typical)));
    const tr=el('div','tr'),i=el('i'),w=Math.abs(x.effect)/mx*50;i.style.width=w+'%';i.style.left=x.effect>=0?'50%':(50-w)+'%';
    i.style.background=x.effect>=0?'var(--up)':'var(--down)';tr.appendChild(i);
    row.appendChild(nm);row.appendChild(tr);const tiny=Math.abs(x.effect)<0.05;row.appendChild(el('div','v '+(tiny?'':x.effect>=0?'up':'dn'),tiny?'0':sg(x.effect)));d.appendChild(row)});
  box.appendChild(d);
  box.scrollIntoView({behavior:'smooth',block:'start'});
}
async function run(){
  const btn=$('dyno');btn.disabled=true;btn.textContent='...';
  try{
    const body={inputs:vals};const lv=lineInput?parseFloat(lineInput.value):NaN;if(!isNaN(lv))body.line=lv;
    const r=await fetch('/api/models/'+SLUG+'/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const j=await r.json();if(!r.ok)throw new Error(j.detail||r.status);render(j);
  }catch(e){const box=$('result');box.hidden=false;box.replaceChildren(el('p',null,'Could not run the model: '+e.message))}
  btn.disabled=false;btn.textContent='DYNO';
}
fetch('/api/models/'+SLUG).then(r=>r.json()).then(m=>{meta=m;build();$('dyno').onclick=run;
  $('reset').onclick=()=>{meta.features.forEach(f=>ctl[f.name](f.default));if(lineInput)lineInput.value='';$('result').hidden=true}});
</script></main></body></html>"""

NCR = HEAD.replace("__TITLE__", "NCR Classifier · ddyno") + """
<a class="back" href="/">&larr; ddyno</a>
<p class="cat">Manufacturing</p>
<h1>NCR Classifier</h1><p class="sub">TF-IDF + logistic regression trained on a small synthetic set. Demo model, swap in real data to iterate.</p>
<textarea id="t" placeholder="e.g. bore diameter oversize after final grind"></textarea>
<div class="chips" id="ex" style="margin-top:12px"></div>
<button class="btn" id="go">Classify</button>
<div id="out"></div>
<script>
const ex=["scratches on sealing surface","missing washer during final assembly","calibration sticker expired on gauge","porosity found in casting"];
const t=document.getElementById('t'),out=document.getElementById('out'),go=document.getElementById('go');
ex.forEach(s=>{const c=document.createElement('span');c.className='chip';c.textContent=s;c.onclick=()=>{t.value=s;run()};document.getElementById('ex').appendChild(c)});
async function run(){
  if(t.value.trim().length<3)return;go.disabled=true;
  try{
    const r=await fetch('/api/classify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t.value})});
    if(!r.ok)throw new Error(r.status);
    const {predictions}=await r.json();out.replaceChildren();
    predictions.forEach(p=>{const row=document.createElement('div');row.className='row';const b=document.createElement('b');
      const a=document.createElement('span');a.textContent=p.label;const c=document.createElement('span');c.textContent=(p.score*100).toFixed(1)+'%';b.append(a,c);
      const bar=document.createElement('div');bar.className='bar';const i=document.createElement('i');i.style.width=(p.score*100)+'%';bar.appendChild(i);row.append(b,bar);out.appendChild(row)});
  }catch(e){out.textContent='Error: '+e.message}
  go.disabled=false;
}
go.onclick=run;
</script></main></body></html>"""
