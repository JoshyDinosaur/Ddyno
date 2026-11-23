"""Standalone app: NCR Manufacturing Text Classifier (/apps/ncr, /api/classify)."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

import ui

NCR_DATA = {
    "Dimensional": ["bore diameter out of tolerance on finished part", "length exceeds drawing spec by 0.02 inches",
                    "flange thickness below minimum dimension", "hole position off from datum by 0.015",
                    "outer diameter oversize after final grind", "wall thickness under tolerance at section B"],
    "Surface Finish": ["scratches visible on sealing surface", "surface roughness exceeds Ra requirement",
                       "machining chatter marks on housing face", "pitting and corrosion spots on exterior",
                       "burrs left on edge after deburr operation", "tool marks on bearing journal"],
    "Material": ["hardness test below specified range", "wrong alloy certificate received from supplier",
                 "inclusions found in forging cross section", "material lot missing traceability documentation",
                 "porosity detected in casting during x-ray", "tensile strength failed supplier cert check"],
    "Assembly": ["fastener torque not within specification", "missing washer during final assembly",
                 "o-ring installed twisted in groove", "wrong part number installed at station 4",
                 "connector not fully seated on harness", "gasket misaligned causing leak at joint"],
    "Documentation": ["operator signature missing on traveler", "inspection record incomplete for lot",
                      "revision level mismatch between drawing and work order", "calibration sticker expired on gauge used",
                      "cert of conformance not attached to shipment", "incorrect serial number recorded in log"],
}
NCR_MODEL = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True), LogisticRegression(max_iter=1000, C=10))
NCR_MODEL.fit([t for ts in NCR_DATA.values() for t in ts], [k for k, ts in NCR_DATA.items() for _ in ts])

router = APIRouter()


class ClassifyIn(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


@router.post("/api/classify")
def api_classify(body: ClassifyIn):
    probs = NCR_MODEL.predict_proba([body.text])[0]
    ranked = sorted(zip(NCR_MODEL.classes_, probs), key=lambda p: -p[1])[:3]
    return {"predictions": [{"label": l, "score": round(float(s), 4)} for l, s in ranked]}


@router.get("/apps/ncr", response_class=HTMLResponse)
def ncr_page():
    return ui.NCR


APP = {
    "slug": "ncr",
    "name": "NCR Classifier",
    "category": "Manufacturing",
    "url": "/apps/ncr",
    "summary": "Paste a manufacturing non-conformance description and get the likely flaw category.",
    "pill": "Demo",
    "cta": "Open demo",
    "nav": False,
    "order": 20,
    "hosts": ["ncr.ddyno.com"],
    "router": router,
}
