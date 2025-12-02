"""
수행평가 관리 앱
Streamlit 기반으로 수행평가 날짜와 평가 척도를 관리합니다.
"""
import os
import streamlit as st
from datetime import datetime, date
import calendar
from pathlib import Path
from typing import List, Optional
from data_manager import (
    load_data, add_performance, get_performances_by_date,
    get_all_performances, search_performances, get_dates_with_performances,
    save_uploaded_image, delete_performance
)
from PIL import Image

try:
    from openai import OpenAI  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - OpenAI 패키지가 없는 환경 대비
    OpenAI = None  # type: ignore

# 페이지 설정
st.set_page_config(
    page_title="수행평가 관리",
    page_icon="📅",
    layout="wide"
)

# 선생님 코드 (실제로는 환경변수나 별도 설정 파일에서 관리)
TEACHER_CODE = "teacher123"
SUBJECTS = [
    "국어", "수학", "영어", "사회", "과학", "역사", "도덕",
    "체육", "음악", "미술", "기술", "가정", "한문", "정보"
]
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# 세션 상태 초기화
if 'is_teacher' not in st.session_state:
    st.session_state.is_teacher = False
if 'selected_subjects' not in st.session_state:
    st.session_state.selected_subjects = []
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None


def check_teacher_mode():
    """선생님 모드 확인"""
    return st.session_state.is_teacher


