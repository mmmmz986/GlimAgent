from pathlib import Path
import sys

# MAIN 폴더에서 실행해도 프로젝트 패키지를 찾습니다.
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from CORE.llm import create_chain
from CORE.log_parser import decode_log, entries_to_json, parse_log
from VIEW import view


def initialize():
    """분석에 사용할 LLM 체인을 초기화합니다."""
    return create_chain()

def run_sequence(chain):
    uploaded_file, encoding = view.render_upload()
    entries = None
    parsed_json = None
    if uploaded_file is not None:
        try:
            log_text, detected_encoding = decode_log(uploaded_file.getvalue(), encoding)
            entries = parse_log(log_text)
            parsed_json = entries_to_json(entries)
        except (UnicodeError, ValueError) as exc:
            view.show_error(f"로그 파일을 읽지 못했습니다: {exc}")
        else:
            view.render_parse_result(entries, detected_encoding, parsed_json)

    question, requested = view.render_analysis_input()
    if not requested:
        return

    if uploaded_file is None:
        view.show_warning("로그 파일을 업로드하세요.")
    elif not question:
        view.show_warning("질문을 입력하세요.")
    elif not entries or not any(entry.raw.strip() for entry in entries):
        view.show_warning("읽을 수 있는 로그 내용이 필요합니다. 파일과 인코딩을 확인하세요.")
    else:
        with view.analysis_progress():
            result = chain.invoke({"log": parsed_json, "question": question})
        view.render_analysis_result(result.content)


def main():
    # 1. 초기화
    chain = initialize()

    # 2. 실행 시퀀스: 업로드 → 파싱 → 질문 → 분석 → 결과 표시
    run_sequence(chain)


if __name__ == "__main__":
    main()
