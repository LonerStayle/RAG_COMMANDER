"""
Housing FAQ 챗봇 Streamlit 프론트엔드
"""
import streamlit as st
import requests
import uuid
import json
from typing import Dict, Any

# 페이지 설정
st.set_page_config(
    page_title="주택 FAQ 챗봇",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API 엔드포인트 설정
API_BASE_URL = "http://localhost:8000"

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "target_area" not in st.session_state:
    st.session_state.target_area = ""
if "main_type" not in st.session_state:
    st.session_state.main_type = ""
if "total_units" not in st.session_state:
    st.session_state.total_units = ""


def send_message_streaming(
    message: str,
    target_area: str,
    main_type: str,
    total_units: str,
    use_faq: bool,
    use_rule: bool,
    use_policy: bool,
) -> tuple[str, list]:
    """스트리밍 방식으로 메시지 전송"""
    url = f"{API_BASE_URL}/chat/stream"
    payload = {
        "message": message,
        "target_area": target_area if target_area else None,
        "main_type": main_type if main_type else None,
        "total_units": total_units if total_units else None,
        "session_id": st.session_state.session_id,
        "use_faq": use_faq,
        "use_rule": use_rule,
        "use_policy": use_policy,
    }

    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        response.raise_for_status()

        full_response = ""
        sources = []

        for line in response.iter_lines():
            if line:
                line_text = line.decode("utf-8")
                if line_text.startswith("data: "):
                    data_json = line_text[6:]  # "data: " 제거
                    try:
                        chunk = json.loads(data_json)
                        if chunk["type"] == "text":
                            full_response += chunk.get("content", "")
                            yield full_response, sources
                        elif chunk["type"] == "sources":
                            sources = chunk.get("sources", [])
                        elif chunk["type"] == "session":
                            st.session_state.session_id = chunk.get("content", "")
                        elif chunk["type"] == "error":
                            st.error(f"오류: {chunk.get('error')}")
                            return
                    except json.JSONDecodeError:
                        continue

        return full_response, sources

    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 실패: {str(e)}")
        return "", []


def send_message(
    message: str,
    target_area: str,
    main_type: str,
    total_units: str,
    use_faq: bool,
    use_rule: bool,
    use_policy: bool,
) -> tuple[str, list]:
    """일반 방식으로 메시지 전송"""
    url = f"{API_BASE_URL}/chat"
    payload = {
        "message": message,
        "target_area": target_area if target_area else None,
        "main_type": main_type if main_type else None,
        "total_units": total_units if total_units else None,
        "session_id": st.session_state.session_id,
        "use_faq": use_faq,
        "use_rule": use_rule,
        "use_policy": use_policy,
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["response"], data.get("sources", [])
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 실패: {str(e)}")
        return "", []


def clear_history():
    """대화 기록 초기화"""
    try:
        url = f"{API_BASE_URL}/chat/history/{st.session_state.session_id}"
        requests.delete(url)
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.success("대화 기록이 초기화되었습니다.")
    except requests.exceptions.RequestException as e:
        st.error(f"초기화 실패: {str(e)}")


# ========== UI 구성 ==========

# 헤더
st.title("🏠 주택 FAQ 챗봇")
st.markdown("**주택 청약 및 분양에 대한 질문을 해보세요!**")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")

    # PDF 업로드 섹션
    st.subheader("📄 PDF 업로드")
    uploaded_file = st.file_uploader(
        "정책 PDF 파일 업로드",
        type=["pdf"],
        help="새로운 정책 PDF를 업로드하여 DB에 추가할 수 있습니다",
    )

    if uploaded_file is not None:
        if st.button("📤 PDF 업로드 및 DB 저장"):
            with st.spinner("PDF 업로드 중..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(f"{API_BASE_URL}/upload/pdf", files=files)

                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data['message']}")
                        with st.expander("업로드된 PDF 정보"):
                            st.write(f"**파일명:** {data['file_path']}")
                            st.write(f"**정책 날짜:** {data['policy_date']}")
                            st.write(f"**정책 유형:** {data['policy_type']}")
                            st.write(f"**제목:** {data['title']}")
                    else:
                        st.error(f"❌ 업로드 실패: {response.text}")
                except Exception as e:
                    st.error(f"❌ 업로드 중 오류 발생: {str(e)}")

    st.divider()

    # 사업지 정보
    st.subheader("📍 사업지 정보")
    target_area = st.text_input(
        "사업지 장소",
        value=st.session_state.target_area,
        placeholder="예: 서울특별시 강남구 역삼동",
        help="분양 사업지의 상세 주소를 입력하세요",
    )
    main_type = st.text_input(
        "단지 타입",
        value=st.session_state.main_type,
        placeholder="예: 84타입",
        help="분양 단지의 타입을 입력하세요",
    )
    total_units = st.text_input(
        "세대수",
        value=st.session_state.total_units,
        placeholder="예: 120세대",
        help="분양 단지의 총 세대수를 입력하세요",
    )

    # 설정 저장
    if st.button("💾 설정 저장"):
        st.session_state.target_area = target_area
        st.session_state.main_type = main_type
        st.session_state.total_units = total_units
        st.success("설정이 저장되었습니다!")

    st.divider()

    # 데이터 소스 선택
    st.subheader("📚 데이터 소스")
    use_faq = st.checkbox("FAQ 데이터 사용", value=True)
    use_rule = st.checkbox("주택공급규칙 데이터 사용", value=True)
    use_policy = st.checkbox("정책문서 데이터 사용", value=True)

    st.divider()

    # 스트리밍 모드
    st.subheader("⚡ 응답 모드")
    streaming_mode = st.toggle("스트리밍 모드", value=True, help="실시간으로 응답을 받습니다")

    st.divider()

    # 대화 초기화
    if st.button("🗑️ 대화 기록 초기화", type="secondary"):
        clear_history()

    # 세션 정보
    st.divider()
    st.caption(f"세션 ID: `{st.session_state.session_id[:8]}...`")

    # API 상태 확인
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ API 연결됨")
        else:
            st.error("❌ API 연결 실패")
    except:
        st.error("❌ API 연결 실패")

# 메인 화면
# 대화 기록 표시
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # 소스 표시 (assistant 메시지인 경우)
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    with st.expander(f"📄 참조 문서 ({len(message['sources'])}개)"):
                        for source in message["sources"]:
                            source_type = source.get("type", "알 수 없음")
                            source_detail = source.get("detail", "")

                            # 출처 타입에 따라 아이콘 표시
                            icon = "📌"
                            if source_type == "FAQ":
                                icon = "❓"
                            elif source_type == "주택공급규칙":
                                icon = "📋"
                            elif source_type == "정책문서":
                                icon = "📜"

                            st.markdown(f"### {icon} **[{source['id']}] {source_type}**")
                            if source_detail:
                                st.caption(f"🔖 {source_detail}")
                            st.markdown(f"> {source['content']}")
                            st.divider()

# 사용자 입력
if prompt := st.chat_input("질문을 입력하세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        if streaming_mode:
            # 스트리밍 모드
            response_placeholder = st.empty()
            sources = []

            for response, sources in send_message_streaming(
                prompt,
                st.session_state.target_area,
                st.session_state.main_type,
                st.session_state.total_units,
                use_faq,
                use_rule,
                use_policy,
            ):
                response_placeholder.markdown(response)

            # 소스 표시
            if sources:
                with st.expander(f"📄 참조 문서 ({len(sources)}개)"):
                    for source in sources:
                        source_type = source.get("type", "알 수 없음")
                        source_detail = source.get("detail", "")

                        # 출처 타입에 따라 아이콘 표시
                        icon = "📌"
                        if source_type == "FAQ":
                            icon = "❓"
                        elif source_type == "주택공급규칙":
                            icon = "📋"
                        elif source_type == "정책문서":
                            icon = "📜"

                        st.markdown(f"### {icon} **[{source['id']}] {source_type}**")
                        if source_detail:
                            st.caption(f"🔖 {source_detail}")
                        st.markdown(f"> {source['content']}")
                        st.divider()

        else:
            # 일반 모드
            with st.spinner("답변 생성 중..."):
                response, sources = send_message(
                    prompt,
                    st.session_state.target_area,
                    st.session_state.main_type,
                    st.session_state.total_units,
                    use_faq,
                    use_rule,
                    use_policy,
                )
                st.markdown(response)

                # 소스 표시
                if sources:
                    with st.expander(f"📄 참조 문서 ({len(sources)}개)"):
                        for source in sources:
                            source_type = source.get("type", "알 수 없음")
                            source_detail = source.get("detail", "")

                            # 출처 타입에 따라 아이콘 표시
                            icon = "📌"
                            if source_type == "FAQ":
                                icon = "❓"
                            elif source_type == "주택공급규칙":
                                icon = "📋"
                            elif source_type == "정책문서":
                                icon = "📜"

                            st.markdown(f"### {icon} **[{source['id']}] {source_type}**")
                            if source_detail:
                                st.caption(f"🔖 {source_detail}")
                            st.markdown(f"> {source['content']}")
                            st.divider()

    # AI 응답 저장
    st.session_state.messages.append(
        {"role": "assistant", "content": response, "sources": sources}
    )

# 예시 질문
with st.expander("💡 예시 질문"):
    example_questions = [
        "1세대 1주택자는 어떤 청약 조건이 필요한가요?",
        "생애최초 특별공급 자격은 어떻게 되나요?",
        "청약 가점제와 추첨제의 차이는 무엇인가요?",
        "특별공급과 일반공급의 차이를 알려주세요.",
        "재개발 아파트 청약은 어떻게 하나요?",
    ]
    for q in example_questions:
        st.markdown(f"- {q}")
