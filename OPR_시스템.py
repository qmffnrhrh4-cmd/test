#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 자동 채점 시스템 통합 버전
모든 기능이 하나의 파일에 통합됨
추가 패키지 설치 불필요 (Python 기본 라이브러리만 사용)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import re
import random
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass


# ============================================================================
# 자동 채점 시스템
# ============================================================================

@dataclass
class GradingCriteria:
    """채점 기준"""
    required_keywords: List[str]
    forbidden_keywords: List[str]
    max_logic_score: int = 40
    max_clarity_score: int = 30
    max_completeness_score: int = 30


@dataclass
class GradingResult:
    """채점 결과"""
    logic_score: float
    clarity_score: str
    completeness_score: str
    total_score: float
    feedback: List[str]
    keyword_matches: Dict[str, int]
    forbidden_found: List[str]


class AutoGradingSystem:
    """자동 채점 시스템"""

    def __init__(self):
        self.grade_to_score = {
            'S': 1.0, 'A': 0.85, 'B': 0.70, 'C': 0.55, 'D': 0.40
        }

    def calculate_logic_score(
        self, answer_text: str, criteria: GradingCriteria
    ) -> Tuple[float, Dict[str, int], List[str]]:
        """논리·정확성 점수 계산"""
        normalized_answer = answer_text.replace(' ', '')

        keyword_matches = {}
        for keyword in criteria.required_keywords:
            normalized_keyword = keyword.replace(' ', '')
            count = normalized_answer.count(normalized_keyword)
            if count > 0:
                keyword_matches[keyword] = count

        forbidden_found = []
        for forbidden in criteria.forbidden_keywords:
            normalized_forbidden = forbidden.replace(' ', '')
            if normalized_forbidden in normalized_answer:
                forbidden_found.append(forbidden)

        match_rate = len(keyword_matches) / len(criteria.required_keywords) if criteria.required_keywords else 0
        base_score = criteria.max_logic_score * match_rate
        penalty = len(forbidden_found) * 2
        final_score = max(0, base_score - penalty)

        return final_score, keyword_matches, forbidden_found

    def evaluate_clarity(self, answer_text: str) -> Tuple[str, List[str]]:
        """명확·간결성 평가"""
        feedback = []
        score = 85

        repeated_words = self._check_repetition(answer_text)
        if repeated_words:
            score -= 10
            feedback.append(f"반복되는 단어 발견: {', '.join(repeated_words[:3])}")

        lines = answer_text.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line.replace(' ', '')) > 35]
        if long_lines:
            score -= 5
            feedback.append(f"35자 초과 줄: {long_lines[:3]}")

        if self._is_keyword_listing(answer_text):
            score -= 10
            feedback.append("단순 키워드 나열식 작성으로 보임")

        if score >= 90: grade = 'S'
        elif score >= 80: grade = 'A'
        elif score >= 70: grade = 'B'
        elif score >= 60: grade = 'C'
        else: grade = 'D'

        return grade, feedback

    def evaluate_completeness(self, answer_text: str) -> Tuple[str, List[str]]:
        """완결성 평가"""
        feedback = []
        score = 85

        has_title = bool(re.search(r'^.{1,21}$', answer_text.split('\n')[0]))
        has_sections = len(re.findall(r'^[1-9]\.', answer_text, re.MULTILINE)) > 0
        has_subsections = len(re.findall(r'^□', answer_text, re.MULTILINE)) > 0

        if not has_title:
            score -= 5
            feedback.append("제목이 명확하지 않음")
        if not has_sections:
            score -= 10
            feedback.append("대항목(1, 2, 3) 구조 없음")
        if not has_subsections:
            score -= 5
            feedback.append("중항목(□) 구조 부족")

        lines = [l for l in answer_text.split('\n') if l.strip()]
        if len(lines) < 15:
            score -= 10
            feedback.append(f"내용이 부족함 (총 {len(lines)}줄)")

        if score >= 90: grade = 'S'
        elif score >= 80: grade = 'A'
        elif score >= 70: grade = 'B'
        elif score >= 60: grade = 'C'
        else: grade = 'D'

        return grade, feedback

    def _check_repetition(self, text: str) -> List[str]:
        """반복되는 단어 체크"""
        words = re.findall(r'[\w]{2,}', text)
        word_count = {}
        for word in words:
            if len(word) >= 2:
                word_count[word] = word_count.get(word, 0) + 1
        repeated = [w for w, c in word_count.items() if c >= 5]
        return repeated

    def _is_keyword_listing(self, text: str) -> bool:
        """키워드 나열식인지 체크"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        short_lines = [l for l in lines if len(l) < 15]
        return len(short_lines) / len(lines) > 0.5 if lines else False

    def grade_answer(self, answer_text: str, criteria: GradingCriteria) -> GradingResult:
        """답안 채점"""
        logic_score, keyword_matches, forbidden_found = self.calculate_logic_score(
            answer_text, criteria
        )
        clarity_grade, clarity_feedback = self.evaluate_clarity(answer_text)
        completeness_grade, completeness_feedback = self.evaluate_completeness(answer_text)

        clarity_score = criteria.max_clarity_score * self.grade_to_score[clarity_grade]
        completeness_score = criteria.max_completeness_score * self.grade_to_score[completeness_grade]
        total_score = logic_score + clarity_score + completeness_score

        feedback = []
        feedback.append(f"=== 논리·정확성 ({logic_score:.1f}/{criteria.max_logic_score}점) ===")
        feedback.append(f"키워드 매칭: {len(keyword_matches)}/{len(criteria.required_keywords)}개")
        if keyword_matches:
            feedback.append(f"  - 발견된 키워드: {', '.join(list(keyword_matches.keys())[:10])}")
        if forbidden_found:
            feedback.append(f"  ⚠️ 금지어 발견 (-{len(forbidden_found)*2}점): {', '.join(forbidden_found)}")

        feedback.append(f"\n=== 명확·간결성 ({clarity_grade}등급, {clarity_score:.1f}/{criteria.max_clarity_score}점) ===")
        feedback.extend(clarity_feedback)

        feedback.append(f"\n=== 완결성 ({completeness_grade}등급, {completeness_score:.1f}/{criteria.max_completeness_score}점) ===")
        feedback.extend(completeness_feedback)

        feedback.append(f"\n{'='*50}")
        feedback.append(f"📊 총점: {total_score:.1f}/100점")

        return GradingResult(
            logic_score=logic_score,
            clarity_score=clarity_grade,
            completeness_score=completeness_grade,
            total_score=total_score,
            feedback=feedback,
            keyword_matches=keyword_matches,
            forbidden_found=forbidden_found
        )


# ============================================================================
# 문제 생성기
# ============================================================================

class ExamGenerator:
    """문제 생성기"""

    def __init__(self):
        self.topics = {
            "easy": {
                "제목": "디지털 전환 가속화 대응전략",
                "상황": "4차 산업혁명 시대 대응을 위한 디지털 전환 필요성 증대",
                "키워드": ["디지털전환", "AI활용", "데이터분석", "자동화", "업무혁신", "시스템구축"]
            },
            "medium": {
                "제목": "탄소중립 달성을 위한 추진전략",
                "상황": "2050 탄소중립 목표 달성을 위한 구체적 실행방안 마련 필요",
                "키워드": ["탄소중립", "온실가스감축", "재생에너지", "ESG경영", "친환경기술", "배출권거래"]
            },
            "hard": {
                "제목": "전력시장 개편 대응방안",
                "상황": "전력시장 구조 개편에 따른 회사 차원의 대응 전략 수립 필요",
                "키워드": ["전력시장개편", "경쟁체제", "수익성개선", "사업다각화", "신사업발굴", "리스크관리"]
            }
        }

    def generate_exam(self, difficulty: str = "medium") -> Dict:
        """연습 문제 생성"""
        selected = self.topics.get(difficulty, self.topics["medium"])

        exam = {
            "제목": selected["제목"],
            "상황": selected["상황"],
            "키워드": selected["키워드"],
            "금지어": ["디지털 뉴딜", "한국판 뉴딜", "코로나", "재택근무"],
            "난이도": difficulty,
            "예상시간": "150분"
        }

        return exam

    def format_exam_document(self, exam_data: Dict) -> str:
        """문제지 문서 생성"""
        doc = f"""
================================================================================
OPR 자동 생성 연습 문제
================================================================================

【문제】

제목: {exam_data['제목']}

1. 보고서 작성배경 및 상황
--------------------------------------------------------------------------------

□ {exam_data['상황']}

□ 귀하는 'A기업' 관련 부서의 차장이며, 해당 주제에 대한 보고서를
  작성하여 사장에게 보고해야 하는 상황입니다.

2. 보고서 작성 및 평가기준
--------------------------------------------------------------------------------

□ 다음 항목으로 구성된 보고서를 작성하시오:
  - 추진배경
  - 추진방향
  - 대응전략
  - 향후계획

□ 작성 및 평가 주요기준
  ○ 논리·정확성 (40점): 보고서 전체의 논리가 일관되고 구체적 근거에 의거하여 작성
  ○ 명확·간결성 (30점): 불필요한 정보 없이 핵심내용 위주로 명확·간결하게 작성
  ○ 완결성 (30점): 보고 목적에 부합하는 구성으로 완결된 형식의 보고서를 작성

3. 작성 유의사항
--------------------------------------------------------------------------------

□ 배점 (총 100점 만점)

  항 목      | 논리·정확성 | 명확·간결성 | 완결성 | 합 계
  ----------|------------|-----------|--------|-------
  배 점      |     40     |     30    |   30   | 100점

□ 작성 유의사항
  ○ 총 26줄 이내의 개조식으로 작성
  ○ 글자체 및 글자크기
    - 제 목: HY헤드라인M, 21포인트, 최대 21자
    - 본 문: 신명조, 13포인트, 최대 35자(순수 글자수)

【참고】 필수 키워드 (채점 기준)
--------------------------------------------------------------------------------
"""
        for i, kw in enumerate(exam_data['키워드'], 1):
            doc += f"  {i}. {kw}\n"

        doc += f"""
【주의】 금지어 (사용 시 감점)
--------------------------------------------------------------------------------
"""
        for word in exam_data['금지어']:
            doc += f"  ⚠️ {word}\n"

        doc += f"""
================================================================================
예상 작성 시간: {exam_data['예상시간']}
난이도: {exam_data['난이도'].upper()}
================================================================================
"""
        return doc


# ============================================================================
# 공부 가이드
# ============================================================================

class StudyGuide:
    """공부 가이드"""

    def __init__(self):
        self.tips = [
            {
                "제목": "제시문의 단어를 그대로 사용하라",
                "설명": "모든 단어는 문제지에 있는 단어만 쓰고, 있는 그대로 작성하는 게 중요합니다.",
                "예시": [
                    "❌ 온실가스 억제 → ✅ 온실가스 저감",
                    "❌ 친환경 기술수준 부족 → ✅ 친환경 기술수준 미흡"
                ]
            },
            {
                "제목": "키워드를 최대한 많이 넣어라",
                "설명": "채점자는 200명 답안을 빠르게 채점하므로, 키워드 중심으로 채점합니다.",
                "예시": [
                    "정 모르겠으면 관련 키워드를 최대한 많이 작성",
                    "문제 지문에서 중요해 보이는 단어는 모두 포함"
                ]
            },
            {
                "제목": "시험지 받으면 먼저 제목, 대제목 작성",
                "설명": "문제에서 제목, 대제목 등 틀을 잡고 시작합니다.",
                "예시": [
                    "1단계: 제목, 대제목 먼저 써놓기",
                    "2단계: 읽으면서 채워나가기"
                ]
            },
            {
                "제목": "CEO 메시지에서 추진배경과 향후 일정 추출",
                "설명": "CEO 메시지는 주로 추진배경과 향후 일정을 언급합니다.",
                "예시": [
                    "CEO가 '~를 하자' → 무조건 향후 계획",
                    "전사 행사, 토론회 등 → 향후 계획"
                ]
            },
            {
                "제목": "부장과 컴케에서 보고서 틀 확인",
                "설명": "보통 2, 3번 보고서 틀이 잡히고, 주의사항도 언급됩니다.",
                "예시": [
                    "부장: '추진방향은 A, B, C로 구분해서 작성하세요'",
                    "→ 이것까지 잡아놓고 시작!"
                ]
            }
        ]

    def get_study_plan(self) -> str:
        """4주 학습 계획"""
        return """
【4주 학습 계획】

▶ 1주차: 채점 방식 이해 및 기출문제 분석
  활동:
    • 채점 방식 이해하기
    • 기출문제 3개년 분석 (구조 파악)
    • 모범답안 패턴 분석
  ✓ 체크포인트: 채점 기준 3가지를 말할 수 있는가?

▶ 2주차: 키워드 추출 연습 및 문제 분석 훈련
  활동:
    • 문제지에서 키워드 추출 연습
    • 제시자료 유형별 특징 파악
    • 기출문제 1개 시간제한 없이 작성
  ✓ 체크포인트: 제시자료에서 키워드를 빠르게 찾을 수 있는가?

▶ 3주차: 실전 연습 및 시간 관리
  활동:
    • 기출문제 2개 실전 연습 (150분)
    • 작성 후 스스로 채점
    • 자신만의 루틴 확립
  ✓ 체크포인트: 150분 내에 26줄 답안을 완성할 수 있는가?

▶ 4주차: 최종 점검 및 실전 감각 유지
  활동:
    • 기출문제 2~3개 추가 연습
    • 약점 파트 집중 훈련
    • 최신 산업 이슈 확인
  ✓ 체크포인트: 모범답안에 가까운 답안을 작성할 수 있는가?
"""

    def get_checklist(self) -> List[str]:
        """시험 당일 체크리스트"""
        return [
            "문제지 받으면 제목과 대제목을 먼저 작성",
            "CEO 메시지에서 추진배경과 향후 일정 체크",
            "처장/부장 이메일에서 보고서 구조 확인",
            "제시자료를 읽으며 키워드에 형광펜 표시",
            "모든 키워드를 문제지에 있는 단어 그대로 사용",
            "금지어를 사용하지 않았는지 확인",
            "각 줄이 35자를 초과하지 않는지 확인",
            "총 26줄 이내로 작성",
            "보고서 구조가 명확한지 확인 (1,2,3 → □ → ○ → -)",
            "CEO 중심의 향후 일정 작성",
            "단순 키워드 나열이 아닌 논리적 문장",
            "제목은 21자 이내"
        ]


# ============================================================================
# 통합 GUI
# ============================================================================

class OPRSystemGUI:
    """OPR 시스템 통합 GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("📚 OPR 자동 채점 시스템 (통합 버전)")
        self.root.geometry("1200x800")

        # 시스템 초기화
        self.grader = AutoGradingSystem()
        self.exam_gen = ExamGenerator()
        self.study_guide = StudyGuide()

        # UI 생성
        self.create_widgets()

    def create_widgets(self):
        """UI 구성"""
        # 상단 제목
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=100)
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(
            title_frame,
            text="📚 OPR 자동 채점 시스템",
            font=("맑은 고딕", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)

        subtitle_label = tk.Label(
            title_frame,
            text="자동 채점 • 문제 생성 • 공부 가이드",
            font=("맑은 고딕", 11),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        subtitle_label.pack()

        # 메인 컨테이너
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 왼쪽: 메뉴
        left_frame = tk.Frame(main_container, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        menu_label = tk.Label(
            left_frame,
            text="🎯 메뉴",
            font=("맑은 고딕", 16, "bold")
        )
        menu_label.pack(pady=(0, 20))

        buttons = [
            ("📝 답안 자동 채점", self.show_grading_panel, "#3498db"),
            ("📄 연습 문제 생성", self.show_exam_panel, "#2ecc71"),
            ("📚 공부 노하우", self.show_study_guide, "#e74c3c"),
            ("📅 학습 계획", self.show_study_plan, "#f39c12"),
            ("✅ 체크리스트", self.show_checklist, "#9b59b6"),
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

        # 오른쪽: 작업 패널
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

        welcome_text = """

🎓 OPR 자동 채점 시스템에 오신 것을 환영합니다!

왼쪽 메뉴에서 원하는 기능을 선택하세요.


【주요 기능】

📝 답안 자동 채점
   - 작성한 답안을 자동으로 채점
   - 키워드 매칭 및 금지어 검사
   - 상세한 피드백 제공

📄 연습 문제 생성
   - 새로운 연습 문제 생성
   - 난이도별 선택 가능

📚 공부 노하우
   - 채점 방식 및 작성 전략
   - 고득점 비법

📅 학습 계획
   - 4주 단계별 학습 계획

✅ 체크리스트
   - 시험 당일 확인사항
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
            text="📝 답안 자동 채점",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        input_frame = tk.LabelFrame(
            self.right_frame,
            text="답안 입력",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.answer_text = scrolledtext.ScrolledText(
            input_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD,
            height=15
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(self.right_frame, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        load_btn = tk.Button(
            btn_frame,
            text="📂 파일 불러오기",
            command=self.load_answer_file,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        )
        load_btn.pack(side=tk.LEFT, padx=5)

        sample_btn = tk.Button(
            btn_frame,
            text="📋 샘플 답안",
            command=self.load_sample_answer,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        )
        sample_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(
            btn_frame,
            text="🗑️ 지우기",
            command=lambda: self.answer_text.delete("1.0", tk.END),
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        grade_btn = tk.Button(
            btn_frame,
            text="✅ 채점하기",
            command=self.grade_answer,
            font=("맑은 고딕", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            width=15,
            height=2
        )
        grade_btn.pack(side=tk.RIGHT, padx=5)

    def load_answer_file(self):
        """파일에서 답안 불러오기"""
        filename = filedialog.askopenfilename(
            title="답안 파일 선택",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.answer_text.delete("1.0", tk.END)
                self.answer_text.insert("1.0", content)
                messagebox.showinfo("성공", "파일을 불러왔습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"파일 읽기 오류: {e}")

    def load_sample_answer(self):
        """샘플 답안 불러오기"""
        sample = """전력망 건설 지연 대응전략 보고서

1. 추진배경
□ 첨단산업 전력수요 증가 및 재생e 발전 확산으로 전력망 역할 증대
○ 반도체 등 첨단산업단지 대용량 전력공급 인프라 구축 필요
○ 재생e 계통연계 지연으로 발전제약 해소 시급(최대 6.5GW)
□ 인허가 지연 등으로 송전선로 건설 평균 5년 지연
○ 지연사유: 인허가 48%, 입지선정 25%, 시공여건 17%

2. 추진방향
□ 발전제약 해소를 통한 안정적 전력공급 실현
□ 법령 제개정으로 인허가 절차 개선 및 갈등 해소
□ 시공기간 단축을 위한 신기술 및 해외인력 활용

3. 대응전략
□ 단기(~'27년)
○ (발전제약 해소) NWAs 기술 적용으로 송전능력 2.6GW 확보
 - 계통안정화용 ESS 설치, 유연송전설비 9개소 적용
○ (발전제약 해소) 고객참여 부하차단 제도 도입(1.0GW 확보)
○ (법령 제개정) 전원촉진법 개정으로 입지선정위원회 법제화('26.1)
□ 중장기('28년~)
○ (발전제약 해소) WAMS 본격 적용으로 전력망 운영 안정성 제고('28)
○ (발전제약 해소) 동적 송전용량 산정 기술 계통 적용('29)
○ (법령 제개정) 전력망혁신법 제정으로 혁신위원회 설치('26.1)
○ (시공기간 단축) 신규 터널 굴착장비 도입 유도(품셈 개정, '28)
○ (시공기간 단축) 해외인력 확보를 위한 비자제도 개선('28)

4. 향후계획
□ 전력망 적기 건설을 위한 전사 다짐대회 개최: 12월 16일
□ 산업부 전력망 건설 지연 대응전략 산업부·국회 대상 CEO 보고: 12월 30일"""

        self.answer_text.delete("1.0", tk.END)
        self.answer_text.insert("1.0", sample)
        messagebox.showinfo("완료", "샘플 답안을 불러왔습니다.")

    def grade_answer(self):
        """답안 채점"""
        answer = self.answer_text.get("1.0", tk.END).strip()

        if not answer:
            messagebox.showwarning("경고", "답안을 입력해주세요.")
            return

        keywords = [
            "전력망 건설지연", "발전제약 해소", "법령 제개정", "시공기간 단축",
            "전력망혁신위원회", "전원촉진법", "입지선정위원회", "협의간주제",
            "NWAs", "계통안정화용 ESS", "유연송전설비", "고객참여 부하차단",
            "WAMS", "동적 송전용량", "신규 장비 도입", "해외인력 확보"
        ]
        forbidden = ["HVDC", "디지털 뉴딜", "한국판 뉴딜", "코로나", "재택근무"]

        criteria = GradingCriteria(
            required_keywords=keywords,
            forbidden_keywords=forbidden
        )

        result = self.grader.grade_answer(answer, criteria)
        self.show_grading_result(result)

    def show_grading_result(self, result):
        """채점 결과 표시"""
        result_window = tk.Toplevel(self.root)
        result_window.title("📊 채점 결과")
        result_window.geometry("800x700")

        title = tk.Label(
            result_window,
            text="📊 채점 결과",
            font=("맑은 고딕", 18, "bold"),
            bg="#3498db",
            fg="white",
            pady=15
        )
        title.pack(fill=tk.X)

        score_frame = tk.Frame(result_window, bg="#ecf0f1", pady=20)
        score_frame.pack(fill=tk.X)

        score_label = tk.Label(
            score_frame,
            text=f"총점: {result.total_score:.1f} / 100점",
            font=("맑은 고딕", 28, "bold"),
            bg="#ecf0f1",
            fg="#e74c3c"
        )
        score_label.pack()

        detail_frame = tk.Frame(result_window)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        detail_text = scrolledtext.ScrolledText(
            detail_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        detail_text.pack(fill=tk.BOTH, expand=True)
        detail_text.insert("1.0", "\n".join(result.feedback))
        detail_text.config(state=tk.DISABLED)

        btn_frame = tk.Frame(result_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        save_btn = tk.Button(
            btn_frame,
            text="💾 결과 저장",
            command=lambda: self.save_result(result),
            font=("맑은 고딕", 10),
            bg="#2ecc71",
            fg="white"
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(
            btn_frame,
            text="닫기",
            command=result_window.destroy,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

    def save_result(self, result):
        """결과 저장"""
        filename = filedialog.asksaveasfilename(
            title="채점 결과 저장",
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("JSON 파일", "*.json")]
        )

        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump({
                            "총점": result.total_score,
                            "논리정확성": result.logic_score,
                            "명확간결성": result.clarity_score,
                            "완결성": result.completeness_score,
                            "피드백": result.feedback
                        }, f, ensure_ascii=False, indent=2)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write("\n".join(result.feedback))

                messagebox.showinfo("저장 완료", f"결과가 저장되었습니다:\n{filename}")
            except Exception as e:
                messagebox.showerror("저장 오류", f"저장 중 오류: {e}")

    def show_exam_panel(self):
        """문제 생성 패널"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="📄 연습 문제 생성",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        settings_frame = tk.LabelFrame(
            self.right_frame,
            text="문제 설정",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        settings_frame.pack(fill=tk.X, padx=10, pady=15)

        diff_frame = tk.Frame(settings_frame, bg="white")
        diff_frame.pack(pady=10)

        tk.Label(
            diff_frame,
            text="난이도:",
            font=("맑은 고딕", 10, "bold"),
            bg="white"
        ).pack(side=tk.LEFT, padx=5)

        self.difficulty_var = tk.StringVar(value="medium")

        for text, value in [("쉬움", "easy"), ("보통", "medium"), ("어려움", "hard")]:
            rb = tk.Radiobutton(
                diff_frame,
                text=text,
                variable=self.difficulty_var,
                value=value,
                font=("맑은 고딕", 10),
                bg="white"
            )
            rb.pack(side=tk.LEFT, padx=10)

        generate_btn = tk.Button(
            self.right_frame,
            text="✨ 문제 생성하기",
            command=self.generate_exam,
            font=("맑은 고딕", 12, "bold"),
            bg="#2ecc71",
            fg="white",
            height=2
        )
        generate_btn.pack(pady=15)

        self.exam_result_frame = tk.LabelFrame(
            self.right_frame,
            text="생성된 문제",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        self.exam_result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.exam_result_text = scrolledtext.ScrolledText(
            self.exam_result_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        self.exam_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def generate_exam(self):
        """문제 생성"""
        difficulty = self.difficulty_var.get()
        exam_data = self.exam_gen.generate_exam(difficulty)

        self.exam_result_text.delete("1.0", tk.END)

        info = f"""✅ 문제 생성 완료!

📌 제목: {exam_data['제목']}
📝 상황: {exam_data['상황']}
🔑 필수 키워드: {len(exam_data['키워드'])}개
⏱️ 예상 시간: {exam_data['예상시간']}

필수 키워드:
"""
        for i, kw in enumerate(exam_data['키워드'], 1):
            info += f"  {i}. {kw}\n"

        self.exam_result_text.insert("1.0", info)
        self.current_exam_data = exam_data

        save_btn = tk.Button(
            self.exam_result_frame,
            text="💾 전체 문제지 파일로 저장",
            command=self.save_exam,
            font=("맑은 고딕", 10, "bold"),
            bg="#3498db",
            fg="white"
        )
        save_btn.pack(pady=5)

    def save_exam(self):
        """문제 저장"""
        if not hasattr(self, 'current_exam_data'):
            messagebox.showwarning("경고", "생성된 문제가 없습니다.")
            return

        filename = filedialog.asksaveasfilename(
            title="문제지 저장",
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt")]
        )

        if filename:
            try:
                full_doc = self.exam_gen.format_exam_document(self.current_exam_data)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_doc)
                messagebox.showinfo("저장 완료", f"문제지가 저장되었습니다:\n{filename}")
            except Exception as e:
                messagebox.showerror("저장 오류", f"저장 중 오류: {e}")

    def show_study_guide(self):
        """공부 가이드 표시"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="📚 공부 노하우 (핵심 전략)",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        guide_frame = tk.Frame(self.right_frame, bg="white")
        guide_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        guide_text = scrolledtext.ScrolledText(
            guide_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        guide_text.pack(fill=tk.BOTH, expand=True)

        content = "\n【핵심 전략 TOP 5】\n\n"
        for i, tip in enumerate(self.study_guide.tips, 1):
            content += f"🎯 {i}. {tip['제목']}\n"
            content += f"   {tip['설명']}\n"
            content += f"   예시:\n"
            for ex in tip['예시']:
                content += f"     • {ex}\n"
            content += "\n"

        guide_text.insert("1.0", content)
        guide_text.config(state=tk.DISABLED)

    def show_study_plan(self):
        """학습 계획 표시"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="📅 4주 학습 계획",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        plan_text = scrolledtext.ScrolledText(
            self.right_frame,
            font=("맑은 고딕", 11),
            wrap=tk.WORD
        )
        plan_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        plan_text.insert("1.0", self.study_guide.get_study_plan())
        plan_text.config(state=tk.DISABLED)

    def show_checklist(self):
        """체크리스트 표시"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="✅ 시험 당일 체크리스트",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        checklist_frame = tk.Frame(self.right_frame, bg="white")
        checklist_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for item in self.study_guide.get_checklist():
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                checklist_frame,
                text=item,
                variable=var,
                font=("맑은 고딕", 11),
                bg="white",
                anchor=tk.W
            )
            cb.pack(fill=tk.X, pady=3)


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
