from __future__ import annotations
import os
import json
from typing import Dict, List, Any, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file",
]

# -------------------------------------------------
# Auth & service
# -------------------------------------------------
def get_slides_service(
    credentials_path: str = "credentials.json",
    token_path: str = "token.json",
):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("slides", "v1", credentials=creds)


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _px(pt: float) -> dict:
    return {"magnitude": pt, "unit": "PT"}

def _create_slide(page_id: str | None = None) -> dict:
    return {
        "createSlide": {
            **({"objectId": page_id} if page_id else {}),
            "slideLayoutReference": {"predefinedLayout": "BLANK"}
        }
    }

def _create_textbox(page_id: str, object_id: str, x: float, y: float, w: float, h: float) -> dict:
    return {
        "createShape": {
            "objectId": object_id,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {"width": _px(w), "height": _px(h)},
                "transform": {
                    "scaleX": 1, "scaleY": 1,
                    "translateX": x, "translateY": y,
                    "unit": "PT",
                },
            },
        }
    }

def _insert_text(object_id: str, text: str, cell_location: Optional[dict] = None) -> dict:
    req = {"insertText": {"objectId": object_id, "text": text}}
    if cell_location:
        req["insertText"]["cellLocation"] = cell_location
    return req

def _text_style_all(object_id: str, **style) -> dict:
    # style e.g. bold=True, fontSize={"magnitude": 24, "unit":"PT"}
    return {
        "updateTextStyle": {
            "objectId": object_id,
            "style": style,
            "textRange": {"type": "ALL"},
            "fields": ",".join(style.keys()),
        }
    }

def _para_style_all(object_id: str, **style) -> dict:
    # style e.g. lineSpacing=110
    return {
        "updateParagraphStyle": {
            "objectId": object_id,
            "style": style,
            "textRange": {"type": "ALL"},
            "fields": ",".join(style.keys()),
        }
    }

def _make_bullets(object_id: str) -> dict:
    return {
        "createParagraphBullets": {
            "objectId": object_id,
            "textRange": {"type": "ALL"},
            "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
        }
    }

def _create_table(page_id: str, object_id: str, rows: int, cols: int,
                  x: float, y: float, w: float, h: float) -> dict:
    return {
        "createTable": {
            "objectId": object_id,
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {"width": _px(w), "height": _px(h)},
                "transform": {
                    "scaleX": 1, "scaleY": 1,
                    "translateX": x, "translateY": y,
                    "unit": "PT",
                },
            },
            "rows": rows,
            "columns": cols,
        }
    }

def _safe_join_lines(lines: List[str]) -> str:
    # 불릿용 문자열
    return "\n".join([l if l is not None else "" for l in lines])

def _title_with_part(title: str, part: Optional[int]) -> str:
    if part and part > 1:
        return f"{title} (part {part})"
    return title

# -------------------------------------------------
# Slide renderers
# -------------------------------------------------
def _render_bluf(slides, presentation_id: str, page_id: str, slide: dict):
    reqs = []
    # Heading
    head_id = f"{page_id}_heading"
    reqs.append(_create_textbox(page_id, head_id, x=40, y=40, w=800, h=60))
    reqs.append(_insert_text(head_id, slide.get("heading", "Executive Summary")))
    reqs.append(_text_style_all(head_id, bold=True, fontSize=_px(28)))
    reqs.append(_para_style_all(head_id, lineSpacing=110))

    # Bullets
    bullets_id = f"{page_id}_bullets"
    bullets = slide.get("bullets", [])
    reqs.append(_create_textbox(page_id, bullets_id, x=40, y=120, w=840, h=380))
    reqs.append(_insert_text(bullets_id, _safe_join_lines(bullets)))
    reqs.append(_make_bullets(bullets_id))
    reqs.append(_text_style_all(bullets_id, fontSize=_px(16)))
    reqs.append(_para_style_all(bullets_id, lineSpacing=115))

    return reqs

