# 수행평가 관리 시스템

학생들이 수행평가 날짜를 놓치지 않도록 관리하는 Streamlit 기반 웹 애플리케이션입니다.

## 주요 기능

### 학생 모드
- 📅 **달력 보기**: 수행평가가 있는 날짜를 빨간색 테두리와 이모지로 명확하게 표시
- 🔍 **검색 기능**: 과목명으로 수행평가 검색
- 📚 **상세 보기**: 날짜 클릭 시 해당 날짜의 수행평가와 평가 척도 이미지 확인
- 🎯 **과목 필터링**: 자신이 듣는 과목만 선택하여 필터링 가능
- 🤖 **AI 주제 추천**: 학생의 진로/관심사를 입력하면 GPT가 수행평가 주제를 추천

### 선생님 모드
- ➕ **수행평가 추가**: 과목, 날짜, 평가 척도 이미지 업로드
- 🗑️ **수행평가 삭제**: 등록된 수행평가 삭제
- 📊 **전체 목록 확인**: 모든 수행평가 목록 확인 및 관리

## 설치 및 실행

### 1. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. (선택) OpenAI API 키 설정
AI 주제 추천 기능을 사용하려면 OpenAI API 키가 필요합니다.

**방법 1: Streamlit secrets.toml 파일 사용 (권장)**
1. `.streamlit/secrets.toml` 파일을 엽니다.
2. `YOUR_API_KEY_HERE`를 실제 OpenAI API 키로 교체합니다.
   ```toml
   OPENAI_API_KEY = "sk-your-actual-api-key-here"
   ```
3. API 키는 [OpenAI Platform](https://platform.openai.com/api-keys)에서 발급받을 수 있습니다.

**방법 2: 환경변수로 설정**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# Windows CMD
setx OPENAI_API_KEY "sk-..."

# macOS / Linux
export OPENAI_API_KEY="sk-..."
```

**참고:**
- 기본 모델은 `gpt-4o-mini`이며, 다른 모델을 쓰고 싶다면 `OPENAI_MODEL` 환경변수로 지정하세요.
- API 키가 설정되지 않은 경우, AI 주제 추천 기능은 비활성화되지만 다른 기능은 정상 작동합니다.

### 3. 애플리케이션 실행
```bash
streamlit run app.py
```

## Streamlit Cloud 배포

### 배포 방법
1. GitHub에 저장소를 푸시합니다.
2. [Streamlit Cloud](https://share.streamlit.io/)에 로그인합니다.
3. "New app"을 클릭하고 저장소를 선택합니다.
4. Main file path를 `app.py`로 설정합니다.
5. "Deploy!"를 클릭합니다.

### Streamlit Cloud에서 OpenAI API 키 설정
1. Streamlit Cloud 대시보드에서 앱을 선택합니다.
2. "Settings" → "Secrets" 메뉴로 이동합니다.
3. 다음 형식으로 secrets를 추가합니다:
   ```toml
   OPENAI_API_KEY = "sk-your-actual-api-key-here"
   ```
4. "Save"를 클릭하면 앱이 자동으로 재배포됩니다.

**중요:** Streamlit Cloud에서는 `.streamlit/secrets.toml` 파일이 작동하지 않습니다. 반드시 Streamlit Cloud의 Secrets 관리 페이지에서 설정해야 합니다.

## 사용 방법

### 학생 모드
1. 앱을 실행하면 기본적으로 학생 모드로 시작됩니다.
2. 달력에서 수행평가가 있는 날짜(빨간색 테두리와 📝 이모지로 표시)를 클릭하면 해당 날짜의 수행평가를 확인할 수 있습니다.
3. 검색 창에서 과목명을 입력하여 수행평가를 검색할 수 있습니다.
4. 설정에서 자신이 듣는 과목을 선택하면, 선택한 과목의 수행평가만 달력에 표시됩니다.
5. 월 이동 버튼(◀ 이전 달 / 다음 달 ▶)을 사용하여 다른 달의 수행평가를 확인할 수 있습니다.

### 선생님 모드
1. 설정 페이지로 이동합니다.
2. 선생님 코드를 입력합니다. (기본 코드: `teacher123`)
3. 선생님 모드로 전환되면 홈에서 수행평가를 추가할 수 있습니다.
4. 과목, 날짜를 선택하고 평가 척도 이미지를 업로드한 후 완료 버튼을 클릭합니다.

## 데이터 저장

- 수행평가 정보는 `data/performances.json` 파일에 저장됩니다.
- 업로드된 이미지는 `uploads/` 디렉토리에 저장됩니다.

## 주의사항

- 선생님 코드는 기본적으로 `teacher123`로 설정되어 있습니다. 실제 사용 시에는 환경변수나 별도 설정 파일에서 관리하는 것을 권장합니다.
- 이미지 파일은 로컬에 저장되므로, 서버 재시작 시에도 데이터가 유지됩니다.
- 같은 날짜에 같은 과목의 수행평가는 중복 등록할 수 없습니다.
- 오프라인 모드에서도 기존 데이터는 확인할 수 있습니다.
- OpenAI API 키가 설정되지 않은 경우, AI 주제 추천 기능은 비활성화됩니다.

## 검증 완료 항목

✅ 기본 시나리오 정상 작동 (추가/완료/수정/삭제/필터)
✅ 세션 내에서 상태 유지
✅ 코드 가독성 및 예외 처리
✅ UI 직관성 및 버튼/컨트롤 배치

## 기술 스택

- **Python**: 프로그래밍 언어
- **Streamlit**: 웹 프레임워크
- **Pillow**: 이미지 처리
- **JSON**: 데이터 저장 형식

