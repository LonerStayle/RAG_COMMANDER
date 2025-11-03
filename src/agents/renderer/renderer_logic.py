from __future__ import annotations
import os
import uuid
from typing import Dict, Any, List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# -----------------------------
# 0) Google Slides OAuth
# -----------------------------
from utils.util import get_project_root
SCOPES = ["https://www.googleapis.com/auth/presentations"]
CREDENTIALS = str(get_project_root() / "credentials.json")  
TOKEN = str(get_project_root() / "token.json")  

def get_slides_service():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return build("slides", "v1", credentials=creds)

# -----------------------------
# 1) 레이아웃(PT 단위) & 스타일
# -----------------------------
PAGE_W, PAGE_H = 720, 405    # Google Slides 기본(10in x 5.625in) → 1in = 72pt
MARGIN_X = 36
TITLE_Y = 18
TITLE_H = 32
LEAD_Y = TITLE_Y + TITLE_H + 8
LEAD_H = 56

GRID_TOP = LEAD_Y + LEAD_H + 12
GRID_LEFT = MARGIN_X
GRID_RIGHT = PAGE_W - MARGIN_X
GRID_W = GRID_RIGHT - GRID_LEFT
GRID_H = PAGE_H - GRID_TOP - 20

GAP = 12
COLS, ROWS = 2, 2
CELL_W = (GRID_W - GAP) / COLS
CELL_H = (GRID_H - GAP) / ROWS

# 글꼴/색
FONT_FAMILY = "Noto Sans"
FS_TITLE = 24       # 대제목
FS_LEAD  = 18       # 리드(골드)
FS_LABEL = 14       # 소제목 라벨
FS_ITEM  = 11       # 본문 항목

COLOR_BLACK = {"red": 0, "green": 0, "blue": 0}
COLOR_GOLD  = {"red": 0.82, "green": 0.72, "blue": 0.47}  # #D1B875 유사

# -----------------------------
# 2) Slides API 헬퍼
# -----------------------------
def _rgb(color):  # API용 RGB 구조
    return {"opaqueColor": {"rgbColor": color}}

def _pt(v):       # magnitude wrapper
    return {"magnitude": float(v), "unit": "PT"}

def new_id(prefix="obj"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def create_presentation(svc, title: str) -> str:
    pres = svc.presentations().create(body={"title": title}).execute()
    return pres["presentationId"]

def add_blank_slide(svc, pres_id: str) -> str:
    requests = [{"createSlide": {"slideLayoutReference": {"predefinedLayout": "BLANK"}}}]
    res = svc.presentations().batchUpdate(presentationId=pres_id, body={"requests": requests}).execute()
    return res["replies"][0]["createSlide"]["objectId"]

def req_create_textbox(page_id: str, object_id: str, x, y, w, h):
    return {
        "createShape": {
            "objectId": object_id,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {"width": _pt(w), "height": _pt(h)},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "PT"},
            },
        }
    }

def req_insert_text(object_id: str, text: str):
    return {"insertText": {"objectId": object_id, "insertionIndex": 0, "text": text}}

def req_text_style(object_id: str, start: int, end: int, size: int, bold=False, color=None):
    style = {"fontFamily": FONT_FAMILY, "fontSize": _pt(size), "bold": bold}
    fields = "fontFamily,fontSize,bold"
    if color:
        style["foregroundColor"] = _rgb(color)
        fields += ",foregroundColor"
    return {
        "updateTextStyle": {
            "objectId": object_id,
            "textRange": {"type": "FIXED_RANGE", "startIndex": start, "endIndex": end},
            "style": style,
            "fields": fields,
        }
    }

def req_paragraph_style(object_id: str, start: int, end: int, align="START", line_spacing=115):
    return {
        "updateParagraphStyle": {
            "objectId": object_id,
            "textRange": {"type": "FIXED_RANGE", "startIndex": start, "endIndex": end},
            "style": {"alignment": align, "lineSpacing": line_spacing},
            "fields": "alignment,lineSpacing",
        }
    }

# def req_bullets(object_id: str, start: int, end: int):
#     # 하이픈(- )으로 시작하는 라인들을 실제 불릿으로 변환
#     return {
#         "createParagraphBullets": {
#             "objectId": object_id,
#             "textRange": {"type": "FIXED_RANGE", "startIndex": start, "endIndex": end},
#             "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
#         }
#     }
def safe_bullets(object_id: str, text: str):
    reqs = []
    text_len = len(text)
    # 비어 있으면 bullets 안 건다
    if text_len == 0:
        return reqs
    # 최소 1글자 이상일 때만 bullets
    reqs.append({
        "createParagraphBullets": {
            "objectId": object_id,
            "textRange": {
                "type": "FIXED_RANGE",
                "startIndex": 0,
                "endIndex": text_len
            },
            "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
        }
    })
    return reqs