def _render_title(slides, presentation_id: str, page_id: str, slide: dict):
    reqs = []
    title_id = f"{page_id}_title"
    sub_id = f"{page_id}_subtitle"
    reqs.append(_create_textbox(page_id, title_id, x=80, y=180, w=760, h=80))
    reqs.append(_insert_text(title_id, slide.get("heading", "")))
    reqs.append(_text_style_all(title_id, bold=True, fontSize=_px(36)))
    reqs.append(_create_textbox(page_id, sub_id, x=80, y=260, w=760, h=60))
    reqs.append(_insert_text(sub_id, slide.get("subheading", "")))
    reqs.append(_text_style_all(sub_id, fontSize=_px(20)))
    return reqs

def _render_text(slides, presentation_id: str, page_id: str, slide: dict):
    reqs = []
    # Title
    title_id = f"{page_id}_title"
    reqs.append(_create_textbox(page_id, title_id, x=40, y=30, w=840, h=50))
    reqs.append(_insert_text(title_id, _title_with_part(slide.get("title",""), slide.get("part"))))
    reqs.append(_text_style_all(title_id, bold=True, fontSize=_px(24)))

    # Lead (optional)
    y_cursor = 90
    if slide.get("lead"):
        lead_id = f"{page_id}_lead"
        reqs.append(_create_textbox(page_id, lead_id, x=40, y=y_cursor, w=840, h=60))
        reqs.append(_insert_text(lead_id, slide["lead"]))
        reqs.append(_text_style_all(lead_id, bold=False, fontSize=_px(16)))
        reqs.append(_para_style_all(lead_id, lineSpacing=115))
        y_cursor += 70

    # Groups
    groups: List[dict] = slide.get("groups", [])
    box_height = 120  # 한 그룹당 높이
    for idx, g in enumerate(groups):
        label = g.get("label", "기타")
        items = g.get("items", [])
        sources = g.get("sources", [])

        # label
        lid = f"{page_id}_g{idx}_label"
        reqs.append(_create_textbox(page_id, lid, x=40, y=y_cursor, w=840, h=24))
        reqs.append(_insert_text(lid, label))
        reqs.append(_text_style_all(lid, bold=True, fontSize=_px(16)))

        # items (bullets)
        bid = f"{page_id}_g{idx}_bullets"
        reqs.append(_create_textbox(page_id, bid, x=60, y=y_cursor+26, w=820, h=box_height-26-18))
        if items:
            reqs.append(_insert_text(bid, _safe_join_lines(items)))
            reqs.append(_make_bullets(bid))
        else:
            reqs.append(_insert_text(bid, "-"))
            reqs.append(_make_bullets(bid))
        reqs.append(_text_style_all(bid, fontSize=_px(14)))
        reqs.append(_para_style_all(bid, lineSpacing=115))

        # sources (small text under group)
        if sources:
            sid = f"{page_id}_g{idx}_src"
            reqs.append(_create_textbox(page_id, sid, x=60, y=y_cursor+box_height-18, w=820, h=16))
            reqs.append(_insert_text(sid, "출처: " + " | ".join(sources)))
            reqs.append(_text_style_all(sid, fontSize=_px(10)))

        y_cursor += box_height

    # slide-level sources
    slide_sources = slide.get("sources", [])
    if slide_sources:
        sid = f"{page_id}_slide_src"
        reqs.append(_create_textbox(page_id, sid, x=40, y=500, w=840, h=16))
        reqs.append(_insert_text(sid, "출처: " + " | ".join(slide_sources)))
        reqs.append(_text_style_all(sid, fontSize=_px(10)))

    return reqs

