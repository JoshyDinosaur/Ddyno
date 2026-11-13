from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

# Synthetic training examples: swap in real data later.
DATA = {
    "Dimensional": [
        "bore diameter out of tolerance on finished part",
        "length exceeds drawing spec by 0.02 inches",
        "flange thickness below minimum dimension",
        "hole position off from datum by 0.015",
        "outer diameter oversize after final grind",
        "wall thickness under tolerance at section B",
    ],
    "Surface Finish": [
        "scratches visible on sealing surface",
        "surface roughness exceeds Ra requirement",
        "machining chatter marks on housing face",
        "pitting and corrosion spots on exterior",
        "burrs left on edge after deburr operation",
        "tool marks on bearing journal",
    ],
    "Material": [
        "hardness test below specified range",
        "wrong alloy certificate received from supplier",
        "inclusions found in forging cross section",
        "material lot missing traceability documentation",
        "porosity detected in casting during x-ray",
        "tensile strength failed supplier cert check",
    ],
    "Assembly": [
        "fastener torque not within specification",
        "missing washer during final assembly",
        "o-ring installed twisted in groove",
        "wrong part number installed at station 4",
        "connector not fully seated on harness",
        "gasket misaligned causing leak at joint",
    ],
    "Documentation": [
        "operator signature missing on traveler",
        "inspection record incomplete for lot",
        "revision level mismatch between drawing and work order",
        "calibration sticker expired on gauge used",
        "cert of conformance not attached to shipment",
        "incorrect serial number recorded in log",
    ],
}







def train():
    X, y = [], []
    for label, texts in DATA.items():
        for t in texts:
            X.append(t)
            y.append(label)
    pipe = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
        LogisticRegression(max_iter=1000, C=10),
    )
    pipe.fit(X, y)
    return pipe


MODEL = train()


def classify(text: str, k: int = 3):
    probs = MODEL.predict_proba([text])[0]
    ranked = sorted(zip(MODEL.classes_, probs), key=lambda p: -p[1])[:k]
    return [{"label": l, "score": round(float(s), 4)} for l, s in ranked]


INDEX = '<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>ddyno · ML-powered apps</title><style>:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--fg:#e6edf3;--mute:#8b949e;--acc:#58a6ff}\n*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}\nmain{max-width:760px;margin:0 auto;padding:48px 20px}\nh1{font-size:2.2rem;margin:0 0 4px}p.sub{color:var(--mute);margin:0 0 32px}\n.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}\n.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;text-decoration:none;color:inherit;display:block}\na.card:hover{border-color:var(--acc)}.card h3{margin:0 0 6px}.card p{margin:0;color:var(--mute);font-size:.95rem}\n.soon{opacity:.5}textarea{width:100%;min-height:110px;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit}\nbutton{background:var(--acc);color:#04111f;border:0;border-radius:8px;padding:10px 18px;font-weight:600;cursor:pointer;margin-top:10px}\nbutton:disabled{opacity:.6}.bar{background:#21262d;border-radius:6px;height:10px;overflow:hidden}.bar i{display:block;height:100%;background:var(--acc)}\n.row{margin:14px 0}.row b{display:flex;justify-content:space-between}.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}\n.chip{background:#21262d;border:1px solid var(--line);color:var(--mute);border-radius:99px;padding:4px 12px;font-size:.85rem;cursor:pointer}\na.back{color:var(--mute);text-decoration:none;font-size:.9rem}\n</style></head>\n<body><main>\n<h1>ddyno</h1><p class="sub">Small ML-powered apps. Built in the open, iterated fast.</p>\n<div class="grid">\n<a class="card" href="/apps/ncr"><h3>NCR Classifier</h3><p>Paste a manufacturing non-conformance description and get the likely flaw category.</p></a>\n<div class="card soon"><h3>NFL Game Modeling</h3><p>Pre-game win probabilities. Coming soon.</p></div>\n</div></main></body></html>\n'
NCR = '<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>NCR Classifier · ddyno</title><style>:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--fg:#e6edf3;--mute:#8b949e;--acc:#58a6ff}\n*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}\nmain{max-width:760px;margin:0 auto;padding:48px 20px}\nh1{font-size:2.2rem;margin:0 0 4px}p.sub{color:var(--mute);margin:0 0 32px}\n.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}\n.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;text-decoration:none;color:inherit;display:block}\na.card:hover{border-color:var(--acc)}.card h3{margin:0 0 6px}.card p{margin:0;color:var(--mute);font-size:.95rem}\n.soon{opacity:.5}textarea{width:100%;min-height:110px;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit}\nbutton{background:var(--acc);color:#04111f;border:0;border-radius:8px;padding:10px 18px;font-weight:600;cursor:pointer;margin-top:10px}\nbutton:disabled{opacity:.6}.bar{background:#21262d;border-radius:6px;height:10px;overflow:hidden}.bar i{display:block;height:100%;background:var(--acc)}\n.row{margin:14px 0}.row b{display:flex;justify-content:space-between}.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}\n.chip{background:#21262d;border:1px solid var(--line);color:var(--mute);border-radius:99px;padding:4px 12px;font-size:.85rem;cursor:pointer}\na.back{color:var(--mute);text-decoration:none;font-size:.9rem}\n</style></head>\n<body><main>\n<a class="back" href="/">← ddyno</a>\n<h1>NCR Classifier</h1><p class="sub">TF-IDF + logistic regression trained on a small synthetic set. Demo model, swap in real data to iterate.</p>\n<textarea id="t" placeholder="e.g. bore diameter oversize after final grind"></textarea>\n<div class="chips" id="ex"></div>\n<button id="go">Classify</button>\n<div id="out"></div>\n<script>\nconst ex=["scratches on sealing surface","missing washer during final assembly","calibration sticker expired on gauge","porosity found in casting"];\nconst t=document.getElementById(\'t\'),out=document.getElementById(\'out\'),go=document.getElementById(\'go\');\nex.forEach(s=>{const c=document.createElement(\'span\');c.className=\'chip\';c.textContent=s;c.onclick=()=>{t.value=s;run()};document.getElementById(\'ex\').appendChild(c)});\nasync function run(){\n  if(t.value.trim().length<3)return;go.disabled=true;\n  try{\n    const r=await fetch(\'/api/classify\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({text:t.value})});\n    if(!r.ok)throw new Error(r.status);\n    const {predictions}=await r.json();\n    out.innerHTML=predictions.map(p=>`<div class="row"><b><span>${p.label}</span><span>${(p.score*100).toFixed(1)}%</span></b><div class="bar"><i style="width:${p.score*100}%"></i></div></div>`).join(\'\');\n  }catch(e){out.textContent=\'Error: \'+e.message}\n  go.disabled=false;\n}\ngo.onclick=run;\n</script></main></body></html>\n'

app = FastAPI(title="ddyno")


class ClassifyIn(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/classify")
def api_classify(body: ClassifyIn):
    return {"predictions": classify(body.text)}


@app.get("/apps/ncr", response_class=HTMLResponse)
def ncr_page():
    return NCR


@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX
