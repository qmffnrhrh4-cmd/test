#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 자동 채점 시스템 - AI 버전
Gemini API 기반 스마트 채점 및 문제 생성
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import json
import re
from typing import Dict, List, Optional

# AI 기능 임포트 (선택적)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini API를 사용하려면 'python -m pip install google-generativeai' 실행")

# PDF 읽기 (선택적)
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PDF 파일을 읽으려면 'python -m pip install PyPDF2' 실행")

# PDF 생성 (선택적)
try:
    from pdf_generator import PDFGenerator
    PDF_GENERATOR_AVAILABLE = True
except ImportError:
    PDF_GENERATOR_AVAILABLE = False
    print("⚠️ PDF 생성 기능을 사용하려면 'python -m pip install reportlab Pillow' 실행")


# ============================================================================
# 모범답안 폴더 관리자
# ============================================================================

class ModelAnswerManager:
    """모범답안 폴더에서 파일을 읽고 매칭"""

    def __init__(self, folder_path: str = "모범답안"):
        self.folder_path = folder_path
        self.model_answers = []
        self.load_all_model_answers()

    def load_all_model_answers(self):
        """모범답안 폴더의 모든 파일 로드 (PDF, TXT, MD 지원)"""
        if not os.path.exists(self.folder_path):
            print(f"[모범답안] 폴더가 없습니다: {self.folder_path}")
            return

        for filename in os.listdir(self.folder_path):
            if filename.endswith(('.txt', '.md', '.pdf')):
                filepath = os.path.join(self.folder_path, filename)
                model_answer_data = self.parse_model_answer_file(filepath)
                if model_answer_data:
                    model_answer_data['파일명'] = filename
                    self.model_answers.append(model_answer_data)

        print(f"[모범답안] {len(self.model_answers)}개 모범답안 로드 완료")

    def parse_model_answer_file(self, filepath: str) -> Optional[Dict]:
        """모범답안 파일 파싱 (PDF, TXT, MD 지원)"""
        try:
            # 파일 확장자에 따라 읽기
            ext = os.path.splitext(filepath)[1].lower()

            if ext == '.pdf':
                # PDF는 FileReader 사용 (나중에 정의됨)
                if not PDF_AVAILABLE:
                    print(f"[WARNING] PDF 파일을 읽으려면 PyPDF2가 필요합니다: {filepath}")
                    return None

                from PyPDF2 import PdfReader
                reader = PdfReader(filepath)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n"
                content = content.strip()
            else:
                # TXT, MD는 직접 읽기
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

            result = {
                '모범답안': '',
                '필수_키워드': [],
                '금지어': [],
                '채점_팁': []
            }

            # [모범답안] 섹션 추출
            if '[모범답안]' in content:
                parts = content.split('[모범답안]')[1]
                if '[필수 키워드]' in parts:
                    result['모범답안'] = parts.split('[필수 키워드]')[0].strip()
                else:
                    result['모범답안'] = parts.strip()
            else:
                # 구조화되지 않은 파일은 전체를 모범답안으로 사용
                result['모범답안'] = content.strip()

            # [필수 키워드] 섹션 추출
            if '[필수 키워드]' in content:
                keywords_section = content.split('[필수 키워드]')[1]
                if '[금지어]' in keywords_section:
                    keywords_section = keywords_section.split('[금지어]')[0]
                elif '[채점 팁]' in keywords_section:
                    keywords_section = keywords_section.split('[채점 팁]')[0]

                # 쉼표로 구분된 키워드 파싱
                keywords_text = keywords_section.strip()
                result['필수_키워드'] = [k.strip() for k in keywords_text.split(',') if k.strip()]

            # [금지어] 섹션 추출
            if '[금지어]' in content:
                forbidden_section = content.split('[금지어]')[1]
                if '[채점 팁]' in forbidden_section:
                    forbidden_section = forbidden_section.split('[채점 팁]')[0]

                forbidden_text = forbidden_section.strip()
                result['금지어'] = [f.strip() for f in forbidden_text.split(',') if f.strip()]

            # [채점 팁] 섹션 추출
            if '[채점 팁]' in content:
                tips_section = content.split('[채점 팁]')[1].strip()
                # 각 줄을 팁으로 저장
                result['채점_팁'] = [line.strip() for line in tips_section.split('\n') if line.strip() and line.strip().startswith('-')]

            # 모범답안이 비어있으면 None 반환
            if not result['모범답안']:
                return None

            return result

        except Exception as e:
            print(f"[ERROR] 모범답안 파일 파싱 실패 ({filepath}): {e}")
            return None

    def find_all_model_answers(self, problem_text: str = None) -> List[Dict]:
        """모든 모범답안 반환 (유사도 점수 시스템 제거)"""
        if not self.model_answers:
            print("[모범답안] 로드된 모범답안이 없습니다.")
            return []

        print(f"[모범답안] {len(self.model_answers)}개의 모범답안을 찾았습니다.")
        return self.model_answers


# ============================================================================
# 문제 데이터베이스 관리자
# ============================================================================

