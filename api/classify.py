# -*- coding: utf-8 -*-
"""Gemini 분류 — Vercel 서버 함수. 열쇠를 숨기려고 여기에 있다.

  받는 것   {"texts": ["가린 문장", ... 최대 10개], "criteria": {...criteria.json...}}
  주는 것   {"results": [{"category", "urgency", "reason"} 또는 null, ...], "model": "..."}
            열쇠가 없거나 실패하면 {"results": null, "reason": "..."} — 화면은 규칙으로 계속 돈다.

문장은 브라우저에서 이미 가린 채로 온다(mask.js). 열쇠는 환경 변수 GEMINI_API_KEY 에서만 읽는다.
파이썬 표준 라이브러리만 쓴다.
"""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

MODEL = os.environ.get("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT = 60
MAX_TEXTS = 10   # 한 번에 받는 문장 수 — 주소가 퍼졌을 때 한도가 새는 것을 줄인다
MAX_LEN = 500    # 문장당 글자 수

URGS = ["높음", "보통", "낮음"]


def build_prompt(texts, crit):
    cats = "\n".join(f"  - {c['name']}: {c['definition']}" for c in crit.get("categories", []))
    order = " > ".join(crit.get("priority", []))
    lines = "\n".join(f"{i}: {t}" for i, t in enumerate(texts))
    return f"""너는 학교에서 식재료 납품 센터로 온 문의를 분류하는 담당자다. 아래 기준을 그대로 따른다. 기준에 없는 판단을 더하지 않는다.

[칸 — 하나만 고른다]
{cats}
  여러 칸에 걸치면 이 순서로 먼저 고른다: {order}
  이유: {crit.get('priority_reason', '')}

[긴급도 — 높음 · 보통 · 낮음]
  {crit.get('urgency', {}).get('guide', '')}

[] 안의 말(예: [이름], [전화번호], [학교])은 가린 개인정보다. 추측하지 않는다.

문장마다 아래 모양의 JSON 배열 하나로만 답한다. 설명을 덧붙이지 않는다.
[{{"i": 0, "category": "...", "urgency": "...", "reason": "왜 그렇게 골랐는지 한 문장"}}]

[문장]
{lines}
"""


def call_gemini(key, prompt):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT.format(model=MODEL), data=body, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = json.loads(r.read().decode("utf-8"))
    return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])


def clean(items, n, cats):
    """기준 안의 값만 받는다. 기준 밖의 값이나 빠진 문장은 null 로 둔다."""
    out = [None] * n
    for it in items if isinstance(items, list) else []:
        try:
            i = int(it.get("i"))
        except (TypeError, ValueError, AttributeError):
            continue
        if 0 <= i < n and it.get("category") in cats and it.get("urgency") in URGS:
            out[i] = {"category": it["category"], "urgency": it["urgency"],
                      "reason": str(it.get("reason", ""))[:200]}
    return out


class handler(BaseHTTPRequestHandler):
    def _send(self, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            return self._send({"results": None, "reason": "열쇠가 없습니다 — Vercel 환경 변수 GEMINI_API_KEY"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(min(n, 60000)).decode("utf-8"))
            texts = [str(t)[:MAX_LEN] for t in req.get("texts", [])][:MAX_TEXTS]
            crit = req.get("criteria") or {}
            cats = [c.get("name") for c in crit.get("categories", []) if isinstance(c, dict)]
            if not texts or not cats:
                return self._send({"results": None, "reason": "보낸 문장이나 기준이 없습니다"})
            items = call_gemini(key, build_prompt(texts, crit))
            return self._send({"results": clean(items, len(texts), cats), "model": MODEL})
        except urllib.error.HTTPError as e:
            return self._send({"results": None, "reason": f"AI 호출 실패 ({e.code}) — 모델 이름 · 한도를 확인"})
        except Exception as e:  # noqa: BLE001
            return self._send({"results": None, "reason": f"AI 호출 실패 — {type(e).__name__}"})