def _render_table(slides, presentation_id: str, page_id: str, slide: dict):
    reqs = []
    # Title
    title_id = f"{page_id}_title"
    reqs.append(_create_textbox(page_id, title_id, x=40, y=30, w=840, h=50))
    reqs.append(_insert_text(title_id, slide.get("title", "")))
    reqs.append(_text_style_all(title_id, bold=True, fontSize=_px(24)))

    # Table
    columns: List[str] = slide.get("columns", [])
    rows: List[List[str]] = slide.get("rows", [])
    total_rows = 1 + len(rows)
    total_cols = len(columns)

    table_id = f"{page_id}_table"
    reqs.append(_create_table(page_id, table_id, rows=total_rows, cols=total_cols,
                              x=40, y=100, w=840, h=360))

    # Header row
    for c, text in enumerate(columns):
        reqs.append(_insert_text(
            table_id, str(text),
            cell_location={"rowIndex": 0, "columnIndex": c}
        ))

    # Data rows
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, cell in enumerate(row):
            reqs.append(_insert_text(
                table_id, "" if cell is None else str(cell),
                cell_location={"rowIndex": r_idx, "columnIndex": c_idx}
            ))

    # Sources
    slide_sources = slide.get("sources", [])
    if slide_sources:
        sid = f"{page_id}_slide_src"
        reqs.append(_create_textbox(page_id, sid, x=40, y=470, w=840, h=16))
        reqs.append(_insert_text(sid, "출처: " + " | ".join(slide_sources)))
        reqs.append(_text_style_all(sid, fontSize=_px(10)))

    return reqs


from utils.util import get_project_root
import uuid
def _new_id(prefix: str, idx: int | None = None) -> str:
    """Slides objectId 규격(5~50자) 만족 & 충돌 최소화"""
    base = f"{prefix}_{idx:04d}_" if idx is not None else f"{prefix}_"
    suf = uuid.uuid4().hex[:8]
    oid = f"{base}{suf}"
    # 5~50자 사이로 잘라주기
    return oid[:50] if len(oid) > 50 else oid

def render_slice_plan(slice_plan: Dict[str, Any],
                      credentials_path: str = str(get_project_root() / "credentials.json"),
                      token_path: str = str(get_project_root() / "token.json")) -> dict:
    """
    slice_plan(dict) → Google Slides
    return: {"presentationId": ..., "url": ...}
    """
    svc = get_slides_service(credentials_path, token_path)
    meta = slice_plan.get("meta", {})
    title = meta.get("title") or "<제목 없음>"

    pres = svc.presentations().create(body={"title": title}).execute()
    pres_id = pres["presentationId"]

    # 첫 슬라이드는 기본 생성됨. 우리는 전부 BLANK를 쓰므로 기본 슬라이드는 버리고 새로 만든 뒤 삭제해도 됨.
    # 여기서는 그냥 추가만 하고 마지막에 기본 슬라이드 삭제(선택) 가능.
    requests: List[dict] = []
    auto_delete_first_slide = True

    pages_to_delete: List[str] = []
    if auto_delete_first_slide and pres.get("slides"):
        pages_to_delete.append(pres["slides"][0]["objectId"])

    # Build requests
    for idx, slide in enumerate(slice_plan.get("slides", [])):
        page_id = _new_id("page", idx+1) 
        requests.append(_create_slide(page_id))

        t = slide.get("type")
        if t == "bluf":
            requests += _render_bluf(svc, pres_id, page_id, slide)
        elif t == "title":
            requests += _render_title(svc, pres_id, page_id, slide)
        elif t == "text":
            requests += _render_text(svc, pres_id, page_id, slide)
        elif t == "table":
            requests += _render_table(svc, pres_id, page_id, slide)
        else:
            # 미지원 타입은 빈 텍스트 슬라이드로 대체
            requests += _render_text(svc, pres_id, page_id, {
                "title": f"Unsupported type: {t}",
                "groups": [{"label": "원본", "items": [json.dumps(slide, ensure_ascii=False)]}],
            })

    # 삭제(선택)
    for pid in pages_to_delete:
        requests.append({"deleteObject": {"objectId": pid}})

    # Commit
    if requests:
        svc.presentations().batchUpdate(
            presentationId=pres_id,
            body={"requests": requests}
        ).execute()

    url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
    return {"presentationId": pres_id, "url": url}