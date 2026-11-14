"""HTML for ddyno pages. Plain strings, no build step.

One visual language for every page: dark surface, row-based lists, right-aligned tabular numbers,
tinted change pills, hairline borders. Tokens live in :root. Pages only read the existing API."""

CSS = """
:root{--bg:#0d1117;--card:#161b22;--raise:#1c232d;--line:#30363d;--hair:#21262d;--fg:#e6edf3;--mute:#8b949e;
--acc:#58a6ff;--up:#3fb950;--down:#f0883e;--neg:#f85149;--warn:#d29922;--ink:#04111f;
--r:14px;--r-sm:9px;--pad:20px}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--acc)}button{font:inherit;cursor:pointer;color:inherit}
h1,h2,h3,p{margin:0}
.num,.val,.pill,td,th,.big,.kv b{font-variant-numeric:tabular-nums}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px;border-radius:6px}

/* shell */
.top{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;height:56px;padding:0 var(--pad);
background:rgba(13,17,23,.82);-webkit-backdrop-filter:saturate(1.4) blur(14px);backdrop-filter:saturate(1.4) blur(14px);border-bottom:1px solid var(--hair)}
.brand{font-weight:800;font-size:1.15rem;letter-spacing:-.02em;color:var(--fg);text-decoration:none;display:inline-flex;align-items:center;gap:8px;min-height:44px}
.brand i{width:10px;height:10px;border-radius:3px;background:var(--acc);display:block}
.crumb{color:var(--mute);font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.crumb:before{content:"/";margin-right:10px;color:var(--line)}
.wrap{max-width:1200px;margin:0 auto;padding:28px var(--pad) 72px}
.title{font-size:clamp(2rem,6vw,2.6rem);line-height:1.08;font-weight:800;letter-spacing:-.025em}
.title span{display:block;color:var(--mute)}
.lede{color:var(--mute);margin-top:10px;max-width:60ch}
.eyebrow{color:var(--acc);font-size:.86rem;font-weight:600;margin-bottom:6px}
.card{background:var(--card);border:1px solid var(--hair);border-radius:var(--r)}
.sech{display:flex;justify-content:space-between;align-items:baseline;gap:12px;color:var(--mute);font-size:.86rem;font-weight:600;padding:0 2px 8px}
.pill{display:inline-block;min-width:58px;padding:3px 8px;border-radius:7px;font-size:.86rem;font-weight:600;text-align:right;white-space:nowrap}
.pill.up{background:rgba(63,185,80,.16);color:var(--up)}.pill.dn{background:rgba(248,81,73,.16);color:#ff7b72}
.pill.flat{background:var(--hair);color:var(--mute)}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 20px;border-radius:11px;border:0;background:var(--acc);color:var(--ink);font-weight:700;text-decoration:none}
.btn:disabled{opacity:.6}.btn.ghost{background:transparent;border:1px solid var(--line);color:var(--fg);font-weight:600}
.note{color:var(--mute);font-size:.86rem}
.empty{color:var(--mute);padding:28px 4px}
footer{color:var(--mute);font-size:.82rem;margin-top:36px}

/* hub */
.tools{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:26px 0 22px}
.search{flex:1 1 240px;max-width:380px;height:44px;border-radius:11px;border:1px solid var(--hair);background:var(--card);color:var(--fg);font:inherit;padding:0 14px}
.search::placeholder{color:var(--mute)}
.seg{display:inline-flex;background:var(--card);border:1px solid var(--hair);border-radius:11px;padding:3px;max-width:100%;overflow-x:auto}
.seg button{min-height:38px;padding:0 14px;border:0;border-radius:8px;background:transparent;color:var(--mute);font-weight:600;font-size:.92rem;white-space:nowrap}
.seg button[aria-pressed=true],.seg button[aria-selected=true]{background:var(--raise);color:var(--fg);box-shadow:inset 0 0 0 1px var(--line)}
.hubcols{display:grid;grid-template-columns:minmax(0,1fr);gap:28px}
.group{margin-bottom:26px}
.rows{border-top:1px solid var(--hair)}
.row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;align-items:center;gap:16px;padding:14px 6px;min-height:76px;border-bottom:1px solid var(--hair);color:inherit;text-decoration:none;border-radius:0}
.row:hover,.row.sel{background:linear-gradient(90deg,rgba(88,166,255,.07),transparent 70%)}
.row h3{font-size:1.08rem;font-weight:700;letter-spacing:-.01em}
.row p{color:var(--mute);font-size:.9rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.row svg{display:block}
.row .rt{text-align:right;min-width:92px}
.row .val{font-weight:700;font-size:1.08rem;display:block}.row .val small{font-weight:500;color:var(--mute);font-size:.8rem;margin-left:4px}
.row .rt .pill{margin-top:4px}
.panel{display:none}
.kv{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--hair);font-size:.92rem}
.kv:last-child{border-bottom:0}.kv span{color:var(--mute)}.kv b{font-weight:600;white-space:nowrap}
.rank{display:grid;grid-template-columns:minmax(0,1fr) 72px auto;gap:10px;align-items:center;padding:8px 0;font-size:.9rem}
.rank .tr{height:6px;border-radius:3px;background:var(--hair);overflow:hidden}.rank .tr i{display:block;height:100%;background:#484f58;border-radius:3px}
.rank.me{font-weight:700}.rank.me .tr i{background:var(--acc)}
.rank b{font-weight:600;min-width:58px;text-align:right}

/* model page */
.mhead{margin-bottom:22px}
.cols{display:grid;grid-template-columns:minmax(0,1fr);gap:22px}
.inputs{padding:6px 18px 0}
.grp{padding:14px 0;border-bottom:1px solid var(--hair)}.grp:last-of-type{border-bottom:0}
.grp>h2{display:flex;align-items:center;gap:8px;font-size:.86rem;font-weight:700;color:var(--mute);margin-bottom:6px}
.grp>h2 i{width:8px;height:8px;border-radius:50%;background:var(--acc)}.grp.away>h2 i{background:var(--down)}.grp.shared>h2 i{background:var(--mute)}
.f{padding:8px 0}
.fh{display:flex;justify-content:space-between;align-items:center;gap:10px;min-height:44px}
.fh label,.f>label{font-size:.95rem;font-weight:600;line-height:1.25}.fh label small{color:var(--mute);font-weight:400;margin-left:4px}
.num{width:76px;height:42px;flex:none;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:var(--r-sm);padding:0 6px;font:inherit;font-weight:700;text-align:center}
.num:focus{outline:2px solid var(--acc);outline-offset:0}
.f p{color:var(--mute);font-size:.8rem;line-height:1.35;margin-top:2px}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:36px;background:transparent;margin:0;touch-action:pan-y;--c:var(--acc);--p:50%}
.away input[type=range]{--c:var(--down)}
input[type=range]::-webkit-slider-runnable-track{height:6px;border-radius:3px;background:linear-gradient(90deg,var(--c) var(--p),var(--line) var(--p))}
input[type=range]::-moz-range-track{height:6px;border-radius:3px;background:var(--line)}
input[type=range]::-moz-range-progress{height:6px;border-radius:3px;background:var(--c)}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:28px;height:28px;border-radius:50%;background:var(--c);border:4px solid var(--card);box-shadow:0 0 0 1px var(--line);margin-top:-11px}
input[type=range]::-moz-range-thumb{width:22px;height:22px;border-radius:50%;background:var(--c);border:4px solid var(--card);box-shadow:0 0 0 1px var(--line)}
.choice{display:flex;gap:4px;background:var(--bg);border:1px solid var(--line);border-radius:11px;padding:3px;margin-top:8px}
.choice button{flex:1;min-height:40px;border:0;border-radius:8px;background:transparent;color:var(--mute);font-weight:600}
.choice button.on{background:var(--acc);color:var(--ink)}
.actions{position:fixed;left:0;right:0;bottom:0;z-index:15;display:flex;align-items:center;gap:12px;padding:10px var(--pad) calc(10px + env(safe-area-inset-bottom));
background:rgba(22,27,34,.9);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);border-top:1px solid var(--line)}
.actions .mini{flex:1;min-width:0;background:none;border:0;padding:0;text-align:left;min-height:46px}
.actions .mini span{display:block;color:var(--mute);font-size:.76rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.actions .mini b{font-size:1.25rem;font-weight:800;font-variant-numeric:tabular-nums}
#dyno{min-width:118px;font-size:1.05rem}
#reset{padding:0 14px}
body.has-actions .wrap{padding-bottom:120px}
#out{scroll-margin-top:68px;min-width:0}.tabs{margin-bottom:16px}
.pane[hidden]{display:none}
.hero{padding:20px}
.hero .lab{color:var(--mute);font-size:.9rem;font-weight:600}
.big{font-size:clamp(3rem,13vw,4.4rem);font-weight:800;line-height:1;letter-spacing:-.03em;margin:6px 0 2px}
.big small{font-size:1rem;font-weight:500;color:var(--mute);margin-left:8px;letter-spacing:0}
.stale .hero{opacity:.55}.stalemsg{display:none;margin-bottom:12px;padding:10px 14px;border:1px solid var(--line);border-radius:11px;color:var(--mute);font-size:.9rem;background:var(--card)}
.stale .stalemsg{display:block}
.duo{display:flex;justify-content:space-between;align-items:flex-end;gap:12px}.duo .r{text-align:right}
.duo span{display:flex;align-items:center;gap:7px;color:var(--mute);font-size:.9rem;font-weight:600}.duo .r span{justify-content:flex-end}
.duo span i{width:8px;height:8px;border-radius:50%;background:var(--acc)}.duo .r span i{background:var(--down)}
.split{position:relative;height:14px;border-radius:7px;background:var(--down);margin:16px 0 10px}
.split>i{display:block;height:100%;border-radius:7px 0 0 7px;background:var(--acc)}
.split .band{position:absolute;top:-5px;bottom:-5px;border-left:2px solid var(--fg);border-right:2px solid var(--fg);background:rgba(230,237,243,.18);border-radius:2px}
.rng{position:relative;height:38px;margin:20px 0 6px}
.rng .trk{position:absolute;left:0;right:0;top:15px;height:8px;border-radius:4px;background:var(--hair)}
.rng .b95{position:absolute;top:11px;height:16px;border-radius:8px;background:rgba(88,166,255,.25)}
.rng .b80{position:absolute;top:8px;height:22px;border-radius:11px;background:rgba(88,166,255,.6)}
.rng .pt{position:absolute;top:2px;width:4px;height:34px;margin-left:-2px;border-radius:2px;background:#fff}
.rng .tick{position:absolute;top:0;height:38px;border-left:2px dashed var(--mute)}.rng .tick.ln{border-color:var(--warn)}
.ends{display:flex;justify-content:space-between;color:var(--mute);font-size:.8rem;font-variant-numeric:tabular-nums}
.legend{display:grid;grid-template-columns:1fr 1fr;gap:10px 16px;margin-top:14px;font-size:.95rem;font-weight:600;font-variant-numeric:tabular-nums}
.legend span{color:var(--mute);display:block;font-size:.8rem;font-weight:400}
.sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
.lean{margin-top:16px;padding:12px 14px;border-radius:11px;background:var(--raise);border:1px solid var(--line);font-size:.95rem}
.below{display:grid;grid-template-columns:minmax(0,1fr);gap:16px;margin-top:16px}
.blk{padding:18px 20px}.blk h3{font-size:.86rem;color:var(--mute);font-weight:700;margin-bottom:8px}
.blk>p{max-width:64ch}
.drv{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(56px,1fr) auto;gap:12px;align-items:center;padding:10px 0;border-top:1px solid var(--hair);font-size:.93rem;font-weight:600}
.drv .nm small{color:var(--mute);display:block;font-size:.8rem;font-weight:400}
.drv .tr{position:relative;height:8px;background:var(--hair);border-radius:4px}
.drv .tr:before{content:"";position:absolute;left:50%;top:-4px;bottom:-4px;border-left:1px solid var(--mute)}
.drv .tr i{position:absolute;top:0;height:8px;border-radius:4px}
.warnbox{border:1px solid var(--warn);background:rgba(210,153,34,.1);border-radius:11px;padding:12px 14px;margin-top:16px;font-size:.9rem}
.warnbox ul{margin:4px 0 0;padding-left:18px}
.fig{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;padding:18px 0;border-top:1px solid var(--hair)}
.fig:first-child{border-top:0;padding-top:4px}
.fig img{display:block;width:100%;height:auto;border-radius:11px;border:1px solid var(--hair);background:var(--card)}
.fig h3{font-size:1.05rem;font-weight:700;margin-bottom:6px}.fig p{color:var(--fg);font-size:.93rem;max-width:58ch}
.fig .tool{display:inline-block;margin-top:10px;color:var(--mute);font-size:.8rem;border:1px solid var(--line);border-radius:6px;padding:1px 7px}
.about h3{font-size:1.05rem;font-weight:700;color:var(--fg);margin:26px 0 8px}.about h3:first-child{margin-top:0}
.about ul{margin:0;padding-left:20px}.about li{margin:0 0 8px;font-size:.95rem;max-width:68ch}
.about p{max-width:68ch}
.tw{overflow-x:auto;margin:8px 0}
table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{text-align:right;padding:9px 8px;border-bottom:1px solid var(--hair);white-space:nowrap}
th:first-child,td:first-child{text-align:left;white-space:normal;padding-left:0}th{color:var(--mute);font-weight:600;font-size:.8rem}
tr.me td{font-weight:700;color:var(--fg)}tr.me td:first-child{box-shadow:inset 3px 0 0 var(--acc);padding-left:10px}
.roc{display:block;width:100%;max-width:280px;margin:8px 0}

/* ncr */
textarea{width:100%;min-height:120px;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:var(--r);padding:14px;font:inherit;resize:vertical}
.ex{display:block;width:100%;text-align:left;background:none;border:0;border-bottom:1px solid var(--hair);padding:12px 4px;min-height:46px;color:var(--fg)}
.ex:hover{background:linear-gradient(90deg,rgba(88,166,255,.07),transparent 70%)}

@media(min-width:700px){
  .fig{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:24px;align-items:center}
  .row{padding:14px 10px}
}
@media(max-width:519px){.row .spark{display:none}.row{grid-template-columns:minmax(0,1fr) auto}}
@media(min-width:980px){
  :root{--pad:32px}
  .hubcols{grid-template-columns:minmax(0,1fr) 400px;gap:36px;align-items:start}
  .panel{display:block;position:sticky;top:76px;padding:22px}
  .panel h2{font-size:1.35rem;font-weight:800;letter-spacing:-.015em}
  .panel .sub{color:var(--mute);font-size:.93rem;margin:6px 0 16px}
  .panel .ph{color:var(--mute);font-size:.82rem;font-weight:700;margin:20px 0 4px}
  .panel .big{font-size:3rem}
  .panel .btn{width:100%;margin-top:20px}
  .cols{grid-template-columns:380px minmax(0,1fr);gap:28px;align-items:start}
  .inputs{position:sticky;top:76px;max-height:calc(100vh - 96px);overflow:auto;padding:6px 20px 0}
  .actions{position:sticky;bottom:0;left:auto;right:auto;margin:0 -20px;padding:14px 20px;background:var(--card);-webkit-backdrop-filter:none;backdrop-filter:none;border-top:1px solid var(--hair);border-radius:0 0 var(--r) var(--r)}
  .actions .mini{display:none}#dyno{flex:1}
  body.has-actions .wrap{padding-bottom:72px}
  .hero{padding:26px 28px}
}
@media(min-width:1180px){.below{grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);align-items:start}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
"""

HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0d1117">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230d1117'/%3E%3Crect x='9' y='9' width='14' height='14' rx='4' fill='%2358a6ff'/%3E%3C/svg%3E">
<title>__TITLE__</title><style>""" + CSS + """</style></head><body>"""

HUB = HEAD.replace("__TITLE__", "ddyno") + """
<header class="top"><a class="brand" href="/"><i></i>ddyno</a></header>
<div class="wrap">
<h1 class="title">Models<span id="count">Loading</span></h1>
<p class="lede">Set the inputs, press Dyno, and see what each model predicts and why.</p>
<div class="tools"><input class="search" id="q" type="search" placeholder="Search models" aria-label="Search models"><div class="seg" id="cats" role="group" aria-label="Category"></div></div>
<div class="hubcols"><div id="list"></div><aside class="panel card" id="panel" aria-live="polite"></aside></div>
<footer>Model numbers are test results on games each model never saw.</footer>
</div>
<script>
const $=id=>document.getElementById(id);
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const NS='http://www.w3.org/2000/svg';
const svg=(n,at)=>{const e=document.createElementNS(NS,n);Object.keys(at).forEach(k=>e.setAttribute(k,at[k]));return e};
const n1=v=>(Math.round(v*10)/10).toFixed(1), sg=v=>(v>0?'+':v<0?'−':'')+n1(Math.abs(v));
let models=[],metas={},preds={},cat='All',sel=null;
const wide=()=>matchMedia('(min-width:980px)').matches;

