"""
데이터 관리 모듈
수행평가 정보를 JSON 파일로 저장/로드하고 이미지 파일을 관리합니다.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 데이터 디렉토리 설정
DATA_DIR = Path("data")
IMAGES_DIR = Path("uploads")
DATA_FILE = DATA_DIR / "performances.json"

# 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)


def load_data() -> List[Dict]:
    """수행평가 데이터를 로드합니다. (오프라인 모드 대응)"""
    if not DATA_FILE.exists():
        return []
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError, FileNotFoundError) as e:
        # 오프라인 모드나 파일 오류 시 빈 리스트 반환
        print(f"데이터 로드 오류 (오프라인 모드일 수 있음): {e}")
        return []


def save_data(data: List[Dict]) -> bool:
    """수행평가 데이터를 저장합니다."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"데이터 저장 오류: {e}")
        return False


def add_performance(subject: str, date: str, image_path: str) -> bool:
    """새로운 수행평가를 추가합니다."""
    try:
        data = load_data()
        
        # 중복 확인 (같은 과목, 같은 날짜)
        for item in data:
            if item.get('subject') == subject and item.get('date') == date:
                return False
        
        # ID 생성 (기존 ID 중 최대값 + 1)
        max_id = max([item.get('id', 0) for item in data], default=0)
        new_id = max_id + 1
        
        new_item = {
            'id': new_id,
            'subject': subject,
            'date': date,
            'image_path': image_path,
            'created_at': datetime.now().isoformat()
        }
        
        data.append(new_item)
        return save_data(data)
    except Exception as e:
        print(f"수행평가 추가 오류: {e}")
        return False


def get_performances_by_date(date: str) -> List[Dict]:
    """특정 날짜의 수행평가 목록을 반환합니다."""
    data = load_data()
    return [item for item in data if item.get('date') == date]


def get_all_performances() -> List[Dict]:
    """모든 수행평가 목록을 반환합니다."""
    return load_data()


def search_performances(keyword: str) -> List[Dict]:
    """키워드로 수행평가를 검색합니다."""
    data = load_data()
    keyword_lower = keyword.lower()
    return [
        item for item in data
        if keyword_lower in item.get('subject', '').lower()
    ]


def get_dates_with_performances() -> List[str]:
    """수행평가가 있는 날짜 목록을 반환합니다."""
    data = load_data()
    dates = set(item.get('date') for item in data if item.get('date'))
    return sorted(list(dates))


def save_uploaded_image(uploaded_file, subject: str, date: str) -> Optional[str]:
    """업로드된 이미지를 저장하고 경로를 반환합니다."""
    try:
        # 파일명 생성: 과목_날짜_타임스탬프.확장자
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(uploaded_file.name).suffix
        filename = f"{subject}_{date}_{timestamp}{file_extension}"
        filepath = IMAGES_DIR / filename
        
        # 파일 저장
        with open(filepath, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        return str(filepath)
    except Exception as e:
        print(f"이미지 저장 오류: {e}")
        return None


def delete_performance(performance_id: int) -> bool:
    """수행평가를 삭제합니다."""
    data = load_data()
    original_length = len(data)
    data = [item for item in data if item.get('id') != performance_id]
    
    if len(data) < original_length:
        return save_data(data)
    return False