def _get_openai_api_key() -> Optional[str]:
    """환경변수 또는 Streamlit secrets에서 OpenAI API 키를 가져옵니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    try:
        # 1) secrets.toml 최상단 키
        return st.secrets["OPENAI_API_KEY"]  # type: ignore[index]
    except Exception:
        pass

    try:
        # 2) 섹션 아래에 키가 정의된 경우 (예: [OPENAI_API])
        return st.secrets["OPENAI_API"]["OPENAI_API_KEY"]  # type: ignore[index]
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def get_openai_client():
    """OpenAI 클라이언트를 생성합니다."""
    if OpenAI is None:
        raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. requirements.txt를 통해 라이브러리를 설치해주세요.")
    api_key = _get_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다. 환경변수 또는 Streamlit secrets에 키를 추가해주세요.")
    return OpenAI(api_key=api_key)


def check_openai_configuration() -> tuple[bool, Optional[str]]:
    """OpenAI 사용 환경 확인"""
    if OpenAI is None:
        return False, "package_missing"
    if _get_openai_api_key() is None:
        return False, "api_key_missing"
    return True, None


def generate_ai_suggestions(
    student_name: str,
    grade: Optional[str],
    interests: str,
    preferred_subjects: List[str]
) -> str:
    """학생 정보 기반 수행평가 주제 추천을 생성합니다."""
    client = get_openai_client()
    subjects_text = ", ".join(preferred_subjects) if preferred_subjects else "모든 교과"
    user_prompt = (
        f"학생 이름: {student_name}\n"
        f"학년: {grade or '미입력'}\n"
        f"관심 분야 및 진로 목표: {interests.strip()}\n"
        f"선호 과목: {subjects_text}\n\n"
        "요청: 위 정보에 맞춰 수행평가 주제 3가지를 제안하세요. "
        "각 주제마다 학습 목표, 준비 과정, 예상 결과물 예시를 간략히 bullet 형식으로 제시해주세요. "
        "주제는 실현 가능하고 교과 연계성이 있어야 합니다."
    )
    
    # OpenAI Chat Completions API 사용
    response = client.chat.completions.create(
        model=DEFAULT_OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 중학생 수행평가를 돕는 교육 컨설턴트입니다. "
                    "학생의 진로와 관심사에 맞는 구체적인 프로젝트 주제를 제안하고, "
                    "현실적인 준비 과정을 안내합니다."
                ),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        max_tokens=600,
        temperature=0.7,
    )
    
    # 응답에서 텍스트 추출
    if response.choices and len(response.choices) > 0:
        suggestions = response.choices[0].message.content
        if suggestions:
            return suggestions.strip()
    
    raise RuntimeError("AI 응답을 해석할 수 없습니다. 잠시 후 다시 시도해주세요.")


def render_calendar(year: int, month: int, filter_subjects: List[str] = None):
    """달력을 렌더링하고 수행평가가 있는 날짜를 색으로 표시"""
    try:
        # 달력 데이터 가져오기 (오프라인 모드 대응)
        dates_with_performances = get_dates_with_performances()
        
        # 과목 필터링 적용
        if filter_subjects:
            all_performances = get_all_performances()
            filtered_dates = set()
            for perf in all_performances:
                if perf.get('subject') in filter_subjects:
                    filtered_dates.add(perf.get('date'))
            dates_with_performances = sorted(list(filtered_dates))
        else:
            dates_with_performances = set(dates_with_performances)
        
        # 달력 생성
        cal = calendar.monthcalendar(year, month)
        
        st.subheader(f"{year}년 {month}월")
        
        # 요일 헤더
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        cols = st.columns(7)
        for i, weekday in enumerate(weekdays):
            cols[i].markdown(f"<div style='text-align: center; font-weight: bold; padding: 5px;'>{weekday}</div>", unsafe_allow_html=True)
        
        # 달력 그리드
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    is_performance_day = date_str in dates_with_performances
                    
                    # 수행평가가 있는 날은 색상으로 강조 표시
                    if is_performance_day:
                        # 색상이 있는 배경으로 표시
                        cols[i].markdown(
                            f'<div style="background-color: #ffebee; border: 2px solid #f44336; border-radius: 5px; padding: 5px; text-align: center; margin-bottom: 5px;">'
                            f'<strong style="color: #d32f2f; font-size: 16px;">📝 {day}</strong></div>',
                            unsafe_allow_html=True
                        )
                        if cols[i].button("보기", key=f"btn_{date_str}", use_container_width=True, 
                                         help="수행평가가 있는 날짜입니다"):
                            st.session_state.selected_date = date_str
                            st.rerun()
                    else:
                        button_label = str(day)
                        if cols[i].button(button_label, key=f"day_{date_str}", use_container_width=True):
                            st.session_state.selected_date = date_str
                            st.rerun()
    except Exception as e:
        st.warning(f"달력을 불러오는 중 오류가 발생했습니다: {e}")
        st.info("기존 데이터만 표시됩니다. 인터넷 연결을 확인해주세요.")


def show_performances_for_date(selected_date: str, filter_subjects: List[str] = None):
    """선택된 날짜의 수행평가를 표시"""
    try:
        performances = get_performances_by_date(selected_date)
        
        # 과목 필터링 적용
        if filter_subjects:
            performances = [p for p in performances if p.get('subject') in filter_subjects]
        
        if not performances:
            st.info(f"{selected_date}에는 수행평가가 없습니다.")
            return
        
        st.subheader(f"📅 {selected_date} 수행평가")
        
        for perf in performances:
            with st.expander(f"📚 {perf.get('subject', '과목 없음')}", expanded=True):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.write(f"**과목:** {perf.get('subject')}")
                    st.write(f"**날짜:** {perf.get('date')}")
                
                with col2:
                    image_path = perf.get('image_path')
                    if image_path and Path(image_path).exists():
                        try:
                            img = Image.open(image_path)
                            st.image(img, caption=f"{perf.get('subject')} 평가 척도", use_container_width=True)
                        except Exception as e:
                            st.error(f"이미지를 불러올 수 없습니다: {e}")
                    else:
                        st.warning("이미지 파일을 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"수행평가를 불러오는 중 오류가 발생했습니다: {e}")
        st.info("인터넷 연결을 확인해주세요.")


def teacher_mode():
    """선생님 모드: 수행평가 추가"""
    st.header("👨‍🏫 선생님 모드")
    
    with st.form("add_performance_form"):
        st.subheader("수행평가 추가")
        
        # 과목 선택
        subject = st.selectbox("과목 선택", SUBJECTS)
        
        # 날짜 선택
        selected_date = st.date_input(
            "수행평가 날짜",
            value=date.today(),
            help="수행평가가 예정된 날짜를 선택하세요"
        )
        
        # 이미지 업로드
        uploaded_file = st.file_uploader(
            "평가 척도 이미지 업로드",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp']
        )
        
        submitted = st.form_submit_button("완료", use_container_width=True)
        
        if submitted:
            if uploaded_file is None:
                st.error("❌ 평가 척도 이미지를 업로드해주세요.")
            else:
                try:
                    # 이미지 저장
                    date_str = selected_date.strftime("%Y-%m-%d")
                    image_path = save_uploaded_image(uploaded_file, subject, date_str)
                    
                    if image_path:
                        # 데이터 저장
                        if add_performance(subject, date_str, image_path):
                            st.success(f"✅ {subject} 수행평가가 {date_str}에 추가되었습니다!")
                            st.balloons()  # 성공 시 축하 애니메이션
                            st.rerun()
                        else:
                            st.error("⚠️ 이미 같은 날짜에 해당 과목의 수행평가가 존재합니다.")
                    else:
                        st.error("❌ 이미지 저장에 실패했습니다. 파일 형식을 확인해주세요.")
                except Exception as e:
                    st.error(f"❌ 오류가 발생했습니다: {str(e)}")
                    st.info("파일을 다시 업로드해주세요.")


def student_mode():
    """학생 모드: 수행평가 확인"""
    st.header("👨‍🎓 학생 모드")
    
    # 과목 필터 표시
    if st.session_state.selected_subjects:
        st.info(f"📚 필터링된 과목: {', '.join(st.session_state.selected_subjects)}")
        if st.button("필터 해제"):
            st.session_state.selected_subjects = []
            st.rerun()
    
    # 검색 기능
    st.subheader("🔍 수행평가 검색")
    search_keyword = st.text_input(
        "과목명으로 검색", 
        placeholder="예: 수학, 국어",
        help="과목명을 입력하면 관련된 모든 수행평가를 검색합니다"
    )
    
    if search_keyword:
        try:
            results = search_performances(search_keyword)
            # 과목 필터링 적용
            if st.session_state.selected_subjects:
                results = [r for r in results if r.get('subject') in st.session_state.selected_subjects]
            
            if results:
                st.write(f"**검색 결과: {len(results)}개**")
                for perf in results:
                    with st.expander(f"📚 {perf.get('subject')} - {perf.get('date')}"):
                        image_path = perf.get('image_path')
                        if image_path and Path(image_path).exists():
                            try:
                                img = Image.open(image_path)
                                st.image(img, caption=f"{perf.get('subject')} 평가 척도", use_container_width=True)
                            except Exception as e:
                                st.error(f"이미지를 불러올 수 없습니다: {e}")
            else:
                st.info("검색 결과가 없습니다.")
        except Exception as e:
            st.warning(f"검색 중 오류가 발생했습니다: {e}")
            st.info("기존 데이터만 표시됩니다.")
    
    st.divider()
    
    # 달력 표시
    st.subheader("📅 수행평가 달력")
    
    # 현재 날짜
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # 월 선택
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ 이전 달"):
            if current_month == 1:
                current_year -= 1
                current_month = 12
            else:
                current_month -= 1
            st.session_state.current_year = current_year
            st.session_state.current_month = current_month
            st.rerun()
    
    with col3:
        if st.button("다음 달 ▶"):
            if current_month == 12:
                current_year += 1
                current_month = 1
            else:
                current_month += 1
            st.session_state.current_year = current_year
            st.session_state.current_month = current_month
            st.rerun()
    
    if 'current_year' not in st.session_state:
        st.session_state.current_year = current_year
    if 'current_month' not in st.session_state:
        st.session_state.current_month = current_month
    
    # 달력 렌더링 (과목 필터 적용)
    try:
        render_calendar(
            st.session_state.current_year, 
            st.session_state.current_month,
            filter_subjects=st.session_state.selected_subjects if st.session_state.selected_subjects else None
        )
    except Exception as e:
        st.warning(f"달력을 불러오는 중 오류가 발생했습니다: {e}")
        st.info("인터넷 연결을 확인해주세요. 기존 데이터만 표시됩니다.")
    
    # 선택된 날짜의 수행평가 표시
    if st.session_state.selected_date:
        st.divider()
        show_performances_for_date(
            st.session_state.selected_date,
            filter_subjects=st.session_state.selected_subjects if st.session_state.selected_subjects else None
        )

    st.divider()
    st.subheader("🧠 맞춤형 수행평가 주제 추천")
    st.caption("OpenAI GPT를 활용해 학생의 진로와 관심 분야에 맞는 수행평가 주제 아이디어를 제안합니다.")

    is_ready, reason = check_openai_configuration()
    if not is_ready:
        if reason == "package_missing":
            st.warning("`openai` 패키지가 설치되어 있지 않습니다. `pip install -r requirements.txt` 명령으로 패키지를 설치한 뒤 다시 시도하세요.")
        else:
            st.info("OpenAI API 키가 설정되어 있지 않아 추천 기능을 사용할 수 없습니다. 환경변수 `OPENAI_API_KEY`를 설정하거나 `.streamlit/secrets.toml`에 키를 추가한 후 다시 실행하세요.")
        return

    with st.form("ai_suggestion_form"):
        student_name = st.text_input("학생 이름", placeholder="예: 김서준")
        grade = st.selectbox(
            "학년 선택 (선택)",
            ["선택 안 함", "1학년", "2학년", "3학년"],
            index=0
        )
        interests = st.text_area(
            "관심 분야 / 진로 목표",
            placeholder="예: 인공지능, 로봇공학, 창의적 문제 해결, 메이커 활동",
            help="학생의 관심사나 꿈에 대해 간단히 적어주세요."
        )
        preferred_subjects = st.multiselect(
            "중점으로 삼고 싶은 과목 (선택)",
            SUBJECTS,
            default=st.session_state.selected_subjects if st.session_state.selected_subjects else []
        )
        submitted = st.form_submit_button("주제 추천 받기", use_container_width=True)

    if submitted:
        if not student_name.strip() or not interests.strip():
            st.warning("학생 이름과 관심 분야를 입력해주세요.")
            return

        grade_value = grade if grade != "선택 안 함" else None
        try:
            with st.spinner("AI가 맞춤형 주제를 추천하고 있어요..."):
                suggestions = generate_ai_suggestions(
                    student_name=student_name.strip(),
                    grade=grade_value,
                    interests=interests,
                    preferred_subjects=preferred_subjects
                )
            st.markdown(suggestions)
        except RuntimeError as e:
            st.error(f"⚠️ {e}")
        except Exception as e:
            st.error("예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            st.exception(e)


def settings_page():
    """설정 페이지"""
    st.header("⚙️ 설정")
    
    # 선생님 모드 전환
    st.subheader("모드 전환")
    
    if st.session_state.is_teacher:
        st.success("✅ 현재 선생님 모드입니다.")
        if st.button("👨‍🎓 학생 모드로 전환", use_container_width=True):
            st.session_state.is_teacher = False
            st.rerun()
    else:
        st.info("👨‍🎓 현재 학생 모드입니다.")
        teacher_code_input = st.text_input(
            "선생님 코드 입력",
            type="password",
            placeholder="선생님 코드를 입력하세요",
            help="선생님 코드를 입력하면 수행평가를 추가/수정/삭제할 수 있습니다"
        )
        
        if st.button("👨‍🏫 선생님 모드로 전환", use_container_width=True):
            if not teacher_code_input:
                st.warning("⚠️ 선생님 코드를 입력해주세요.")
            elif teacher_code_input == TEACHER_CODE:
                st.session_state.is_teacher = True
                st.success("✅ 선생님 모드로 전환되었습니다!")
                st.rerun()
            else:
                st.error("❌ 잘못된 선생님 코드입니다.")
    
    st.divider()
    
    # 과목 선택 (학생 모드에서만)
    if not st.session_state.is_teacher:
        st.subheader("내 과목 선택")
        all_subjects = SUBJECTS
        selected = st.multiselect(
            "듣는 과목을 선택하세요",
            all_subjects,
            default=st.session_state.selected_subjects,
            help="선택한 과목의 수행평가만 달력에 표시됩니다"
        )
        st.session_state.selected_subjects = selected
        if selected:
            st.info(f"📚 선택된 과목: {', '.join(selected)}")
        else:
            st.info("💡 과목을 선택하지 않으면 모든 과목의 수행평가가 표시됩니다.")
    
    st.divider()
    
    # 데이터 관리 (선생님 모드에서만)
    if st.session_state.is_teacher:
        st.subheader("📊 데이터 관리")
        try:
            all_performances = get_all_performances()
            st.write(f"**총 수행평가 수:** {len(all_performances)}개")
            
            if all_performances:
                st.write("**전체 수행평가 목록:**")
                for perf in all_performances:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"📚 **{perf.get('subject')}** - {perf.get('date')}")
                        with col3:
                            if st.button("🗑️ 삭제", key=f"delete_{perf.get('id')}", use_container_width=True):
                                if delete_performance(perf.get('id')):
                                    st.success("✅ 삭제되었습니다!")
                                    st.rerun()
                        st.divider()
            else:
                st.info("등록된 수행평가가 없습니다.")
        except Exception as e:
            st.error(f"❌ 데이터를 불러오는 중 오류가 발생했습니다: {e}")


def main():
    """메인 함수"""
    st.title("📅 수행평가 관리 시스템")
    
    # 오프라인 모드 감지 및 안내
    try:
        test_data = load_data()
    except Exception:
        st.warning("⚠️ 인터넷 연결을 확인할 수 없습니다. 기존 데이터만 표시됩니다.")
    
    # 사이드바 네비게이션
    page = st.sidebar.selectbox(
        "페이지 선택",
        ["홈", "설정"]
    )
    
    # 모드 표시
    mode_text = "👨‍🏫 선생님 모드" if check_teacher_mode() else "👨‍🎓 학생 모드"
    st.sidebar.info(mode_text)
    
    # 페이지 라우팅
    try:
        if page == "홈":
            if check_teacher_mode():
                teacher_mode()
            else:
                student_mode()
        elif page == "설정":
            settings_page()
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.info("페이지를 새로고침하거나 인터넷 연결을 확인해주세요.")


if __name__ == "__main__":
    main()

