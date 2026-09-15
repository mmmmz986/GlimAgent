"""Streamlit 화면 구성과 출력. 파싱 및 LLM 호출은 main.py에서 처리합니다."""

from dataclasses import asdict

import streamlit as st

from CORE.log_parser import LogEntry


# 화면 구성(업로드, 파싱 결과, 분석 입력, 분석 결과)
def render_upload():
    st.title("Log Analyzer Agent")

    uploaded_file = st.file_uploader("FILE UPLOAD", type=["log", "txt"])

    encoding = st.selectbox("LOG ENCODING", ["auto", "utf-8-sig", "cp949", "utf-16"])

    return uploaded_file, encoding

# 파싱 결과 화면 렌더링(통계, 테이블, JSON 다운로드)
def render_parse_result(entries: list[LogEntry], encoding: str, parsed_json: str):
    st.subheader("RESULT PARSE")

    st.caption(f"인코딩: {encoding} · 줄 번호는 업로드한 원본 기준입니다.")

    total, parsed, partial, unparsed = st.columns(4)
    total.metric("전체 줄", len(entries))
    parsed.metric("형식 인식", sum(e.status == "parsed" for e in entries))
    partial.metric("일부 인식", sum(e.status == "partial" for e in entries))
    unparsed.metric("미인식", sum(e.status == "unparsed" for e in entries))

    st.caption("[날짜] [시간] 코드 메시지 형식을 인식하고 선두 태그를 추출합니다. 코드와 로그 레벨은 별개이며, 미인식 줄도 보존합니다.")

    st.dataframe([asdict(entry) for entry in entries[:1000]], use_container_width=True)

    if len(entries) > 1000:
        st.caption("미리보기는 처음 1,000줄입니다. JSON 다운로드에는 전체 결과가 포함됩니다.")

    st.download_button("파싱 결과 JSON 다운로드", parsed_json, "parsed_logs.json", "application/json")

# 질문 입력 화면 렌더링(질문, 분석 버튼)
def render_analysis_input():
    if "analysis_running" not in st.session_state:
        st.session_state.analysis_running = False

    question = st.text_input(
        "QUESTION",
        placeholder="예: 로그 분석해줘.",
        key="analysis_question",
        disabled=st.session_state.analysis_running,
    )

    def start_analysis():
        st.session_state.analysis_running = True
        st.session_state.analysis_requested = True
        st.session_state.pop("analysis_result", None)

    def stop_analysis():
        st.session_state.analysis_running = False
        st.session_state.analysis_stopped = True

    analyze_column, stop_column = st.columns(2)
    with analyze_column:
        st.button(
            "Analyze",
            disabled=st.session_state.analysis_running,
            on_click=start_analysis,
            use_container_width=True,
        )
    with stop_column:
        st.button(
            "Stop Analyze",
            disabled=not st.session_state.analysis_running,
            on_click=stop_analysis,
            use_container_width=True,
        )

    requested = st.session_state.pop("analysis_requested", False)
    stopped = st.session_state.pop("analysis_stopped", False)
    return question, requested, stopped

# 분석 결과 화면 렌더링
def analysis_progress():
    return st.spinner("로그를 분석하고 있습니다...")
def render_analysis_result(content):
    st.subheader("RESULT ANALYSIS")
    st.write(content)


def render_analysis_stream(chunks):
    """Render model chunks as they arrive and return the completed text."""
    st.subheader("RESULT ANALYSIS")
    output = st.empty()
    content = ""
    for chunk in chunks:
        part = chunk.content
        if isinstance(part, str):
            content += part
        elif isinstance(part, list):
            content += "".join(
                item.get("text", "") for item in part if isinstance(item, dict)
            )
        output.markdown(content + "▌")
    output.markdown(content)
    return content


def stored_analysis_result():
    return st.session_state.get("analysis_result")


def finish_analysis(content=None):
    st.session_state.analysis_running = False
    if content:
        st.session_state.analysis_result = content


def queue_notice(level, message):
    st.session_state.analysis_notice = (level, message)


def render_notice():
    notice = st.session_state.pop("analysis_notice", None)
    if notice is None:
        return
    level, message = notice
    if level == "error":
        st.error(message)
    else:
        st.warning(message)


def rerun():
    st.rerun()

# 오류/경고 메시지 화면 렌더링
def show_error(message: str):
    st.error(message)
def show_warning(message: str):
    st.warning(message)