# -----------------------------
# 3) 렌더링 유틸
# -----------------------------
def clamp_lines(lines: List[str], max_lines: int = 6, max_chars_per_line: int = 120) -> List[str]:
    """레이아웃 넘침 방지를 위해 줄 수와 글자 수를 대략 제한"""
    out = []
    for ln in lines:
        s = ln.strip()
        if len(s) > max_chars_per_line:
            s = s[: max_chars_per_line - 1] + "…"
        out.append(s)
        if len(out) >= max_lines:
            break
    return out

def grid_cell_xywh(col: int, row: int):
    x = GRID_LEFT + col * (CELL_W + GAP)
    y = GRID_TOP + row * (CELL_H + GAP)
    return x, y, CELL_W, CELL_H

# -----------------------------
# 4) 슬라이드 렌더링 (type="text")
# -----------------------------
def render_text_slide_requests(page_id: str, slide: Dict[str, Any]) -> List[Dict[str, Any]]:
    reqs: List[Dict[str, Any]] = []

    # -- 4.1 Title (가운데)
    title_id = new_id("title")
    title = (slide.get("title") or "").strip()
    if title and not title.endswith("\n"):
        title += "\n"
    reqs += [
        req_create_textbox(page_id, title_id, MARGIN_X, TITLE_Y, PAGE_W - 2 * MARGIN_X, TITLE_H),
        req_insert_text(title_id, title),
        req_text_style(title_id, 0, len(title), FS_TITLE, bold=True, color=COLOR_BLACK),
        req_paragraph_style(title_id, 0, len(title), align="CENTER", line_spacing=110),
    ]

    # -- 4.2 Lead (골드, 요약 인사이트)
    lead_id = new_id("lead")
    lead = (slide.get("lead") or "").strip()
    if lead and not lead.endswith("\n"):
        lead += "\n"
    reqs += [
        req_create_textbox(page_id, lead_id, MARGIN_X, LEAD_Y, PAGE_W - 2 * MARGIN_X, LEAD_H),
        req_insert_text(lead_id, lead),
        req_text_style(lead_id, 0, len(lead), FS_LEAD, bold=True, color=COLOR_GOLD),
        req_paragraph_style(lead_id, 0, len(lead), align="START", line_spacing=100),
    ]

    # -- 4.3 2x2 Grid (groups 최대 4개)
    groups = slide.get("groups") or []
    # 4개 초과면 파트 나누는 건 여기서 처리하지 않고, 호출부에서 슬라이드 분할 권장
    # (현재 입력은 각 슬라이드 정확히 4개)
    for idx, group in enumerate(groups[:4]):
        col, row = idx % 2, idx // 2
        x, y, w, h = grid_cell_xywh(col, row)

        # 라벨 박스 (상단)
        label_id = new_id("label")
        label_txt = (group.get("label") or "").strip()
        if label_txt and not label_txt.endswith("\n"):
            label_txt += "\n"
        reqs += [
            req_create_textbox(page_id, label_id, x, y, w, 26),
            req_insert_text(label_id, label_txt),
            req_text_style(label_id, 0, len(label_txt), FS_LABEL, bold=True, color=COLOR_BLACK),
            req_paragraph_style(label_id, 0, len(label_txt), align="START", line_spacing=110),
        ]

        # 아이템 박스 (라벨 아래)
        items_id = new_id("items")
        items = group.get("items") or []
        items = clamp_lines(items, max_lines=6, max_chars_per_line=110)
        items_txt = "\n".join(f"- {it}" for it in items)
        if items_txt and not items_txt.endswith("\n"):
            items_txt += "\n"
        reqs += [
            req_create_textbox(page_id, items_id, x, y + 28, w, h - 30),
            req_insert_text(items_id, items_txt),
            req_text_style(items_id, 0, len(items_txt), FS_ITEM, bold=False, color=COLOR_BLACK),
            req_paragraph_style(items_id, 0, len(items_txt), align="START", line_spacing=120),
            # req_bullets(items_id, 0, len(items_txt)),
        ]
        reqs += safe_bullets(items_id, items_txt)

    return reqs

# ----------------------------- 
# 5) 메인 렌더러
# -----------------------------
def render_sliceplan(slice_plan: Dict[str, Any]) -> Dict[str, Any]:
    """SlicePlan(JSON dict) → Google Slides 생성"""
    svc = get_slides_service()
    meta = slice_plan.get("meta", {})
    title = meta.get("title") or "Untitled Report"

    pres_id = create_presentation(svc, title)

    # slides 순회: type=="text"만 처리
    for slide in slice_plan.get("slides", []):
        if slide.get("type") != "text":
            # 필요시 'bluf'/'table' 타입 추가 처리 가능
            continue
        page_id = add_blank_slide(svc, pres_id)
        reqs = render_text_slide_requests(page_id, slide)
        if reqs:
            svc.presentations().batchUpdate(presentationId=pres_id, body={"requests": reqs}).execute()

    # 생성된 프레젠테이션 URL 반환
    url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
    return {"presentationId": pres_id, "url": url}