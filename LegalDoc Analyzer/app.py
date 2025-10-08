import re, json
import fitz
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import traceback

app = FastAPI(title="Contract ML Service", version="0.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# ---------------- Models ----------------
class ClauseOut(BaseModel):
    type: str
    text: str
    facts: Dict[str, Any]
    explanation_simple: str
    key_facts: List[str]
    risk_flags: List[str]

class AnalysisOut(BaseModel):
    contract_summary: str
    clauses: List[ClauseOut]
    missing_clauses: List[str]

# ---------------- Clause patterns -------------__
CLAUSE_PATTERNS = {
    "Limitation of Liability": r"\bliabilit(y|ies)|responsibilit(y|ies)|not exceed|cap|maximum\b",
    "Termination": r"\bterminat(e|ion)|expire|notice|cure period|without cause\b",
    "Confidentiality": r"\bconfidential|non[- ]disclosure|NDA|trade secret|proprietary\b",
    "Governing Law": r"\bgoverning law|jurisdiction|venue|court|arbitration\b",
    "Payment": r"\bfee|invoice|payment|due date|late fee|tax(es)?\b",
    "IP": r"\bintellectual property|license|ownership|work made for hire|IP\b",
    "Indemnity": r"\bindemnif(y|ication)|hold harmless|defend\b",
    "Force Majeure": r"\bforce majeure|beyond (its|their) control\b",
    "Notices": r"\bnotices?|in writing|registered mail|email address\b",
}

MUST_HAVE = {"Limitation of Liability","Termination","Confidentiality","Governing Law","Payment","Indemnity"}

# ---------------- Functions ----------------
def extract_text_blocks(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks = []
    for i in range(len(doc)):
        page = doc[i]
        for b in page.get_text("blocks"):
            text = b[4] if len(b) > 4 and b[4] is not None else ""
            if text.strip():
                blocks.append({"page": i+1, "text": text})
    return blocks

def segment_clauses(text_blocks):
    full = "\n".join(b["text"] for b in text_blocks if b["text"])
    if not full.strip():
        return []  # no text found
    # Split by headings, numbering, or two newlines
    parts = re.split(r"(?mi)^(?:section|clause)?\s*\d+(\.\d+)*\s*[:.)-]?\s+|[\n]{2,}", full)
    # Filter out None or empty strings
    return [p.strip() for p in parts if p and p.strip() and len(p.strip()) > 50]

def classify_clause(text: str) -> str:
    for label, pat in CLAUSE_PATTERNS.items():
        if re.search(pat, text, flags=re.I | re.M):
            return label
    return "Other"

def extract_facts(text: str) -> Dict[str, Any]:
    facts = {}
    amounts = re.findall(r"(?:USD|INR|Rs\.?|₹)?\s?\$?\s?[\d,]+(?:\.\d{1,2})?", text)
    if amounts: facts["amounts"] = amounts
    dur = re.findall(r"\b\d{1,3}\s*(day|days|month|months|year|years)\b", text, re.I)
    if dur: facts["durations"] = dur
    m = re.search(r"governing law (?:of|in) ([A-Za-z ]+)", text, re.I)
    if m: facts["governing_law"] = m.group(1).strip()
    if re.search(r"not exceed|maximum|cap(ped)?\b", text, re.I): facts["has_cap"] = True
    return facts

def simple_explain(ctype: str, facts: Dict[str, Any]) -> str:
    return f"This clause is about {ctype.lower()}. It explains obligations or limits in simple terms."

def risk_flags(ctype: str, text: str, facts: Dict[str, Any]) -> List[str]:
    flags = []
    if ctype=="Limitation of Liability" and not facts.get("has_cap"): flags.append("No clear liability cap found.")
    if ctype=="Payment" and re.search(r"\b45\s*days|60\s*days\b", text, re.I): flags.append("Long payment cycle (45–60 days).")
    if ctype=="Governing Law" and not facts.get("governing_law"): flags.append("Governing law missing.")
    if ctype=="Indemnity" and re.search(r"any and all claims", text, re.I): flags.append("Indemnity is broad.")
    if re.search(r"auto-?renew|renew.*unless.*notice", text, re.I): flags.append("Auto-renewal clause present.")
    return flags

def analyze_pdf(pdf_bytes: bytes) -> AnalysisOut:
    blocks = extract_text_blocks(pdf_bytes)
    clauses_raw = segment_clauses(blocks)
    clauses = []
    for c in clauses_raw:
        ctype = classify_clause(c)
        facts = extract_facts(c)
        clauses.append(ClauseOut(
            type=ctype,
            text=c,
            facts=facts,
            explanation_simple=simple_explain(ctype, facts),
            key_facts=[f"{k}: {v}" for k,v in facts.items()],
            risk_flags=risk_flags(ctype,c,facts)
        ))
    types_present = {c.type for c in clauses}
    missing = sorted(list(MUST_HAVE - types_present))
    return AnalysisOut(contract_summary="Automated contract overview.", clauses=clauses, missing_clauses=missing)

# ---------------- Routes ----------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html><body>
    <h2>Upload Contract PDF</h2>
    <form action="/analyze" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept="application/pdf"/>
        <input type="submit" value="Analyze"/>
    </form>
    </body></html>
    """

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        result = analyze_pdf(pdf_bytes)

        clauses_html = ""
        for c in result.clauses:
            clauses_html += f"<div style='margin-bottom:15px; padding:8px; border:1px solid #ccc;'>"
            clauses_html += f"<b>Type:</b> {c.type}<br>"
            clauses_html += f"<b>Text:</b> {c.text[:500]}...<br>"
            clauses_html += f"<b>Facts:</b> {json.dumps(c.facts)}<br>"
            clauses_html += f"<b>Explanation:</b> {c.explanation_simple}<br>"
            clauses_html += f"<b>Risk Flags:</b> {c.risk_flags}<br></div>"

        missing_html = "<br>".join(result.missing_clauses) if result.missing_clauses else "None"

        return f"""
        <html><body>
        <h2>Analysis Result</h2>
        <p><b>Summary:</b> {result.contract_summary}</p>
        <h3>Clauses:</h3>{clauses_html}
        <h3>Missing Must-Have Clauses:</h3>{missing_html}
        <br><a href="/">Analyze Another PDF</a>
        </body></html>
        """
    except Exception as e:
        tb = traceback.format_exc()
        return f"""
        <html><body>
        <h2>Internal Error Occurred</h2>
        <pre>{tb}</pre>
        <br><a href="/">Try Again</a>
        </body></html>
        """
