from __future__ import print_function
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from utils.util import get_project_root
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
BASE_DIR = get_project_root()
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

def gmail_authenticate():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("♻️  Gmail token 갱신 완료")
        else:
            print("🌐 최초 인증 중... (브라우저 창 열림)")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
            print(f"💾 토큰 저장 완료 → {TOKEN_PATH}")

    return creds

from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import markdown

def send_markdown_as_html(md_content: str, to: str, title: str):
    """Markdown 문자열을 HTML로 렌더링해서 Gmail 본문으로 전송"""
    html_content = markdown.markdown(md_content, extensions=["extra", "tables", "fenced_code"])

    creds = gmail_authenticate()
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(html_content, "html", "utf-8")
    message["to"] = to
    message["subject"] = title

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw}
    send = service.users().messages().send(userId="me", body=body).execute()

    print(f"✅ HTML 본문 메일 전송 완료! ID: {send['id']}")