class ProblemDatabaseManager:
    """문제 DB 관리 및 자동 매칭"""

    def __init__(self, db_path: str = "문제_DB.json"):
        self.db_path = db_path
        self.problems = []
        self.load_database()

    def load_database(self):
        """문제 DB 로드"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.problems = data.get('문제_목록', [])
                print(f"[DB] 문제 DB 로드 완료: {len(self.problems)}개 문제")
            else:
                print(f"[DB] 문제 DB 파일이 없습니다: {self.db_path}")
        except Exception as e:
            print(f"[DB] 문제 DB 로드 실패: {e}")

    def find_all_problems(self, text: str = None) -> List[Dict]:
        """모든 문제 반환 (유사도 점수 시스템 제거)"""
        if not self.problems:
            print("[DB] 로드된 문제가 없습니다.")
            return []

        print(f"[DB] {len(self.problems)}개의 문제를 찾았습니다.")
        return self.problems

    def get_problem_by_id(self, problem_id: str) -> Optional[Dict]:
        """ID로 문제 조회"""
        for problem in self.problems:
            if problem.get('id') == problem_id:
                return problem
        return None


# ============================================================================
# Gemini API 클라이언트
# ============================================================================

class GeminiClient:
    """Gemini API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None

        if self.api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                self.available = True
            except Exception as e:
                print(f"Gemini API 초기화 실패: {e}")
                self.available = False
        else:
            self.available = False

    def _get_few_shot_examples(self) -> str:
        """Few-shot learning을 위한 실제 채점 예시"""
        return """
# 학습 예시 (실제 OPR 채점 패턴)

## 예시 1: 우수 답안 (85점)
**문제**: 디지털 전환 추진 전략
**필수 키워드**: 디지털 혁신, 클라우드, AI 활용, 데이터 기반, 프로세스 혁신
**학생 답안**: "디지털 혁신을 통한 경쟁력 강화 전략 보고서. 1. 추진배경 □ 디지털 전환 가속화로 클라우드 및 AI 활용 필요성 증대 2. 추진방향 □ 데이터 기반 의사결정 체계 구축 □ 프로세스 혁신으로 업무효율 향상..."

**채점 결과**:
- 논리정확성: 35/40 (5개 키워드 중 5개 모두 포함, 구체적)
- 명확간결성: 26/30 (A등급, 간결하고 명확)
- 완결성: 24/30 (A등급, 기본 구조 완벽)
- **총점: 85/100**

**채점 사유**: 모든 필수 키워드 포함, 보고서 형식 완벽, 논리 흐름 우수

---

## 예시 2: 보통 답안 (62점)
**문제**: 탄소중립 실행 계획
**필수 키워드**: 온실가스 감축, 재생에너지, ESG 경영, 탄소배출권, 친환경 투자
**학생 답안**: "탄소중립 실행 계획. 온실가스를 줄이기 위해 재생에너지 확대가 필요합니다. ESG 경영 강화하고 친환경 투자를 늘려야 합니다..."

**채점 결과**:
- 논리정확성: 26/40 (5개 키워드 중 4개 포함, 탄소배출권 누락)
- 명확간결성: 20/30 (B등급, 약간 단순함)
- 완결성: 16/30 (C등급, 구조 미흡, 기호 미사용)
- **총점: 62/100**

**채점 사유**: 핵심 키워드 1개 누락, 보고서 형식 미흡, 구체성 부족

---

## 예시 3: 미흡 답안 (38점)
**문제**: 신사업 진출 전략
**필수 키워드**: 시장 분석, 경쟁력 확보, 리스크 관리, 투자계획, 추진체계
**학생 답안**: "신사업을 해야 합니다. 새로운 시장에 진출하여 경쟁력을 높이고 투자를 늘리면 좋을 것 같습니다..."

**채점 결과**:
- 논리정확성: 16/40 (5개 키워드 중 2개만 포함, 구체성 없음)
- 명확간결성: 12/30 (D등급, 장황하고 불명확)
- 완결성: 10/30 (D등급, 보고서 형식 없음, 제목·구조 없음)
- **총점: 38/100**

**채점 사유**: 대부분의 키워드 누락, 보고서가 아닌 에세이 형식, 구체성 매우 부족

---

이제 당신이 채점할 차례입니다. 위 예시들처럼 **정확하고 구체적으로** 채점하세요.
"""

    def grade_answer_detailed(
        self,
        student_answer: str,
        model_answer: str,
        keywords: List[str],
        forbidden_words: List[str]
    ) -> Dict:
        """상세한 답안 채점 (AI 기반)"""

        if not self.available:
            # Fallback - 기본 채점 사용
            grader = BasicGrader()
            return grader.grade_answer(student_answer, keywords, forbidden_words)

        # Few-shot learning을 위한 실제 예시 준비
        few_shot_examples = self._get_few_shot_examples()

        prompt = f"""당신은 OPR 채점 전문가입니다. 아래 두 답안을 비교하여 채점하세요.

# 절대 원칙
1. 두 답안이 거의 같은 내용이면 → 90-100점
2. 키워드 대부분 포함하면 → 70-89점
3. 키워드 반 이하면 → 50점 이하
4. 완전히 다른 답안이면 → 30점 이하

# 채점 방법

## 1단계: 답안 비교 (50점)
모범답안과 학생답안을 읽고 직접 비교:
- 내용이 거의 같음 → 48-50점
- 주요 내용 대부분 같음 → 40-47점
- 절반 정도 같음 → 25-39점
- 완전히 다름 → 0-24점

## 2단계: 키워드 확인 (30점)
각 키워드를 학생답안에서 찾으세요:

**매칭 규칙 (매우 유연하게!):**
- "신재생 사업" → "신재생사업", "신재생 에너지 사업" 모두 매칭
- "AI(인공지능)" → "AI", "인공지능", "인공지능 기술" 모두 매칭
- "2020년 12월 18일" → "2020년 12월", "12월 18일" 포함되면 매칭
- "박 차장" → "박차장", "박 부장" 유사하면 매칭

**점수 계산:**
- 키워드 {len(keywords)}개 중 매칭 개수 계산
- 모두 포함: 30점
- 80% 이상: 25점
- 60% 이상: 20점
- 40% 이상: 15점
- 그 이하: 10점 미만

## 3단계: 형식 (20점)
- 제목 있음: +5점
- 대제목 구분: +5점
- □/○ 기호: +5점
- 적절한 분량: +5점

---

【모범답안】
{model_answer[:2000]}

【학생 답안】
{student_answer[:2000]}

【필수 키워드 {len(keywords)}개】
{', '.join(keywords)}

---

# 중요: 실제 예시로 학습하세요

예시 1: 모범답안과 거의 동일
- 내용 비교: 48점 (거의 같음)
- 키워드: 30점 (모두 포함)
- 형식: 20점
- 총점: 98점

예시 2: 전혀 다른 답안
- 내용 비교: 5점 (완전히 다름)
- 키워드: 0점 (아무것도 없음)
- 형식: 10점
- 총점: 15점

---

# 출력: JSON만 반환

```json
{{
  "총점": 95,
  "논리정확성": {{
    "점수": 48,
    "매칭된_키워드": ["찾은 키워드들을 모두 나열"],
    "누락된_키워드": ["없는 키워드들을 나열"],
    "발견된_금지어": [],
    "잘한_점": ["구체적으로 어떤 점이 좋은지"],
    "부족한_점": ["무엇이 부족한지"],
    "피드백": "총평"
  }},
  "명확간결성": {{
    "등급": "S",
    "점수": 28,
    "잘한_점": ["좋은 점"],
    "부족한_점": ["부족한 점"],
    "개선_방법": ["개선 방법"],
    "피드백": "총평"
  }},
  "완결성": {{
    "등급": "S",
    "점수": 19,
    "잘한_점": ["좋은 점"],
    "부족한_점": ["부족한 점"],
    "개선_방법": ["개선 방법"],
    "피드백": "총평"
  }},
  "종합_평가": {{
    "강점": ["강점"],
    "약점": ["약점"],
    "보완_방법": ["보완 방법"],
    "다음_학습_방향": "학습 방향"
  }}
}}
```

**채점 체크리스트:**
✓ 모범답안과 비슷 → 90점 이상
✓ 키워드 대부분 → 70-89점
✓ 완전히 다름 → 30점 이하

JSON만 출력하세요."""

        try:
            # API 호출
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            print(f"[DEBUG] Gemini 원본 응답 (처음 500자): {result_text[:500]}")

            # JSON 추출 - 여러 방법 시도
            json_text = result_text

            # 방법 1: ```json ... ``` 형식
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            # 방법 2: ``` ... ``` 형식
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            # 방법 3: { ... } 추출
            elif "{" in json_text and "}" in json_text:
                start = json_text.find("{")
                end = json_text.rfind("}") + 1
                json_text = json_text[start:end]

            print(f"[DEBUG] 추출된 JSON (처음 300자): {json_text[:300]}")

            # JSON 파싱
            result = json.loads(json_text)

            # 필수 필드 검증 및 기본값 설정
            if "총점" not in result:
                result["총점"] = 0

            if "논리정확성" not in result:
                result["논리정확성"] = {
                    "점수": 0,
                    "매칭된_키워드": [],
                    "누락된_키워드": keywords,
                    "발견된_금지어": [],
                    "잘한_점": [],
                    "부족한_점": ["AI 응답 형식 오류"],
                    "피드백": "JSON 형식 오류"
                }

            if "명확간결성" not in result:
                result["명확간결성"] = {
                    "등급": "C",
                    "점수": 0,
                    "잘한_점": [],
                    "부족한_점": [],
                    "개선_방법": [],
                    "피드백": "평가 불가"
                }

            if "완결성" not in result:
                result["완결성"] = {
                    "등급": "C",
                    "점수": 0,
                    "잘한_점": [],
                    "부족한_점": [],
                    "개선_방법": [],
                    "피드백": "평가 불가"
                }

            if "종합_평가" not in result:
                result["종합_평가"] = {
                    "강점": [],
                    "약점": ["AI 채점 오류"],
                    "보완_방법": ["다시 시도하거나 API 키를 확인하세요"],
                    "다음_학습_방향": "기본 채점 시스템을 사용하세요"
                }

            print(f"[DEBUG] 채점 성공 - 총점: {result.get('총점')}")
            return result

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 오류: {e}")
            print(f"[ERROR] 문제된 텍스트: {json_text[:500] if 'json_text' in locals() else result_text[:500]}")
            # Fallback
            grader = BasicGrader()
            fallback_result = grader.grade_answer(student_answer, keywords, forbidden_words)
            fallback_result["종합_평가"]["약점"].append("Gemini API JSON 파싱 실패")
            return fallback_result

        except Exception as e:
            print(f"[ERROR] Gemini API 오류: {type(e).__name__}: {str(e)}")
            # Fallback
            grader = BasicGrader()
            fallback_result = grader.grade_answer(student_answer, keywords, forbidden_words)
            fallback_result["종합_평가"]["약점"].append(f"Gemini API 오류: {str(e)[:100]}")
            return fallback_result

    def analyze_problem_paper(self, problem_text: str) -> Dict:
        """문제지를 AI가 자동으로 분석하여 모범답안과 키워드 추출"""

        if not self.available:
            return {
                "error": "Gemini API를 사용할 수 없습니다.",
                "모범답안": "",
                "필수_키워드": [],
                "금지어": []
            }

        prompt = f"""# 역할
당신은 한국전력공사 OPR 시험 전문가입니다.
문제지를 분석하여 모범답안을 작성하고 필수 키워드를 추출해야 합니다.

# 문제지
{problem_text[:3000]}

# 작업
1. 문제를 정확히 이해하세요
2. 문제에 맞는 완벽한 모범답안을 작성하세요 (보고서 형식)
3. 필수 키워드 15-20개를 추출하세요
4. 사용하면 안 되는 금지어 5개를 지정하세요

# 모범답안 작성 기준
- 보고서 형식: 제목, 1/2/3/4 대제목, □/○/- 기호 사용
- 최소 15줄 이상
- 제시자료의 단어를 그대로 사용
- 구체적인 수치 포함
- 단기/중장기 구분 (필요시)

# 필수 키워드 추출 기준
- 문제의 핵심 개념
- 제시자료에 나온 기술명, 조직명, 정책명
- 구체적인 수치
- 중요한 전문용어

# 출력 형식
**반드시 아래 JSON 형식으로만 응답하세요.**

```json
{{
  "문제_제목": "추출한 문제 제목",
  "모범답안": "완벽한 보고서 형식의 모범답안 (최소 15줄)\\n\\n1. 추진배경\\n□ ...\\n○ ...\\n\\n2. 추진방향\\n□ ...\\n○ ...\\n\\n3. 대응전략\\n□ ...\\n○ ...\\n\\n4. 향후계획\\n□ ...",
  "필수_키워드": ["키워드1", "키워드2", "키워드3", "...최소 15개"],
  "금지어": ["금지어1", "금지어2", "금지어3", "금지어4", "금지어5"],
  "문제_분석": "이 문제는 무엇을 요구하는가에 대한 간단한 설명"
}}
```

JSON만 출력하세요."""

        try:
            print("[INFO] AI가 문제지를 분석 중...")
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            print(f"[DEBUG] AI 분석 응답 (처음 300자): {result_text[:300]}")

            # JSON 추출
            json_text = result_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            elif "{" in json_text and "}" in json_text:
                start = json_text.find("{")
                end = json_text.rfind("}") + 1
                json_text = json_text[start:end]

            result = json.loads(json_text)

            # 필수 필드 확인
            if "모범답안" not in result:
                result["모범답안"] = "모범답안 생성 실패"
            if "필수_키워드" not in result:
                result["필수_키워드"] = []
            if "금지어" not in result:
                result["금지어"] = []

            print(f"[INFO] 문제지 분석 완료 - 키워드: {len(result.get('필수_키워드', []))}개, 금지어: {len(result.get('금지어', []))}개")
            return result

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 오류: {e}")
            return {
                "error": f"JSON 파싱 오류: {str(e)}",
                "모범답안": "",
                "필수_키워드": [],
                "금지어": []
            }
        except Exception as e:
            print(f"[ERROR] 문제지 분석 오류: {type(e).__name__}: {str(e)}")
            return {
                "error": f"문제지 분석 중 오류: {str(e)}",
                "모범답안": "",
                "필수_키워드": [],
                "금지어": []
            }

    def generate_exam_from_files(
        self,
        reference_texts: List[str],
        difficulty: str = "medium"
    ) -> Dict:
        """폴더의 자료들로 실전 문제 생성"""

        if not self.available:
            return {"error": "Gemini API를 사용할 수 없습니다. API 키를 설정하세요."}

        # 참고 자료 제한 (너무 길면 API 에러)
        refs_text = "\n\n==========\n\n".join([t[:1500] for t in reference_texts[:5]])

        diff_desc = {
            "easy": "쉬움 - 명확한 키워드와 구조",
            "medium": "보통 - 실제 시험 수준",
            "hard": "어려움 - 복잡한 구조와 많은 제시자료"
        }

        prompt = f"""당신은 한국전력공사의 수석 OPR 문제 출제 전문가입니다.
실제 OPR 시험과 **완전히 동일한** 수준의 문제를 만들어야 합니다.

【참고 자료】
{refs_text}

【생성 조건】
- 난이도: {diff_desc.get(difficulty, "보통")}
- 실제 OPR 시험 형식 완벽 재현
- CEO 소통 메시지, 부장 이메일, 메신저, 언론 보도, 통계 자료 등 최소 10개 제시자료
- **모범답안도 함께 생성** (실제로 만점 받을 수 있는 수준)

# 실제 OPR 문제 구조 예시

**상황**: 회사가 직면한 구체적 상황 (200자)
**과제**: 본부장에게 보고할 보고서 작성 (명확한 지시)
**제시자료**:
1. CEO 소통 메시지 (회사 방향, 추진 배경)
2. 부장 이메일 (구체적 지시사항, 보고서 구성)
3. 메신저 대화 (주의사항, 금지어)
4. 언론 보도 (외부 환경)
5. 통계 자료 (구체적 수치)
6-10. 추가 자료 (기술 설명, 사례 등)

다음 JSON 형식으로 반드시 응답하세요:

{{
  "문제": {{
    "제목": "OO 추진전략 보고서",
    "상황": "구체적인 배경 상황 (200자 이상)",
    "과제": "본부장에게 보고할 보고서를 작성하시오. 다음 항목으로 구성: 추진배경, 추진방향, 세부전략, 향후계획",
    "보고서_구성": ["추진배경", "추진방향", "세부전략", "향후계획"],
    "제시자료": [
      {{
        "번호": 1,
        "유형": "CEO 소통 메시지",
        "제목": "디지털 혁신 추진 메시지",
        "내용": "전 직원 여러분, 우리 회사는... (최소 250자, 구체적으로)"
      }},
      {{
        "번호": 2,
        "유형": "부장 이메일",
        "제목": "보고서 작성 지시",
        "내용": "OOO 대리, 다음과 같이 보고서를 작성해주세요... (최소 200자)"
      }},
      {{
        "번호": 3,
        "유형": "메신저 대화",
        "제목": "주의사항 공유",
        "내용": "보고서 작성 시 주의할 점... 금지어: ... (최소 150자)"
      }}
      ... 최소 10개
    ],
    "필수_키워드": ["구체적인키워드1", "구체적인키워드2", ...최소 15개],
    "금지어": ["금지어1", "금지어2"],
    "예상_작성_시간": "150분",
    "출제_의도": "이 문제를 통해 평가하고자 하는 구체적 능력"
  }},
  "모범답안": {{
    "제목": "실제 만점 받을 수 있는 답안 제목",
    "본문": "1. 추진배경\\n□ 첫 번째 배경 (제시자료의 단어 그대로 사용)\\n○ 구체적 내용 (수치 포함)\\n\\n2. 추진방향\\n□ ... (최소 15줄, 모든 키워드 포함)",
    "포함된_키워드": ["키워드1", "키워드2", ...모두],
    "예상_점수": {{
      "논리정확성": 38,
      "명확간결성": 26,
      "완결성": 25,
      "총점": 89
    }},
    "작성_포인트": ["이 답안이 우수한 이유 1", "이 답안이 우수한 이유 2"]
  }},
  "채점_기준": {{
    "키워드별_배점": ["키워드1 (3점)", "키워드2 (3점)", ...],
    "감점_요소": ["금지어 사용 시 -2점", "형식 미비 시 -5점"],
    "만점_조건": ["필수 키워드 15개 모두 포함", "보고서 형식 완벽", "구체적 수치 포함"]
  }}
}}"""

        try:
            print("[DEBUG] 문제 생성 시작...")
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            print(f"[DEBUG] Gemini 응답 (처음 300자): {result_text[:300]}")

            # JSON 추출
            json_text = result_text

            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            elif "{" in json_text and "}" in json_text:
                start = json_text.find("{")
                end = json_text.rfind("}") + 1
                json_text = json_text[start:end]

            result = json.loads(json_text)

            # 필수 필드 검증 (새로운 구조)
            if "문제" not in result:
                # 구 형식 지원
                return result

            문제 = result.get("문제", {})
            모범답안 = result.get("모범답안", {})

            if not 문제.get("제목"):
                문제["제목"] = "OPR 실전 문제"
            if not 문제.get("제시자료"):
                문제["제시자료"] = [{"번호": 1, "유형": "참고", "내용": "제시자료 생성 실패"}]
            if not 문제.get("필수_키워드"):
                문제["필수_키워드"] = []

            result["문제"] = 문제
            result["모범답안"] = 모범답안

            print(f"[DEBUG] 문제 생성 성공 - 제시자료: {len(문제.get('제시자료', []))}개, 모범답안: {'있음' if 모범답안.get('본문') else '없음'}")
            return result

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 오류: {e}")
            print(f"[ERROR] 문제된 텍스트: {json_text[:500] if 'json_text' in locals() else result_text[:500]}")
            return {
                "error": f"JSON 파싱 오류: {str(e)}",
                "원본_응답": result_text[:500] if len(result_text) > 500 else result_text
            }

        except Exception as e:
            print(f"[ERROR] 문제 생성 오류: {type(e).__name__}: {str(e)}")
            return {"error": f"문제 생성 중 오류: {str(e)}"}