/* headline test metric for a model, straight from its card */
function stat(meta){
  const a=meta.card.accuracy,me=a[0],rest=a.slice(1);
  if(meta.type==='logistic_regression'){const best=Math.max(...rest.map(x=>x.accuracy));
    return {value:Math.round(me.accuracy*100)+'%',unit:'accuracy',diff:(me.accuracy-best)*100,good:me.accuracy>best,suffix:' pts',
      rows:a.map(x=>({name:x.name,v:x.accuracy,show:Math.round(x.accuracy*100)+'%'})),caption:'Share of test games picked right'}}
  const best=Math.min(...rest.map(x=>x.mae));
  return {value:n1(me.mae),unit:'pts avg miss',diff:me.mae-best,good:me.mae<best,suffix:' pts',
    rows:a.map(x=>({name:x.name,v:x.mae,show:n1(x.mae)+' pts'})),caption:'Average miss on test games (lower is better)'};
}
function spark(st){
  const h=8*st.rows.length-3,s=svg('svg',{viewBox:'0 0 64 '+h,width:64,height:h,'class':'spark','aria-hidden':'true'}),mx=Math.max(...st.rows.map(r=>r.v));
  st.rows.forEach((r,i)=>s.appendChild(svg('rect',{x:0,y:i*8,width:Math.max(3,r.v/mx*64),height:5,rx:2.5,fill:i?'#484f58':'#58a6ff'})));
  return s;
}
function row(m){
  const a=el('a','row'+(sel===m.slug?' sel':''));a.href=m.url;a.dataset.slug=m.slug;
  const l=el('div');l.appendChild(el('h3',null,m.name));l.appendChild(el('p',null,m.summary));a.appendChild(l);
  const meta=metas[m.slug],rt=el('div','rt');
  if(meta){const st=stat(meta);a.appendChild(spark(st));
    const v=el('span','val',st.value);v.appendChild(el('small',null,st.unit));rt.appendChild(v);
    const p=el('span','pill '+(Math.abs(st.diff)<0.05?'flat':st.good?'up':'dn'),sg(st.diff)+st.suffix);p.title='Compared with the best simple method';rt.appendChild(p);
  }else{a.appendChild(el('span','spark'));rt.appendChild(el('span','pill flat','Demo'))}
  a.appendChild(rt);
  a.addEventListener('mouseenter',()=>{if(wide())pick(m.slug)});a.addEventListener('focus',()=>{if(wide())pick(m.slug)});
  return a;
}
function draw(){
  const q=$('q').value.trim().toLowerCase(),list=$('list'),cats=[...new Set(models.map(m=>m.category))];
  $('cats').replaceChildren(...['All',...cats].map(c=>{const b=el('button',null,c);b.type='button';b.setAttribute('aria-pressed',c===cat);b.onclick=()=>{cat=c;draw()};return b}));
  const show=models.filter(m=>(cat==='All'||m.category===cat)&&(!q||(m.name+' '+m.summary+' '+m.category).toLowerCase().includes(q)));
  list.replaceChildren();
  if(!show.length){const e=el('p','empty','No models match that search.');const b=el('button','btn ghost','Clear search');b.onclick=()=>{$('q').value='';cat='All';draw()};
    list.appendChild(e);list.appendChild(b);return}
  cats.forEach(c=>{const ms=show.filter(m=>m.category===c);if(!ms.length)return;
    const g=el('section','group'),h=el('div','sech');h.appendChild(el('span',null,c));h.appendChild(el('span',null,ms.length+(ms.length===1?' model':' models')));
    const r=el('div','rows');ms.forEach(m=>r.appendChild(row(m)));g.appendChild(h);g.appendChild(r);list.appendChild(g)});
}
function pick(slug){
  if(sel===slug)return;sel=slug;
  document.querySelectorAll('.row').forEach(r=>r.classList.toggle('sel',r.dataset.slug===slug));
  panel();
}
function panel(){
  const p=$('panel'),m=models.find(x=>x.slug===sel);if(!m){p.replaceChildren();return}
  const meta=metas[m.slug];p.replaceChildren();
  p.appendChild(el('p','eyebrow',m.category));p.appendChild(el('h2',null,m.name));p.appendChild(el('p','sub',m.summary));
  if(meta){
    p.appendChild(el('p','ph','With typical inputs'));const box=el('div');p.appendChild(box);preview(m.slug,meta,box);
    const st=stat(meta);p.appendChild(el('p','ph',st.caption));const mx=Math.max(...st.rows.map(r=>r.v));
    st.rows.forEach((r,i)=>{const d=el('div','rank'+(i?'':' me'));d.appendChild(el('span',null,r.name));const t=el('div','tr'),b=el('i');b.style.width=(r.v/mx*100)+'%';t.appendChild(b);d.appendChild(t);d.appendChild(el('b',null,r.show));p.appendChild(d)});
    p.appendChild(el('p','ph','Details'));
    const kv=(k,v)=>{const d=el('div','kv');d.appendChild(el('span',null,k));d.appendChild(el('b',null,v));p.appendChild(d)};
    kv('Inputs you set',meta.features.length);kv('Trained on',meta.card.n_games.toLocaleString()+' games');kv('Seasons',meta.card.seasons[0]+' to '+meta.card.seasons[1]);kv('Last trained',meta.card.trained_on);
  }
  const b=el('a','btn','Open model');b.href=m.url;p.appendChild(b);
}
function preview(slug,meta,box){
  const paint=r=>{if(!box.isConnected)return;box.replaceChildren();
    if(r.kind==='probability'){const pc=Math.round(r.probability*100),duo=el('div','duo'),l=el('div'),rt=el('div','r');
      const a=el('span');a.appendChild(el('i'));a.appendChild(document.createTextNode(r.labels.positive));l.appendChild(a);l.appendChild(el('div','big',pc+'%'));
      const c=el('span');c.appendChild(document.createTextNode(r.labels.negative));c.appendChild(el('i'));rt.appendChild(c);rt.appendChild(el('div','big',(100-pc)+'%'));
      duo.appendChild(l);duo.appendChild(rt);box.appendChild(duo);const s=el('div','split'),i=el('i');i.style.width=(r.probability*100)+'%';s.appendChild(i);box.appendChild(s);
    }else{const u=meta.target.unit||'',big=el('div','big',n1(r.prediction));big.appendChild(el('small',null,u));box.appendChild(big);
      box.appendChild(el('p','note','Likely range '+Math.round(r.intervals['80'].low)+' to '+Math.round(r.intervals['80'].high)+' '+u))}};
  if(preds[slug])return paint(preds[slug]);
  box.appendChild(el('p','note','Running the model'));
  const inputs={};meta.features.forEach(f=>inputs[f.name]=f.default);
  fetch('/api/models/'+slug+'/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({inputs})})
    .then(r=>r.ok?r.json():Promise.reject()).then(r=>{preds[slug]=r;if(sel===slug)paint(r)}).catch(()=>{if(box.isConnected)box.replaceChildren(el('p','note','Preview unavailable right now.'))});
}
$('q').addEventListener('input',draw);
fetch('/api/models').then(r=>r.json()).then(d=>{
  models=d.models;const cats=new Set(models.map(m=>m.category)).size;
  $('count').textContent=models.length+' live in '+cats+(cats===1?' category':' categories');
  draw();
  return Promise.all(models.filter(m=>m.url.indexOf('/m/')===0).map(m=>fetch('/api/models/'+m.slug).then(r=>r.ok?r.json():null).then(j=>{if(j)metas[m.slug]=j}).catch(()=>{})));
}).then(()=>{draw();if(models.length){sel=null;pick(models[0].slug)}})
.catch(()=>{$('count').textContent='Unavailable';$('list').replaceChildren(el('p','empty','Could not load the models. Refresh to try again.'))});
</script></body></html>"""

MODEL = HEAD.replace("__TITLE__", "__NAME__ · ddyno") + """
<header class="top"><a class="brand" href="/"><i></i>ddyno</a><span class="crumb" id="crumb"></span></header>
<div class="wrap">
<div class="mhead"><p class="eyebrow" id="cat"></p><h1 class="title" id="name">__NAME__</h1><p class="lede" id="summary"></p></div>
<div class="cols">
  <section class="inputs card" id="inputs" aria-label="Inputs">
    <div id="groups"></div>
    <div class="actions"><button class="mini" id="mini" type="button" aria-label="Jump to the prediction"><span id="miniLab">Prediction</span><b id="miniVal">–</b></button>
      <button class="btn ghost" id="reset" type="button">Reset</button><button class="btn" id="dyno" type="button">Dyno</button></div>
  </section>
  <div id="out">
    <div class="seg tabs" role="tablist" aria-label="Model sections">
      <button role="tab" id="t-pred" aria-selected="true" aria-controls="p-pred" type="button">Prediction</button>
      <button role="tab" id="t-diag" aria-selected="false" aria-controls="p-diag" type="button">Diagnostics</button>
      <button role="tab" id="t-about" aria-selected="false" aria-controls="p-about" type="button">About</button>
    </div>
    <div class="pane" id="p-pred" role="tabpanel" aria-labelledby="t-pred"><p class="stalemsg">Inputs changed. Press Dyno to update the prediction.</p><div id="result"><p class="empty">Running the model with typical inputs.</p></div></div>
    <div class="pane" id="p-diag" role="tabpanel" aria-labelledby="t-diag" hidden><p class="note" id="diagLede" style="margin-bottom:10px"></p><div id="plotList"></div></div>
    <div class="pane about card blk" id="p-about" role="tabpanel" aria-labelledby="t-about" hidden></div>
    <footer id="foot"></footer>
  </div>
</div>
</div>
<script>
const SLUG="__SLUG__";
const $=id=>document.getElementById(id);
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const n1=v=>(Math.round(v*10)/10).toString(), n0=v=>Math.round(v).toString();
const sg=v=>(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(1);
let meta,vals={},ctl={},lineInput,ran=false;
document.body.classList.add('has-actions');

function tab(id){['pred','diag','about'].forEach(k=>{$('t-'+k).setAttribute('aria-selected',k===id);$('p-'+k).hidden=k!==id})}
['pred','diag','about'].forEach(k=>$('t-'+k).onclick=()=>tab(k));
function stale(){if(ran)$('p-pred').classList.add('stale')}

function field(f){
  if(f.choices){const w=el('div','f'),seg=el('div','choice'),btn={};w.appendChild(el('label',null,f.label));
    const set=(v,user)=>{vals[f.name]=v;Object.keys(btn).forEach(k=>{btn[k].className=(+k===v?'on':'');btn[k].setAttribute('aria-pressed',+k===v)});if(user)stale()};
    Object.keys(f.choices).forEach(k=>{const b=el('button',null,f.choices[k]);b.type='button';b.onclick=()=>set(+k,true);btn[k]=b;seg.appendChild(b)});
    ctl[f.name]=set;set(f.default);w.appendChild(seg);w.appendChild(el('p',null,f.description));return w}
  const w=el('div','f'),h=el('div','fh'),lab=el('label',null,f.label);
  if(f.unit)lab.appendChild(el('small',null,f.unit));
  const num=el('input','num');num.type='number';num.inputMode='decimal';num.step=f.step;num.min=f.hard_min;num.max=f.hard_max;
  const rng=el('input');rng.type='range';rng.min=f.min;rng.max=f.max;rng.step=f.step;
  lab.htmlFor=num.id='n_'+f.name;rng.setAttribute('aria-label',f.label);
  const set=(v,from)=>{v=Math.min(f.hard_max,Math.max(f.hard_min,v));vals[f.name]=v;if(from!=='num')num.value=v;if(from!=='rng')rng.value=v;
    rng.style.setProperty('--p',Math.min(100,Math.max(0,(v-f.min)/(f.max-f.min)*100))+'%');if(from)stale()};
  rng.oninput=()=>set(parseFloat(rng.value),'rng');
  num.oninput=()=>{const v=parseFloat(num.value);if(!isNaN(v))set(v,'num')};
  num.onblur=()=>{num.value=vals[f.name]};
  ctl[f.name]=set;set(f.default);
  h.appendChild(lab);h.appendChild(num);w.appendChild(h);w.appendChild(rng);w.appendChild(el('p',null,f.description));
  return w;
}
function build(){
  $('cat').textContent=meta.category;$('crumb').textContent=meta.category;$('name').textContent=meta.name;$('summary').textContent=meta.summary;
  const box=$('groups'),sides=[['home','Home'],['away','Away']].filter(s=>meta.features.some(f=>f.side===s[0]));
  const grp=(cls,title,fs)=>{const g=el('div','grp '+cls),h=el('h2');h.appendChild(el('i'));h.appendChild(document.createTextNode(title));g.appendChild(h);fs.forEach(f=>g.appendChild(field(f)));box.appendChild(g);return g};
  sides.forEach(([k,title])=>grp(k,title,meta.features.filter(f=>f.side===k)));
  const sh=meta.features.filter(f=>f.side==='shared');
  if(sh.length)grp('shared',sides.length?'Game context':'Inputs',sh);
  if(meta.compare_line){const g=grp('shared','Compare',[]),w=el('div','f'),h=el('div','fh'),lab=el('label',null,meta.compare_line.label);
    lineInput=el('input','num');lineInput.type='number';lineInput.inputMode='decimal';lineInput.step=meta.compare_line.step;lineInput.placeholder='–';lineInput.id='line';lab.htmlFor='line';
    lineInput.oninput=stale;h.appendChild(lab);h.appendChild(lineInput);w.appendChild(h);g.appendChild(w)}
  $('miniLab').textContent=meta.target.label;
  plots();about();$('foot').textContent=meta.card.disclaimer||'';
}
function plots(){
  const box=$('plotList'),ps=meta.plots||[];
  if(!ps.length){$('diagLede').textContent='';box.appendChild(el('p','empty','No diagnostic plots have been published for this model yet.'));return}
  $('diagLede').textContent='The standard checks for this kind of model, drawn from its real test games, each with a short reading guide.';
  ps.forEach(p=>{const f=el('figure','fig');f.style.margin='0';const im=el('img');im.src=p.url;im.loading='lazy';im.alt=p.title+'. '+p.text;f.appendChild(im);
    const c=el('figcaption');c.appendChild(el('h3',null,p.title));c.appendChild(el('p',null,p.text));c.appendChild(el('span','tool','Made with '+p.tool));f.appendChild(c);box.appendChild(f)});
}
function about(){
  const c=meta.card,b=$('p-about');
  b.appendChild(el('h3',null,'What the model learned'));
  const ul=el('ul');c.findings.forEach(t=>ul.appendChild(el('li',null,t)));b.appendChild(ul);
  b.appendChild(el('h3',null,'How accurate is it?'));
  b.appendChild(el('p','note','Tested on the '+c.holdout_label+'.'));
  const cols=c.accuracy_columns||[['mae','Average miss','pts'],['rmse','RMSE','num1'],['r2','R²','num']];
  const show=(v,k)=>v==null?'–':k==='pct'?Math.round(v*100)+'%':k==='pts'?v.toFixed(1)+' pts':k==='num1'?v.toFixed(1):v.toFixed(2);
  const t=el('table'),hr=el('tr');['Method',...cols.map(x=>x[1])].forEach(x=>hr.appendChild(el('th',null,x)));t.appendChild(hr);
  c.accuracy.forEach((a,i)=>{const r=el('tr',i?'':'me');r.appendChild(el('td',null,a.name));cols.forEach(x=>r.appendChild(el('td',null,show(a[x[0]],x[2]))));t.appendChild(r)});
  const tw=el('div','tw');tw.appendChild(t);b.appendChild(tw);
  b.appendChild(el('p','note',c.metric_note||'Average miss is how far off the prediction was on a typical game. RMSE is similar but punishes big misses more. R² is the share of game-to-game differences the method explains (1.00 would be perfect).'));
  if(c.roc&&!(meta.plots||[]).length){b.appendChild(el('h3',null,'ROC curve'));
    const NS='http://www.w3.org/2000/svg',sv=document.createElementNS(NS,'svg');sv.setAttribute('viewBox','0 0 220 220');sv.setAttribute('class','roc');
    const mk=(n,at)=>{const e=document.createElementNS(NS,n);Object.keys(at).forEach(k=>e.setAttribute(k,at[k]));sv.appendChild(e);return e};
    mk('rect',{x:30,y:10,width:180,height:180,fill:'none',stroke:'#30363d'});
    mk('line',{x1:30,y1:190,x2:210,y2:10,stroke:'#8b949e','stroke-dasharray':'4 4'});
    mk('polyline',{points:c.roc.map(p=>(30+p[0]*180)+','+(190-p[1]*180)).join(' '),fill:'none',stroke:'#58a6ff','stroke-width':3});
    mk('text',{x:120,y:212,fill:'#8b949e','font-size':11,'text-anchor':'middle'}).textContent='False alarms (away wins called home)';
    mk('text',{x:12,y:100,fill:'#8b949e','font-size':11,'text-anchor':'middle',transform:'rotate(-90 12 100)'}).textContent='Home wins caught';
    b.appendChild(sv);
    b.appendChild(el('p','note','The further the blue line bows toward the top-left corner, the better the model separates wins from losses. The dashed line is a coin flip.'))}
  if(c.calibration){b.appendChild(el('h3',null,'Can you trust the percentages?'));
    b.appendChild(el('p','note','Test games grouped by what the model said, next to what really happened. Close numbers mean the percentages are honest.'));
    const ct=el('table'),ch=el('tr');['Model said','Games','Avg predicted','Home actually won'].forEach(x=>ch.appendChild(el('th',null,x)));ct.appendChild(ch);
    c.calibration.forEach(k=>{const r=el('tr');[k.range,k.n,Math.round(k.predicted*100)+'%',Math.round(k.actual*100)+'%'].forEach(x=>r.appendChild(el('td',null,x)));ct.appendChild(r)});
    const cw=el('div','tw');cw.appendChild(ct);b.appendChild(cw);
    if(c.confident)b.appendChild(el('p',null,'When the model was at least 80% sure (about '+Math.round(c.confident.share*100)+'% of test games), it was right '+Math.round(c.confident.accuracy*100)+'% of the time. When it was under 60% sure, it was right '+Math.round(c.confident.tossup_accuracy*100)+'% of the time.'))}
  if(c.coverage){b.appendChild(el('h3',null,'Can you trust the range?'));
    b.appendChild(el('p',null,'In the test games, the real final score landed inside the 80% range '+Math.round(c.coverage['80']*100)+'% of the time and inside the 95% range '+Math.round(c.coverage['95']*100)+'% of the time. That is what honest ranges should do.'))}
  b.appendChild(el('h3',null,'Limitations'));
  const ul2=el('ul');c.limitations.forEach(t=>ul2.appendChild(el('li',null,t)));b.appendChild(ul2);
  const tn=el('p','note',(c.model_kind||'Linear regression')+' trained on '+c.n_games.toLocaleString()+' games from the '+c.seasons[0]+' to '+c.seasons[1]+' seasons, after testing '+c.candidates_tested+' candidate inputs. Last trained '+c.trained_on+'. Data: nflverse.');
  tn.style.marginTop='18px';b.appendChild(tn);
}
function below(box,r,note){
  const g=el('div','below');
  const why=el('div','card blk');why.appendChild(el('h3',null,'The short version'));why.appendChild(el('p',null,r.synopsis));
  if(r.warnings.length){const w=el('div','warnbox');w.appendChild(el('b',null,'Unusual inputs'));const ul=el('ul');r.warnings.forEach(t=>ul.appendChild(el('li',null,t)));w.appendChild(ul);why.appendChild(w)}
  g.appendChild(why);
  const d=el('div','card blk');d.appendChild(el('h3',null,'What moved this prediction'));const nt=el('p','note',note);nt.style.marginBottom='10px';d.appendChild(nt);
  const mx=Math.max(1,...r.drivers.map(x=>Math.abs(x.effect)));
  r.drivers.forEach(x=>{const row=el('div','drv'),nm=el('div','nm',(x.side?x.side+' ':'')+x.label.toLowerCase().replace(/^./,c=>x.side?c:c.toUpperCase()));
    nm.appendChild(el('small',null,(x.value_label||n1(x.value)+(x.unit?' '+x.unit:''))+(x.computed?' (computed)':'')+(x.typical!=null?', typical '+n1(x.typical):'')));
    const tr=el('div','tr'),i=el('i'),w=Math.abs(x.effect)/mx*50;i.style.width=w+'%';i.style.left=x.effect>=0?'50%':(50-w)+'%';
    i.style.background=x.effect>=0?'var(--up)':'var(--neg)';tr.appendChild(i);
    const tiny=Math.abs(x.effect)<0.05;row.appendChild(nm);row.appendChild(tr);row.appendChild(el('span','pill '+(tiny?'flat':x.effect>=0?'up':'dn'),tiny?'0.0':sg(x.effect)));d.appendChild(row)});
  g.appendChild(d);box.appendChild(g);
}
function renderProb(r){
  const box=$('result');box.replaceChildren();const p=r.probability,P=r.labels.positive,N=r.labels.negative,pc=Math.round(p*100);
  const hero=el('div','card hero');hero.appendChild(el('p','lab','Chance to win the game'));
  const duo=el('div','duo'),l=el('div'),rt=el('div','r');
  const a=el('span');a.appendChild(el('i'));a.appendChild(document.createTextNode(P));l.appendChild(a);l.appendChild(el('div','big',pc+'%'));
  const c=el('span');c.appendChild(document.createTextNode(N));c.appendChild(el('i'));rt.appendChild(c);rt.appendChild(el('div','big',(100-pc)+'%'));
  duo.appendChild(l);duo.appendChild(rt);hero.appendChild(duo);
  const i95=r.intervals['95'],sp=el('div','split'),i=el('i');i.style.width=(p*100)+'%';sp.appendChild(i);
  const band=el('div','band');band.style.left=(i95.low*100)+'%';band.style.width=Math.max(0.6,(i95.high-i95.low)*100)+'%';sp.appendChild(band);hero.appendChild(sp);
  hero.appendChild(el('p','note','The marked band is the 95% range for the true '+P.toLowerCase()+' chance in games like this: '+Math.round(i95.low*100)+'% to '+Math.round(i95.high*100)+'%.'));
  box.appendChild(hero);
  below(box,r,'Start from an average game ('+Math.round(r.baseline*100)+'% '+P.toLowerCase()+'). Each row shows how many percentage points that input, on its own, moves the win chance for the '+P.toLowerCase()+' team.');
  $('miniVal').textContent=P+' '+pc+'%';
}
function render(r){
  ran=true;$('p-pred').classList.remove('stale');
  if(r.kind==='probability')return renderProb(r);
  const u=meta.target.unit||'',box=$('result');box.replaceChildren();
  const hero=el('div','card hero');hero.appendChild(el('p','lab','Expected '+meta.target.label.toLowerCase()));
  const big=el('div','big',n1(r.prediction));big.appendChild(el('small',null,u));hero.appendChild(big);
  const i80=r.intervals['80'],i95=r.intervals['95'];
  let a=Math.min(i95.low,r.floor??i95.low),b=i95.high;
  if(r.compare){a=Math.min(a,r.compare.line);b=Math.max(b,r.compare.line)}
  const pad=(b-a)*0.06;a-=pad;b+=pad;const pos=v=>((v-a)/(b-a)*100)+'%',wid=(x,y)=>((y-x)/(b-a)*100)+'%';
  const g=el('div','rng');g.appendChild(el('div','trk'));
  const b95=el('div','b95');b95.style.left=pos(i95.low);b95.style.width=wid(i95.low,i95.high);g.appendChild(b95);
  const b80=el('div','b80');b80.style.left=pos(i80.low);b80.style.width=wid(i80.low,i80.high);g.appendChild(b80);
  if(r.floor!=null){const t=el('div','tick');t.style.left=pos(r.floor);g.appendChild(t)}
  if(r.compare){const t=el('div','tick ln');t.style.left=pos(r.compare.line);g.appendChild(t)}
  const pt=el('div','pt');pt.style.left=pos(r.prediction);g.appendChild(pt);hero.appendChild(g);
  const ends=el('div','ends');ends.appendChild(el('span',null,n0(a)));ends.appendChild(el('span',null,n0(b)));hero.appendChild(ends);
  const lg=el('div','legend');
  const item=(color,title,text,dashed)=>{const d=el('div'),s=el('span');const sw=el('i','sw');
    if(dashed){sw.style.width='0';sw.style.borderLeft='2px dashed '+color;sw.style.height='12px';sw.style.borderRadius='0'}else sw.style.background=color;
    s.appendChild(sw);s.appendChild(document.createTextNode(title));d.appendChild(s);d.appendChild(document.createTextNode(text));lg.appendChild(d)};
  item('rgba(88,166,255,.75)','Likely range (80%)',n0(i80.low)+' to '+n0(i80.high)+' '+u);
  item('rgba(88,166,255,.3)','Almost certain (95%)',n0(i95.low)+' to '+n0(i95.high)+' '+u);
  if(r.floor!=null)item('#8b949e',meta.floor.label.replace(/^./,c=>c.toUpperCase()),n1(r.floor)+' '+u,true);
  if(r.compare)item('#d29922','Line you entered',n1(r.compare.line)+' '+u,true);
  hero.appendChild(lg);
  if(r.compare){const c=r.compare,l=el('div','lean');
    l.textContent=Math.abs(c.gap)<1.5?'Right on the line. No real lean either way ('+Math.round(c.p_over*100)+'% chance of going over).'
      :'Model leans '+c.lean.toUpperCase()+' by '+n1(Math.abs(c.gap))+' '+u+'. About '+Math.round(c.p_over*100)+'% chance of going over.';
    hero.appendChild(l)}
  box.appendChild(hero);
  below(box,r,'Start from an average game ('+n1(r.baseline)+' '+u+'). Each row shows how many points your input adds or removes.');
  $('miniVal').textContent=n1(r.prediction)+' '+u;
}
async function run(user){
  const btn=$('dyno');btn.disabled=true;btn.textContent='Running';
  try{
    const body={inputs:vals};const lv=lineInput?parseFloat(lineInput.value):NaN;if(!isNaN(lv))body.line=lv;
    const r=await fetch('/api/models/'+SLUG+'/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const j=await r.json();if(!r.ok)throw new Error(typeof j.detail==='string'?j.detail:'check the inputs and try again');render(j);
    if(user){tab('pred');if(!matchMedia('(min-width:980px)').matches)$('out').scrollIntoView({behavior:'smooth',block:'start'})}
  }catch(e){$('result').replaceChildren(el('p','empty','The model did not run: '+e.message+'. Press Dyno to try again.'));if(user)tab('pred')}
  btn.disabled=false;btn.textContent='Dyno';
}
fetch('/api/models/'+SLUG).then(r=>r.ok?r.json():Promise.reject()).then(m=>{meta=m;build();
  $('dyno').onclick=()=>run(true);
  $('mini').onclick=()=>{tab('pred');$('out').scrollIntoView({behavior:'smooth',block:'start'})};
  $('reset').onclick=()=>{meta.features.forEach(f=>ctl[f.name](f.default));if(lineInput)lineInput.value='';run(false)};
  run(false);
}).catch(()=>{$('result').replaceChildren(el('p','empty','Could not load this model. Refresh to try again.'))});
</script></body></html>"""

NCR = HEAD.replace("__TITLE__", "NCR Classifier · ddyno") + """
<header class="top"><a class="brand" href="/"><i></i>ddyno</a><span class="crumb">Manufacturing</span></header>
<div class="wrap" style="max-width:820px">
<div class="mhead"><p class="eyebrow">Manufacturing</p><h1 class="title">NCR Classifier</h1>
<p class="lede">Paste a non-conformance description and get the likely flaw category. Demo model: TF-IDF and logistic regression trained on a small synthetic set.</p></div>
<label class="sech" for="t">Description</label>
<textarea id="t" placeholder="For example: bore diameter oversize after final grind"></textarea>
<div style="display:flex;gap:12px;margin:14px 0 26px"><button class="btn" id="go" type="button">Classify</button></div>
<div id="out"></div>
<div class="sech" style="margin-top:26px"><span>Try an example</span></div>
<div class="rows" id="ex"></div>
</div>
<script>
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const ex=["scratches on sealing surface","missing washer during final assembly","calibration sticker expired on gauge","porosity found in casting"];
const t=document.getElementById('t'),out=document.getElementById('out'),go=document.getElementById('go');
ex.forEach(s=>{const b=el('button','ex',s);b.type='button';b.onclick=()=>{t.value=s;run()};document.getElementById('ex').appendChild(b)});
async function run(){
  if(t.value.trim().length<3){out.replaceChildren(el('p','note','Enter at least a few words to classify.'));return}
  go.disabled=true;go.textContent='Classifying';
  try{
    const r=await fetch('/api/classify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t.value})});
    if(!r.ok)throw new Error(r.status);
    const {predictions}=await r.json();const card=el('div','card blk');card.appendChild(el('h3',null,'Most likely categories'));
    predictions.forEach((p,i)=>{const d=el('div','rank'+(i?'':' me'));d.style.gridTemplateColumns='minmax(0,1fr) minmax(72px,1fr) auto';d.appendChild(el('span',null,p.label));
      const tr=el('div','tr'),b=el('i');b.style.width=(p.score*100)+'%';tr.appendChild(b);d.appendChild(tr);d.appendChild(el('b',null,(p.score*100).toFixed(1)+'%'));card.appendChild(d)});
    out.replaceChildren(card);
  }catch(e){out.replaceChildren(el('p','note','Could not classify that text. Try again.'))}
  go.disabled=false;go.textContent='Classify';
}
go.onclick=run;
</script></body></html>"""