# ============================================================================
# 파일 읽기
# ============================================================================

class FileReader:
    """파일 읽기 (PDF, TXT)"""

    @staticmethod
    def read_file(file_path: str) -> str:
        """파일 읽기"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            return FileReader.read_pdf(file_path)
        elif ext == '.txt':
            return FileReader.read_txt(file_path)
        elif ext == '.hwp':
            return "HWP 파일은 TXT로 변환 후 사용해주세요.\n(한글에서 다른 이름으로 저장 → TXT 선택)"
        else:
            return FileReader.read_txt(file_path)

    @staticmethod
    def read_pdf(file_path: str) -> str:
        """PDF 읽기"""
        if not PDF_AVAILABLE:
            return "PDF를 읽으려면 PyPDF2 설치가 필요합니다.\n'설치.bat'을 실행하세요."

        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"PDF 읽기 오류: {str(e)}"

    @staticmethod
    def read_txt(file_path: str) -> str:
        """TXT 읽기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            try:
                with open(file_path, 'r', encoding='cp949') as f:
                    return f.read()
            except Exception as e:
                return f"파일 읽기 오류: {str(e)}"

    @staticmethod
    def read_folder(folder_path: str, extensions: List[str] = ['.pdf', '.txt']) -> List[str]:
        """폴더의 모든 파일 읽기"""
        texts = []

        if not os.path.exists(folder_path):
            return texts

        for filename in os.listdir(folder_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in extensions:
                file_path = os.path.join(folder_path, filename)
                text = FileReader.read_file(file_path)
                if text and "오류" not in text:
                    texts.append(text)

        return texts


# ============================================================================
# 기본 채점 시스템 (Fallback)
# ============================================================================

class BasicGrader:
    """기본 채점 시스템 (AI 없을 때)"""

    def __init__(self):
        self.grade_to_score = {
            'S': 1.0, 'A': 0.85, 'B': 0.70, 'C': 0.55, 'D': 0.40
        }

    def normalize_text(self, text: str) -> str:
        """텍스트 정규화 - 공백, 특수문자 제거"""
        import re
        # 공백 제거
        text = text.replace(' ', '').replace('\t', '').replace('\n', '')
        # 특수 괄호 제거
        text = text.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
        # 소문자 변환
        text = text.lower()
        return text

    def fuzzy_match(self, keyword: str, text: str) -> bool:
        """유연한 키워드 매칭"""
        # 방법 1: 정규화 후 부분 매칭
        norm_kw = self.normalize_text(keyword)
        norm_text = self.normalize_text(text)

        if norm_kw in norm_text:
            return True

        # 방법 2: 키워드의 80% 이상 문자가 순서대로 있으면 매칭
        if len(norm_kw) < 3:
            return False

        # 최소 매칭 비율
        required_chars = max(3, int(len(norm_kw) * 0.7))
        matched_chars = 0
        text_idx = 0

        for char in norm_kw:
            pos = norm_text.find(char, text_idx)
            if pos != -1:
                matched_chars += 1
                text_idx = pos + 1

        return matched_chars >= required_chars

    def grade_answer(self, answer_text: str, keywords: List[str], forbidden: List[str]) -> Dict:
        """기본 채점 (개선된 키워드 매칭)"""

        print(f"[BasicGrader] 채점 시작 - 키워드 {len(keywords)}개")

        # 키워드 매칭 (개선된 로직)
        matched = []
        missing = []

        for kw in keywords:
            if self.fuzzy_match(kw, answer_text):
                matched.append(kw)
                print(f"[BasicGrader] ✓ 매칭: {kw}")
            else:
                missing.append(kw)
                print(f"[BasicGrader] ✗ 누락: {kw}")

        # 금지어
        found_forbidden = []
        for word in forbidden:
            if self.fuzzy_match(word, answer_text):
                found_forbidden.append(word)
                print(f"[BasicGrader] ⚠ 금지어 발견: {word}")

        # 점수 계산
        if len(keywords) > 0:
            keyword_ratio = len(matched) / len(keywords)
            logic_score = 40 * keyword_ratio
        else:
            logic_score = 0

        # 금지어 감점
        logic_score = max(0, logic_score - len(found_forbidden) * 2)

        # 간결성 평가 (간단한 휴리스틱)
        lines = answer_text.strip().split('\n')
        line_count = len([l for l in lines if l.strip()])

        if line_count >= 15:
            completeness_score = 22.0  # B+
            completeness_grade = "B"
        elif line_count >= 10:
            completeness_score = 18.0  # C+
            completeness_grade = "C"
        else:
            completeness_score = 14.0  # D
            completeness_grade = "D"

        # 명확성 평가
        clarity_score = 21.0  # 기본 B등급
        clarity_grade = "B"

        total = logic_score + clarity_score + completeness_score

        # 잘한 점 / 부족한 점 생성
        well_done = []
        lacking = []

        if len(matched) > 0:
            well_done.append(f"{len(matched)}개 키워드를 포함함")
        if len(matched) >= len(keywords) * 0.7:
            well_done.append("70% 이상의 키워드를 포함하여 기본 내용을 충실히 작성")

        if len(missing) > 0:
            lacking.append(f"{len(missing)}개 키워드 누락")
        if len(missing) >= len(keywords) * 0.3:
            lacking.append("중요 키워드가 많이 누락됨")
        if len(found_forbidden) > 0:
            lacking.append(f"금지어 {len(found_forbidden)}개 사용으로 {len(found_forbidden)*2}점 감점")

        print(f"[BasicGrader] 채점 완료 - 총점: {round(total, 1)}점")

        return {
            "총점": round(total, 1),
            "논리정확성": {
                "점수": round(logic_score, 1),
                "매칭된_키워드": matched,
                "누락된_키워드": missing,
                "발견된_금지어": found_forbidden,
                "잘한_점": well_done,
                "부족한_점": lacking,
                "피드백": f"{len(matched)}/{len(keywords)}개 키워드 매칭 ({keyword_ratio*100:.0f}%)"
            },
            "명확간결성": {
                "등급": clarity_grade,
                "점수": clarity_score,
                "잘한_점": ["기본적인 문장 구성"],
                "부족한_점": [],
                "개선_방법": ["AI 채점으로 더 정확한 평가를 받으세요"],
                "피드백": "기본 평가 (AI 미사용)"
            },
            "완결성": {
                "등급": completeness_grade,
                "점수": completeness_score,
                "잘한_점": [f"{line_count}줄 작성"] if line_count >= 10 else [],
                "부족한_점": ["최소 15줄 이상 작성 권장"] if line_count < 15 else [],
                "개선_방법": ["보고서 형식(제목, □/○/- 기호)을 갖추세요"],
                "피드백": f"기본 평가 ({line_count}줄, AI 미사용)"
            },
            "종합_평가": {
                "강점": well_done if well_done else ["답안을 작성함"],
                "약점": (lacking if lacking else ["AI 채점을 사용하면 더 정확한 피드백을 받을 수 있습니다"]) + ["⚙️ Gemini API 키를 설정하면 상세한 피드백을 받을 수 있습니다"],
                "보완_방법": [
                    f"누락된 키워드 {len(missing)}개를 추가하세요: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}",
                    "API 설정 메뉴에서 Gemini API 키를 입력하세요"
                ],
                "다음_학습_방향": "키워드 중심 작성 연습. 제시자료의 단어를 그대로 사용하세요."
            }
        }


# ============================================================================
# GUI
# ============================================================================

class OPRSystemGUI:
    """OPR 시스템 GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("📚 OPR 자동 채점 시스템 - AI 버전")
        self.root.geometry("1200x850")

        # API 키
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # 시스템 초기화
        self.init_systems()

        # UI 생성
        self.create_widgets()

    def init_systems(self):
        """시스템 초기화"""
        if self.gemini_api_key and GEMINI_AVAILABLE:
            try:
                self.ai_client = GeminiClient(self.gemini_api_key)
                self.ai_available = self.ai_client.available
            except:
                self.ai_available = False
        else:
            self.ai_available = False

        self.basic_grader = BasicGrader()
        self.file_reader = FileReader()

        # 모범답안 폴더 매니저 초기화 (가장 중요!)
        self.model_answer_manager = ModelAnswerManager()

        # 문제 데이터베이스 (레거시, 백업용)
        self.problem_db = ProblemDatabaseManager()

        # PDF 생성기 초기화
        if PDF_GENERATOR_AVAILABLE:
            try:
                self.pdf_generator = PDFGenerator()
            except ImportError as e:
                print(f"[PDF] PDF 생성기 초기화 실패: {e}")
                self.pdf_generator = None
        else:
            self.pdf_generator = None

        # 여러 모범답안 관리
        self.loaded_model_answers = []  # 로드된 모범답안 리스트
        self.current_model_answer_index = 0  # 현재 선택된 인덱스

    def create_widgets(self):
        """UI 구성"""
        # 상단
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=120)
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(
            title_frame,
            text="📚 OPR 자동 채점 시스템 - AI 버전",
            font=("맑은 고딕", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)

        status_text = "✅ Gemini AI 활성화" if self.ai_available else "⚠️ AI 미활성화 (기본 모드)"
        status_label = tk.Label(
            title_frame,
            text=status_text,
            font=("맑은 고딕", 11),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        status_label.pack()

        # 메인 컨테이너
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 왼쪽 메뉴
        left_frame = tk.Frame(main_container, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        menu_label = tk.Label(
            left_frame,
            text="🎯 메뉴",
            font=("맑은 고딕", 16, "bold")
        )
        menu_label.pack(pady=(0, 20))

        buttons = [
            ("📝 AI 답안 채점", self.show_grading_panel, "#3498db"),
            ("📄 실전 문제 생성", self.show_exam_panel, "#2ecc71"),
            ("📚 공부 노하우", self.show_study_guide, "#e74c3c"),
            ("⚙️ API 키 설정", self.show_api_settings, "#f39c12"),
        ]

        for text, command, color in buttons:
            btn = tk.Button(
                left_frame,
                text=text,
                command=command,
                font=("맑은 고딕", 11, "bold"),
                bg=color,
                fg="white",
                relief=tk.RAISED,
                bd=3,
                cursor="hand2",
                height=2
            )
            btn.pack(fill=tk.X, pady=5)

        exit_btn = tk.Button(
            left_frame,
            text="🚪 종료",
            command=self.root.quit,
            font=("맑은 고딕", 12, "bold"),
            bg="#95a5a6",
            fg="white",
            relief=tk.RAISED,
            bd=3,
            cursor="hand2",
            height=2
        )
        exit_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        # 오른쪽 패널
        self.right_frame = tk.Frame(main_container, bg="white", relief=tk.SUNKEN, bd=2)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.show_welcome()

    def clear_panel(self):
        """패널 초기화"""
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    def show_welcome(self):
        """환영 화면"""
        self.clear_panel()

        welcome_text = f"""

🎓 OPR 자동 채점 시스템 AI 버전에 오신 것을 환영합니다!

현재 상태: {'✅ Gemini AI 활성화' if self.ai_available else '⚠️ AI 미활성화'}

{'AI가 상세하게 채점하고 피드백을 제공합니다!' if self.ai_available else 'API 키를 설정하면 AI 기능을 사용할 수 있습니다.'}


【주요 기능】

📝 AI 답안 채점
   - PDF/HWP/TXT 파일 첨부 가능
   - AI가 모범답안과 비교하여 상세 채점
   - 잘한 점, 부족한 점, 보완 방법 제공
   - 다음 학습 방향 안내

📄 실전 문제 생성
   - 특정 폴더의 자료들로 실전 문제 생성
   - AI가 실제 OPR 형식으로 문제 만들기
   - 10개 이상의 제시자료 포함

📚 공부 노하우
   - 핵심 전략 TOP 5
   - 채점 방식 이해

⚙️ API 키 설정
   - Gemini API 키 입력
   - AI 기능 활성화


{"✅ 지금 바로 AI 채점을 사용해보세요!" if self.ai_available else "⚠️ '⚙️ API 키 설정' 메뉴에서 Gemini API 키를 입력하세요."}
        """

        label = tk.Label(
            self.right_frame,
            text=welcome_text,
            font=("맑은 고딕", 11),
            bg="white",
            justify=tk.LEFT
        )
        label.pack(expand=True, pady=20, padx=20)

    def show_grading_panel(self):
        """채점 패널"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="📝 AI 답안 채점 (스마트 피드백)",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        # 스크롤 가능한 컨테이너
        canvas = tk.Canvas(self.right_frame, bg="white")
        scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 1. 문제지 업로드
        problem_frame = tk.LabelFrame(
            scrollable_frame,
            text="1️⃣ 문제지 업로드 (모범답안 폴더에서 자동 매칭)",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        problem_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(
            problem_frame,
            text="💡 문제지를 업로드하면 '모범답안/' 폴더에서 해당 모범답안을 자동으로 찾습니다",
            font=("맑은 고딕", 9),
            bg="white",
            fg="#27ae60"
        ).pack(pady=3)

        self.problem_file_var = tk.StringVar(value="파일 없음")
        tk.Label(
            problem_frame,
            textvariable=self.problem_file_var,
            font=("맑은 고딕", 9),
            bg="white",
            fg="#7f8c8d"
        ).pack(pady=3)

        tk.Button(
            problem_frame,
            text="📂 문제지 선택 (PDF/HWP/TXT)",
            command=self.select_problem_file,
            font=("맑은 고딕", 10, "bold"),
            bg="#9b59b6",
            fg="white",
            height=2
        ).pack(pady=5, padx=10, fill=tk.X)

        # 2. 답안지 업로드
        answer_frame = tk.LabelFrame(
            scrollable_frame,
            text="2️⃣ 답안지 업로드 (PDF/HWP/TXT 첨부 또는 직접 입력)",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        answer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.answer_file_var = tk.StringVar(value="파일 없음")
        tk.Label(
            answer_frame,
            textvariable=self.answer_file_var,
            font=("맑은 고딕", 9),
            bg="white",
            fg="#7f8c8d"
        ).pack(pady=3)

        tk.Button(
            answer_frame,
            text="📂 답안지 선택",
            command=self.select_answer_file,
            font=("맑은 고딕", 9),
            bg="#3498db",
            fg="white"
        ).pack(pady=3)

        self.answer_text = scrolledtext.ScrolledText(
            answer_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD,
            height=8
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 3. 모범답안
        model_frame = tk.LabelFrame(
            scrollable_frame,
            text="3️⃣ 모범답안 (비교 기준 - 자동입력됨)",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        model_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 모범답안 선택 드롭다운
        model_selector_frame = tk.Frame(model_frame, bg="white")
        model_selector_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        tk.Label(
            model_selector_frame,
            text="📚 모범답안 선택:",
            font=("맑은 고딕", 10),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.model_answer_var = tk.StringVar(value="모범답안 없음")
        self.model_answer_dropdown = ttk.Combobox(
            model_selector_frame,
            textvariable=self.model_answer_var,
            state="readonly",
            font=("맑은 고딕", 9),
            width=60
        )
        self.model_answer_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.model_answer_dropdown.bind("<<ComboboxSelected>>", self.on_model_answer_selected)

        self.model_answer_text = scrolledtext.ScrolledText(
            model_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD,
            height=6
        )
        self.model_answer_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 4. 필수 키워드
        keyword_frame = tk.LabelFrame(
            scrollable_frame,
            text="4️⃣ 필수 키워드 (쉼표로 구분 - 자동입력됨)",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        keyword_frame.pack(fill=tk.X, padx=10, pady=5)

        self.keywords_text = scrolledtext.ScrolledText(
            keyword_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD,
            height=4
        )
        self.keywords_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 5. 금지어
        forbidden_frame = tk.LabelFrame(
            scrollable_frame,
            text="5️⃣ 금지어 (쉼표로 구분, 선택사항)",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        forbidden_frame.pack(fill=tk.X, padx=10, pady=5)

        self.forbidden_text = tk.Entry(
            forbidden_frame,
            font=("맑은 고딕", 10)
        )
        self.forbidden_text.pack(fill=tk.X, padx=5, pady=5)

        # 버튼
        btn_frame = tk.Frame(scrollable_frame, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="📋 샘플 불러오기",
            command=self.load_sample_with_criteria,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="🗑️ 전체 지우기",
            command=self.clear_all_inputs,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="✅ AI 채점 시작",
            command=self.grade_answer_ai,
            font=("맑은 고딕", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            width=18,
            height=2
        ).pack(side=tk.RIGHT, padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def on_model_answer_selected(self, event=None):
        """드롭다운에서 모범답안 선택 시 호출"""
        if not self.loaded_model_answers:
            return

        # 현재 선택된 인덱스 찾기
        selected_text = self.model_answer_var.get()
        for i, answer_data in enumerate(self.loaded_model_answers):
            display_name = f"{i+1}. {answer_data.get('파일명', 'Unknown')}"
            if selected_text == display_name:
                self.current_model_answer_index = i
                self.display_model_answer(i)
                break

    def display_model_answer(self, index: int):
        """특정 인덱스의 모범답안을 화면에 표시"""
        if index < 0 or index >= len(self.loaded_model_answers):
            return

        answer_data = self.loaded_model_answers[index]

        # 모범답안 표시
        model_answer = answer_data.get('모범답안', '')
        self.model_answer_text.delete("1.0", tk.END)
        self.model_answer_text.insert("1.0", model_answer)

        # 키워드 표시
        keywords = answer_data.get('필수_키워드', [])
        keywords_str = ', '.join(keywords)
        self.keywords_text.delete("1.0", tk.END)
        self.keywords_text.insert("1.0", keywords_str)

        # 금지어 표시
        forbidden = answer_data.get('금지어', [])
        if forbidden:
            forbidden_str = ', '.join(forbidden)
            self.forbidden_text.delete(0, tk.END)
            self.forbidden_text.insert(0, forbidden_str)
        else:
            self.forbidden_text.delete(0, tk.END)

    def select_problem_file(self):
        """문제지 파일 선택 및 모범답안 표시"""
        filename = filedialog.askopenfilename(
            title="문제지 파일 선택",
            filetypes=[
                ("지원 파일", "*.pdf *.txt *.hwp"),
                ("PDF 파일", "*.pdf"),
                ("텍스트 파일", "*.txt"),
                ("한글 파일", "*.hwp"),
                ("모든 파일", "*.*")
            ]
        )

        if not filename:
            return

        self.problem_file_var.set(f"선택: {os.path.basename(filename)}")

        # 파일 읽기
        content = self.file_reader.read_file(filename)

        if not content:
            messagebox.showerror("오류", "파일을 읽을 수 없습니다.")
            return

        # 모든 모범답안 가져오기 (유사도 점수 시스템 제거)
        all_model_answers = self.model_answer_manager.find_all_model_answers(content)

        if all_model_answers:
            # 모범답안 로드 성공
            self.loaded_model_answers = all_model_answers

            # 드롭다운 업데이트
            dropdown_values = [f"{i+1}. {ans.get('파일명', 'Unknown')}"
                             for i, ans in enumerate(all_model_answers)]
            self.model_answer_dropdown['values'] = dropdown_values

            # 첫 번째 모범답안 선택
            self.model_answer_var.set(dropdown_values[0])
            self.current_model_answer_index = 0
            self.display_model_answer(0)

            # 사용자에게 알림
            messagebox.showinfo(
                "✅ 모범답안 로드 완료!",
                f"{len(all_model_answers)}개의 모범답안을 찾았습니다!\n\n"
                f"📚 드롭다운에서 다른 모범답안을 선택할 수 있습니다.\n"
                f"💡 현재: {all_model_answers[0].get('파일명', 'Unknown')}\n\n"
                f"이제 답안지를 업로드하세요!"
            )

        else:
            # 모범답안 없음
            self.loaded_model_answers = []
            self.model_answer_dropdown['values'] = []
            self.model_answer_var.set("모범답안 없음")

            messagebox.showwarning(
                "모범답안을 찾을 수 없습니다",
                f"'모범답안/' 폴더에 파일이 없거나 읽을 수 없습니다.\n\n"
                f"해결 방법:\n"
                f"1. '모범답안/' 폴더에 PDF, TXT, MD 파일을 추가하세요\n"
                f"2. 또는 아래 필드에 직접 입력하세요\n\n"
                f"모범답안 파일 형식 (선택사항):\n"
                f"[모범답안]\n답안 내용...\n\n"
                f"[필수 키워드]\n키워드1, 키워드2, ...\n\n"
                f"[금지어]\n금지어1, 금지어2, ..."
            )

    def select_answer_file(self):
        """답안지 파일 선택"""
        filename = filedialog.askopenfilename(
            title="답안지 파일 선택",
            filetypes=[
                ("지원 파일", "*.pdf *.txt *.hwp"),
                ("PDF 파일", "*.pdf"),
                ("텍스트 파일", "*.txt"),
                ("한글 파일", "*.hwp"),
                ("모든 파일", "*.*")
            ]
        )

        if filename:
            self.answer_file_var.set(f"선택: {os.path.basename(filename)}")

            # 파일 읽기
            content = self.file_reader.read_file(filename)
            self.answer_text.delete("1.0", tk.END)
            self.answer_text.insert("1.0", content)

            messagebox.showinfo(
                "답안지 로드 완료",
                f"답안지가 로드되었습니다.\n\n"
                f"파일: {os.path.basename(filename)}\n\n"
                f"모범답안과 키워드를 확인한 후\n"
                f"'✅ AI 채점 시작' 버튼을 클릭하세요."
            )

    def clear_all_inputs(self):
        """전체 입력 지우기"""
        self.answer_text.delete("1.0", tk.END)
        self.model_answer_text.delete("1.0", tk.END)
        self.keywords_text.delete("1.0", tk.END)
        self.forbidden_text.delete(0, tk.END)
        self.problem_file_var.set("파일 없음")
        self.answer_file_var.set("파일 없음")

    def load_sample_with_criteria(self):
        """샘플 + 채점기준 함께 불러오기"""
        # 학생 답안 샘플
        sample_answer = """전력망 건설 지연 대응전략 보고서

1. 추진배경
□ 첨단산업 전력수요 증가 및 재생e 발전 확산으로 전력망 역할 증대
○ 반도체 등 첨단산업단지 대용량 전력공급 인프라 구축 필요
○ 재생e 계통연계 지연으로 발전제약 해소 시급(최대 6.5GW)

2. 추진방향
□ 발전제약 해소를 통한 안정적 전력공급 실현
□ 법령 제개정으로 인허가 절차 개선

3. 대응전략
□ 단기(~'27년)
○ (발전제약 해소) NWAs 기술 적용으로 송전능력 2.6GW 확보
○ (법령 제개정) 전원촉진법 개정으로 입지선정위원회 법제화('26.1)

4. 향후계획
□ 전력망 적기 건설을 위한 전사 다짐대회 개최: 12월 16일"""

        # 모범답안
        model_answer = """전력망 건설 지연 대응전략 보고서

1. 추진배경
□ 첨단산업 전력수요 증가 및 재생에너지 발전 확산으로 전력망 역할 증대
○ 반도체·AI 등 첨단산업단지 대용량 전력공급 인프라 구축 필요
○ 재생에너지 계통연계 지연으로 발전제약 해소 시급(최대 6.5GW)

2. 추진방향
□ 전력망 건설지연 해소를 통한 안정적 전력공급 실현
□ 법령 제개정 및 시공기간 단축으로 적기 건설 추진
□ 전력망혁신위원회 중심 범정부 협력체계 구축

3. 대응전략
□ 단기(~'27년): 긴급 해소 방안
○ (발전제약 해소) NWAs 기술 적용으로 송전능력 2.6GW 확보
○ (법령 제개정) 전원촉진법 개정으로 입지선정위원회 법제화('26.1)
○ (시공기간 단축) 계통안정화용 ESS, 유연송전설비 우선 적용

□ 중장기(~'30년): 근본적 해결
○ WAMS 기반 동적 송전용량 산정시스템 구축('28~)
○ 전력망 선제적 투자 확대 및 민자 유치

4. 향후계획
□ 전력망혁신위원회 정기회의 개최(분기 1회)
□ 전력망 적기 건설을 위한 전사 다짐대회: 12월 16일"""

        # 필수 키워드
        keywords = """전력망 건설지연, 발전제약 해소, 법령 제개정, 시공기간 단축, 전력망혁신위원회, 전원촉진법, 입지선정위원회, NWAs, 계통안정화용 ESS, 유연송전설비, WAMS, 동적 송전용량"""

        # 금지어
        forbidden = """HVDC, 디지털 뉴딜, 한국판 뉴딜, 코로나"""

        # UI에 입력
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.insert("1.0", sample_answer)

        self.model_answer_text.delete("1.0", tk.END)
        self.model_answer_text.insert("1.0", model_answer)

        self.keywords_text.delete("1.0", tk.END)
        self.keywords_text.insert("1.0", keywords)

        self.forbidden_text.delete(0, tk.END)
        self.forbidden_text.insert(0, forbidden)

        messagebox.showinfo("샘플 로드 완료", "샘플 데이터가 모두 로드되었습니다.\n이제 'AI 채점 시작' 버튼을 눌러보세요!")

    def grade_answer_ai(self):
        """AI 채점 실행"""
        answer = self.answer_text.get("1.0", tk.END).strip()
        model_answer = self.model_answer_text.get("1.0", tk.END).strip()
        keywords_raw = self.keywords_text.get("1.0", tk.END).strip()
        forbidden_raw = self.forbidden_text.get().strip()

        # 유효성 검사
        if not answer:
            messagebox.showwarning("경고", "학생 답안을 입력하세요.")
            return

        if not model_answer:
            messagebox.showwarning("경고", "모범답안을 입력하세요.")
            return

        if not keywords_raw:
            messagebox.showwarning("경고", "필수 키워드를 입력하세요.")
            return

        # 키워드 파싱 (쉼표로 구분)
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        forbidden = [f.strip() for f in forbidden_raw.split(",") if f.strip()] if forbidden_raw else []

        if not keywords:
            messagebox.showwarning("경고", "최소 1개 이상의 키워드를 입력하세요.")
            return

        # 진행 창
        progress = tk.Toplevel(self.root)
        progress.title("AI 채점 중...")
        progress.geometry("450x180")
        progress.transient(self.root)
        progress.grab_set()

        tk.Label(
            progress,
            text="🤖 Gemini AI가 답안을 분석하고 있습니다...",
            font=("맑은 고딕", 13, "bold"),
            pady=20
        ).pack()

        tk.Label(
            progress,
            text=f"✓ 모범답안과 비교 중\n✓ {len(keywords)}개 키워드 매칭 중\n✓ 상세 피드백 생성 중",
            font=("맑은 고딕", 10),
            fg="#2c3e50",
            justify=tk.LEFT
        ).pack()

        tk.Label(
            progress,
            text="10-30초 정도 소요됩니다...",
            font=("맑은 고딕", 9),
            fg="#7f8c8d"
        ).pack(pady=10)

        progress.update()

        try:
            # AI 채점
            if self.ai_available:
                print(f"[INFO] AI 채점 시작 - 키워드 {len(keywords)}개, 금지어 {len(forbidden)}개")
                result = self.ai_client.grade_answer_detailed(
                    answer, model_answer, keywords, forbidden
                )
                print(f"[INFO] AI 채점 완료 - 총점: {result.get('총점', 0)}점")
            else:
                print("[INFO] AI 미사용 - 기본 채점 사용")
                result = self.basic_grader.grade_answer(answer, keywords, forbidden)

            progress.destroy()
            self.show_grading_result(result)

        except Exception as e:
            progress.destroy()
            print(f"[ERROR] 채점 오류: {type(e).__name__}: {str(e)}")
            messagebox.showerror("오류", f"채점 중 오류 발생:\n{str(e)}\n\n기본 채점으로 전환합니다.")
            # Fallback
            try:
                result = self.basic_grader.grade_answer(answer, keywords, forbidden)
                self.show_grading_result(result)
            except:
                pass

    def show_grading_result(self, result: Dict):
        """채점 결과 표시"""
        win = tk.Toplevel(self.root)
        win.title("📊 AI 채점 결과")
        win.geometry("900x750")

        # 제목
        tk.Label(
            win,
            text="📊 AI 상세 채점 결과",
            font=("맑은 고딕", 18, "bold"),
            bg="#3498db",
            fg="white",
            pady=15
        ).pack(fill=tk.X)

        # 총점
        score_frame = tk.Frame(win, bg="#ecf0f1", pady=20)
        score_frame.pack(fill=tk.X)

        tk.Label(
            score_frame,
            text=f"총점: {result.get('총점', 0)} / 100점",
            font=("맑은 고딕", 28, "bold"),
            bg="#ecf0f1",
            fg="#e74c3c"
        ).pack()

        # 상세 결과
        text_widget = scrolledtext.ScrolledText(
            win,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 포맷팅
        content = self.format_grading_result(result)
        text_widget.insert("1.0", content)
        text_widget.config(state=tk.DISABLED)

        # 버튼
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="💾 TXT 저장",
            command=lambda: self.save_result(result),
            font=("맑은 고딕", 10),
            bg="#2ecc71",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        # PDF 저장 버튼 추가
        if self.pdf_generator:
            tk.Button(
                btn_frame,
                text="📄 PDF 저장",
                command=lambda: self.save_result_as_pdf(result),
                font=("맑은 고딕", 10),
                bg="#e74c3c",
                fg="white"
            ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="닫기",
            command=win.destroy,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        ).pack(side=tk.RIGHT, padx=5)

    def format_grading_result(self, result: Dict) -> str:
        """결과 포맷팅"""
        lines = []
        lines.append("="*80)
        lines.append("AI 상세 채점 결과")
        lines.append("="*80)
        lines.append("")
        lines.append(f"🎯 총점: {result.get('총점', 0)}/100점")
        lines.append("")

        # 논리정확성
        logic = result.get('논리정확성', {})
        lines.append(f"【1】 논리·정확성: {logic.get('점수', 0)}/40점")
        lines.append("-"*80)

        matched = logic.get('매칭된_키워드', [])
        missing = logic.get('누락된_키워드', [])
        forbidden = logic.get('발견된_금지어', [])

        lines.append(f"✅ 매칭된 키워드 ({len(matched)}개):")
        for kw in matched[:10]:
            lines.append(f"   • {kw}")

        if missing:
            lines.append(f"\n❌ 누락된 키워드 ({len(missing)}개):")
            for kw in missing[:10]:
                lines.append(f"   • {kw}")

        if forbidden:
            lines.append(f"\n⚠️ 금지어 발견:")
            for word in forbidden:
                lines.append(f"   • {word}")

        well_done = logic.get('잘한_점', [])
        if well_done:
            lines.append("\n👍 잘한 점:")
            for item in well_done:
                lines.append(f"   • {item}")

        lacking = logic.get('부족한_점', [])
        if lacking:
            lines.append("\n📌 부족한 점:")
            for item in lacking:
                lines.append(f"   • {item}")

        lines.append(f"\n💬 피드백: {logic.get('피드백', '')}")
        lines.append("")

        # 명확간결성
        clarity = result.get('명확간결성', {})
        lines.append(f"【2】 명확·간결성: {clarity.get('등급', '-')}등급 ({clarity.get('점수', 0)}/30점)")
        lines.append("-"*80)

        if clarity.get('잘한_점'):
            lines.append("👍 잘한 점:")
            for item in clarity['잘한_점']:
                lines.append(f"   • {item}")

        if clarity.get('부족한_점'):
            lines.append("\n📌 부족한 점:")
            for item in clarity['부족한_점']:
                lines.append(f"   • {item}")

        if clarity.get('개선_방법'):
            lines.append("\n💡 개선 방법:")
            for item in clarity['개선_방법']:
                lines.append(f"   • {item}")

        lines.append(f"\n💬 피드백: {clarity.get('피드백', '')}")
        lines.append("")

        # 완결성
        completeness = result.get('완결성', {})
        lines.append(f"【3】 완결성: {completeness.get('등급', '-')}등급 ({completeness.get('점수', 0)}/30점)")
        lines.append("-"*80)

        if completeness.get('잘한_점'):
            lines.append("👍 잘한 점:")
            for item in completeness['잘한_점']:
                lines.append(f"   • {item}")

        if completeness.get('부족한_점'):
            lines.append("\n📌 부족한 점:")
            for item in completeness['부족한_점']:
                lines.append(f"   • {item}")

        if completeness.get('개선_방법'):
            lines.append("\n💡 개선 방법:")
            for item in completeness['개선_방법']:
                lines.append(f"   • {item}")

        lines.append(f"\n💬 피드백: {completeness.get('피드백', '')}")
        lines.append("")

        # 종합평가
        overall = result.get('종합_평가', {})
        if overall:
            lines.append("【종합 평가】")
            lines.append("="*80)

            if overall.get('강점'):
                lines.append("\n💪 전체 강점:")
                for item in overall['강점']:
                    lines.append(f"   • {item}")

            if overall.get('약점'):
                lines.append("\n⚠️ 전체 약점:")
                for item in overall['약점']:
                    lines.append(f"   • {item}")

            if overall.get('보완_방법'):
                lines.append("\n🔧 보완 방법:")
                for item in overall['보완_방법']:
                    lines.append(f"   • {item}")

            if overall.get('다음_학습_방향'):
                lines.append(f"\n🎯 다음 학습 방향:")
                lines.append(f"   {overall['다음_학습_방향']}")

        lines.append("\n" + "="*80)

        return "\n".join(lines)

    def save_result(self, result: Dict):
        """결과 저장"""
        filename = filedialog.asksaveasfilename(
            title="채점 결과 저장",
            defaultextension=".json",
            filetypes=[("JSON 파일", "*.json"), ("텍스트 파일", "*.txt")]
        )

        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                else:
                    content = self.format_grading_result(result)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)

                messagebox.showinfo("저장 완료", f"결과가 저장되었습니다:\n{filename}")
            except Exception as e:
                messagebox.showerror("저장 오류", f"저장 중 오류: {e}")

    def save_result_as_pdf(self, result: Dict):
        """채점 결과를 PDF로 저장"""
        if not self.pdf_generator:
            messagebox.showerror("오류", "PDF 생성 기능을 사용할 수 없습니다.\nreportlab과 Pillow를 설치하세요.")
            return

        filename = filedialog.asksaveasfilename(
            title="채점 결과 PDF 저장",
            defaultextension=".pdf",
            filetypes=[("PDF 파일", "*.pdf")]
        )

        if filename:
            try:
                success = self.pdf_generator.generate_grading_result_pdf(result, filename)
                if success:
                    messagebox.showinfo("저장 완료", f"PDF가 저장되었습니다:\n{filename}")
                    # PDF 열기 (선택적)
                    import subprocess
                    import platform
                    if platform.system() == 'Windows':
                        os.startfile(filename)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.call(['open', filename])
                    else:  # Linux
                        subprocess.call(['xdg-open', filename])
                else:
                    messagebox.showerror("오류", "PDF 생성에 실패했습니다.")
            except Exception as e:
                messagebox.showerror("저장 오류", f"PDF 저장 중 오류: {e}")

    def show_exam_panel(self):
        """문제 생성 패널"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="📄 실전 문제 생성 (AI 기반)",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        # 폴더 선택
        folder_frame = tk.LabelFrame(
            self.right_frame,
            text="1️⃣ 참고 자료 폴더 선택",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        folder_frame.pack(fill=tk.X, padx=10, pady=10)

        self.folder_var = tk.StringVar(value="폴더가 선택되지 않았습니다")

        tk.Label(
            folder_frame,
            textvariable=self.folder_var,
            font=("맑은 고딕", 9),
            bg="white",
            fg="#7f8c8d"
        ).pack(pady=5)

        tk.Button(
            folder_frame,
            text="📂 폴더 선택 (문제지, 모범답안 등)",
            command=self.select_folder,
            font=("맑은 고딕", 10),
            bg="#3498db",
            fg="white"
        ).pack(pady=10)

        # 난이도
        diff_frame = tk.LabelFrame(
            self.right_frame,
            text="2️⃣ 난이도 선택",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        diff_frame.pack(fill=tk.X, padx=10, pady=10)

        self.difficulty_var = tk.StringVar(value="medium")

        diff_btn_frame = tk.Frame(diff_frame, bg="white")
        diff_btn_frame.pack(pady=10)

        for text, value in [("쉬움", "easy"), ("보통", "medium"), ("어려움", "hard")]:
            tk.Radiobutton(
                diff_btn_frame,
                text=text,
                variable=self.difficulty_var,
                value=value,
                font=("맑은 고딕", 10),
                bg="white"
            ).pack(side=tk.LEFT, padx=10)

        # 생성 버튼
        tk.Button(
            self.right_frame,
            text="✨ AI로 실전 문제 생성하기",
            command=self.generate_exam_ai,
            font=("맑은 고딕", 12, "bold"),
            bg="#2ecc71",
            fg="white",
            height=2
        ).pack(pady=15)

        # 결과
        self.exam_result_text = scrolledtext.ScrolledText(
            self.right_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        self.exam_result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def select_folder(self):
        """폴더 선택"""
        folder = filedialog.askdirectory(title="참고 자료 폴더 선택")

        if folder:
            self.selected_folder = folder
            self.folder_var.set(f"선택: {folder}")

    def generate_exam_ai(self):
        """AI 문제 생성"""
        if not hasattr(self, 'selected_folder'):
            messagebox.showwarning("경고", "폴더를 먼저 선택하세요.")
            return

        if not self.ai_available:
            messagebox.showerror("오류", "AI 기능을 사용하려면 Gemini API 키를 설정하세요.")
            return

        # 진행 창
        progress = tk.Toplevel(self.root)
        progress.title("문제 생성 중...")
        progress.geometry("400x150")
        progress.transient(self.root)
        progress.grab_set()

        tk.Label(
            progress,
            text="🤖 AI가 실전 문제를 생성하고 있습니다...",
            font=("맑은 고딕", 12, "bold"),
            pady=20
        ).pack()

        tk.Label(
            progress,
            text="폴더의 자료들을 분석하여 문제 생성 중\n2-3분 정도 소요됩니다.",
            font=("맑은 고딕", 10),
            fg="#7f8c8d"
        ).pack()

        progress.update()

        try:
            # 폴더에서 파일 읽기
            texts = self.file_reader.read_folder(self.selected_folder)

            if not texts:
                progress.destroy()
                messagebox.showwarning("경고", "폴더에 읽을 수 있는 파일이 없습니다.")
                return

            # AI 문제 생성
            difficulty = self.difficulty_var.get()
            result = self.ai_client.generate_exam_from_files(texts, difficulty)

            progress.destroy()

            if "error" in result:
                messagebox.showerror("오류", result["error"])
                return

            # 결과 표시
            self.exam_result_text.delete("1.0", tk.END)

            # 새 형식 지원
            if "문제" in result:
                문제 = result["문제"]
                모범답안 = result.get("모범답안", {})

                info = f"""✅ AI가 완전한 실전 문제 세트를 생성했습니다!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 문제 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 제목: {문제.get('제목', '')}
📝 상황: {문제.get('상황', '')[:100]}...
🔑 필수 키워드: {len(문제.get('필수_키워드', []))}개
📊 제시자료: {len(문제.get('제시자료', []))}개
⏱️ 예상 시간: {문제.get('예상_작성_시간', '')}

출제 의도: {문제.get('출제_의도', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 모범답안 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{f"📄 제목: {모범답안.get('제목', '')}" if 모범답안.get('제목') else ""}
{f"📝 본문: {len(모범답안.get('본문', ''))}자" if 모범답안.get('본문') else ""}
{f"🎯 포함 키워드: {len(모범답안.get('포함된_키워드', []))}개" if 모범답안.get('포함된_키워드') else ""}
{f"💯 예상 점수: {모범답안.get('예상_점수', {}).get('총점', '-')}점" if 모범답안.get('예상_점수') else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💾 '전체 문제지 저장' 버튼으로 문제, 모범답안, 채점기준을 모두 저장할 수 있습니다!
"""
            else:
                # 구 형식
                info = f"""✅ AI가 실전 문제를 생성했습니다!

📌 제목: {result.get('제목', '')}
📝 상황: {result.get('상황', '')}
🔑 필수 키워드: {len(result.get('필수_키워드', []))}개
📊 제시자료: {len(result.get('제시자료', []))}개
⏱️ 예상 시간: {result.get('예상_작성_시간', '')}

출제 의도: {result.get('출제_의도', '')}
"""

            self.exam_result_text.insert("1.0", info)
            self.current_exam = result

            # 저장 버튼
            tk.Button(
                self.right_frame,
                text="💾 전체 문제지 저장",
                command=self.save_exam,
                font=("맑은 고딕", 10, "bold"),
                bg="#3498db",
                fg="white"
            ).pack(pady=5)

        except Exception as e:
            progress.destroy()
            messagebox.showerror("오류", f"문제 생성 중 오류:\n{str(e)}")

    def save_exam(self):
        """문제 저장"""
        if not hasattr(self, 'current_exam'):
            return

        filename = filedialog.asksaveasfilename(
            title="문제지 저장",
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("JSON 파일", "*.json")]
        )

        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.current_exam, f, ensure_ascii=False, indent=2)
                else:
                    # 문제지 포맷
                    content = self.format_exam_document(self.current_exam)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)

                messagebox.showinfo("저장 완료", f"문제지가 저장되었습니다:\n{filename}")
            except Exception as e:
                messagebox.showerror("저장 오류", f"저장 중 오류: {e}")

    def format_exam_document(self, exam: Dict) -> str:
        """문제지 문서 포맷 (문제 + 모범답안 + 채점기준)"""

        # 새 형식 지원
        if "문제" in exam:
            문제 = exam["문제"]
            모범답안 = exam.get("모범답안", {})
            채점기준 = exam.get("채점_기준", {})

            doc = f"""
{'='*80}
OPR 실전 연습 문제 - 완전판 (AI 생성)
{'='*80}

【📋 문제】

제목: {문제.get('제목', '')}

1. 보고서 작성배경 및 상황
{'-'*80}

{문제.get('상황', '')}

{문제.get('과제', '')}

2. 보고서 작성 및 평가기준
{'-'*80}

□ 다음 항목으로 구성된 보고서를 작성하시오:
"""
            for item in 문제.get('보고서_구성', []):
                doc += f"   - {item}\n"

            doc += f"""
□ 작성 및 평가 주요기준
  ○ 논리·정확성 (40점): 보고서 전체의 논리가 일관되고 구체적 근거에 의거하여 작성
  ○ 명확·간결성 (30점): 불필요한 정보 없이 핵심내용 위주로 명확·간결하게 작성
  ○ 완결성 (30점): 보고 목적에 부합하는 구성으로 완결된 형식의 보고서를 작성

3. 제시자료
{'-'*80}
"""

            for mat in 문제.get('제시자료', []):
                doc += f"\n【제시자료 {mat.get('번호', '')}】 {mat.get('유형', '')} - {mat.get('제목', '')}\n\n"
                doc += f"{mat.get('내용', '')}\n\n"
                doc += "-"*80 + "\n"

            doc += f"""
【참고】 필수 키워드 ({len(문제.get('필수_키워드', []))}개)
{'-'*80}
"""
            for i, kw in enumerate(문제.get('필수_키워드', []), 1):
                doc += f"  {i}. {kw}\n"

            if 문제.get('금지어'):
                doc += f"""
【주의】 금지어
{'-'*80}
"""
                for word in 문제.get('금지어', []):
                    doc += f"  ⚠️ {word}\n"

            doc += f"""
{'='*80}
예상 작성 시간: {문제.get('예상_작성_시간', '')}
출제 의도: {문제.get('출제_의도', '')}
{'='*80}


{'='*80}
【✅ 모범답안】
{'='*80}

{모범답안.get('제목', '')}

{모범답안.get('본문', '')}


"""
            if 모범답안.get('작성_포인트'):
                doc += f"""
【작성 포인트】
{'-'*80}
"""
                for i, point in enumerate(모범답안.get('작성_포인트', []), 1):
                    doc += f"{i}. {point}\n"

            if 모범답안.get('예상_점수'):
                점수 = 모범답안['예상_점수']
                doc += f"""
【예상 점수】
{'-'*80}
논리·정확성: {점수.get('논리정확성', '-')}/40점
명확·간결성: {점수.get('명확간결성', '-')}/30점
완결성: {점수.get('완결성', '-')}/30점
총점: {점수.get('총점', '-')}/100점
"""

            if 채점기준:
                doc += f"""

{'='*80}
【📊 채점 기준】
{'='*80}

"""
                if 채점기준.get('키워드별_배점'):
                    doc += "【키워드별 배점】\n" + "-"*80 + "\n"
                    for 배점 in 채점기준['키워드별_배점']:
                        doc += f"• {배점}\n"

                if 채점기준.get('감점_요소'):
                    doc += "\n【감점 요소】\n" + "-"*80 + "\n"
                    for 감점 in 채점기준['감점_요소']:
                        doc += f"• {감점}\n"

                if 채점기준.get('만점_조건'):
                    doc += "\n【만점 조건】\n" + "-"*80 + "\n"
                    for 조건 in 채점기준['만점_조건']:
                        doc += f"✓ {조건}\n"

            doc += f"\n{'='*80}\n"
            return doc

        else:
            # 구 형식 (이전 코드 유지)
            doc = f"""
================================================================================
OPR 실전 연습 문제 (AI 생성)
================================================================================

【문제】

제목: {exam.get('제목', '')}
...
"""
            return doc

    def show_study_guide(self):
        """공부 가이드"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="📚 공부 노하우 (핵심 전략)",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        guide_text = scrolledtext.ScrolledText(
            self.right_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        guide_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        content = """
【핵심 전략 TOP 5】

🎯 1. 제시문의 단어를 그대로 사용
   모든 단어는 문제지에 있는 단어만 쓰고, 있는 그대로 작성하는 게 중요합니다.
   예시:
     • ❌ 온실가스 억제 → ✅ 온실가스 저감
     • ❌ 친환경 기술수준 부족 → ✅ 친환경 기술수준 미흡

🎯 2. 키워드를 최대한 많이 포함
   채점자는 200명 답안을 빠르게 채점하므로, 키워드 중심으로 채점합니다.
   예시:
     • 정 모르겠으면 관련 키워드를 최대한 많이 작성
     • 문제 지문에서 중요해 보이는 단어는 모두 포함

🎯 3. 시험지 받으면 먼저 제목, 대제목 작성
   문제에서 제목, 대제목 등 틀을 잡고 시작합니다.
   예시:
     • 1단계: 제목, 대제목 먼저 써놓기
     • 2단계: 읽으면서 채워나가기

🎯 4. CEO 메시지에서 추진배경과 향후 일정 추출
   CEO 메시지는 주로 추진배경과 향후 일정을 언급합니다.
   예시:
     • CEO가 '~를 하자' → 무조건 향후 계획
     • 전사 행사, 토론회 등 → 향후 계획

🎯 5. 부장과 컴케에서 보고서 틀 확인
   보통 2, 3번 보고서 틀이 잡히고, 주의사항도 언급됩니다.
   예시:
     • 부장: '추진방향은 A, B, C로 구분해서 작성하세요'
     • → 이것까지 잡아놓고 시작!


【채점 기준】

📊 논리·정확성 (40점)
   - 키워드 매칭 중심
   - 금지어 사용 시 감점 (1개당 -2점)

📊 명확·간결성 (30점)
   - S/A/B/C/D 등급 평가
   - 불필요한 반복, 장황한 표현 확인
   - 35자 제한 준수

📊 완결성 (30점)
   - S/A/B/C/D 등급 평가
   - 보고서 구조 (제목, 1/2/3, □/○/-)
   - 최소 15줄 이상


【금지사항】

⚠️ 금지어 사용 (메신저/쪽지에서 확인)
⚠️ CEO 중심이 아닌 일정
⚠️ 타 신재생 사업 관련 (디지털 뉴딜, 한국판 뉴딜, 코로나 등)


💡 핵심 요약: 제시문의 키워드를 그대로, 최대한 많이 사용하라!
"""

        guide_text.insert("1.0", content)
        guide_text.config(state=tk.DISABLED)

    def show_api_settings(self):
        """API 설정"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="⚙️ Gemini API 설정",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        desc = """
Gemini API를 사용하면 AI 기능을 모두 사용할 수 있습니다.

✅ 상세한 답안 채점 (잘한 점, 부족한 점, 보완 방법)
✅ 폴더 자료 기반 실전 문제 생성
✅ 다음 학습 방향 안내

API 키 발급:
https://makersuite.google.com/app/apikey
        """

        tk.Label(
            self.right_frame,
            text=desc,
            font=("맑은 고딕", 10),
            bg="white",
            justify=tk.LEFT
        ).pack(pady=10)

        # 현재 상태
        status_frame = tk.LabelFrame(
            self.right_frame,
            text="현재 상태",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        status = f"""
Gemini API: {'✅ 활성화' if self.ai_available else '❌ 비활성화'}
필수 패키지: {'✅ 설치됨' if GEMINI_AVAILABLE else '❌ 미설치'}
PDF 읽기: {'✅ 가능' if PDF_AVAILABLE else '❌ 불가능'}
        """

        tk.Label(
            status_frame,
            text=status,
            font=("맑은 고딕", 10),
            bg="white",
            justify=tk.LEFT
        ).pack(padx=10, pady=10)

        # API 키 입력
        key_frame = tk.LabelFrame(
            self.right_frame,
            text="API 키 입력",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        key_frame.pack(fill=tk.X, padx=20, pady=10)

        self.api_key_entry = tk.Entry(
            key_frame,
            font=("맑은 고딕", 10),
            width=60,
            show="*"
        )
        self.api_key_entry.pack(padx=10, pady=10)

        if self.gemini_api_key:
            self.api_key_entry.insert(0, self.gemini_api_key)

        tk.Button(
            key_frame,
            text="💾 저장 및 적용",
            command=self.save_api_key,
            font=("맑은 고딕", 10, "bold"),
            bg="#2ecc71",
            fg="white"
        ).pack(pady=10)

        # 설치 안내
        if not GEMINI_AVAILABLE or not PDF_AVAILABLE:
            install_frame = tk.LabelFrame(
                self.right_frame,
                text="⚠️ 패키지 설치 필요",
                font=("맑은 고딕", 11, "bold"),
                bg="white"
            )
            install_frame.pack(fill=tk.X, padx=20, pady=10)

            tk.Label(
                install_frame,
                text="AI 기능을 사용하려면 필수 패키지를 설치하세요.",
                font=("맑은 고딕", 10),
                bg="white"
            ).pack(pady=5)

            tk.Button(
                install_frame,
                text="📦 설치 프로그램 실행",
                command=lambda: os.system('start 설치.bat'),
                font=("맑은 고딕", 10, "bold"),
                bg="#3498db",
                fg="white"
            ).pack(pady=10)

    def save_api_key(self):
        """API 키 저장"""
        key = self.api_key_entry.get().strip()

        if not key:
            messagebox.showwarning("경고", "API 키를 입력하세요.")
            return

        # 환경변수 설정
        os.environ["GEMINI_API_KEY"] = key
        self.gemini_api_key = key

        # 재초기화
        self.init_systems()

        if self.ai_available:
            messagebox.showinfo("완료", "✅ Gemini API가 활성화되었습니다!\n이제 AI 기능을 사용할 수 있습니다.")
            self.show_welcome()
        else:
            messagebox.showerror("오류", "API 키가 올바르지 않거나 연결에 실패했습니다.")


# ============================================================================
# 메인 실행
# ============================================================================

def main():
    """메인 함수"""
    root = tk.Tk()
    app = OPRSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
