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
                self.model = genai.GenerativeModel('gemini-pro')
                self.available = True
            except Exception as e:
                print(f"Gemini API 초기화 실패: {e}")
                self.available = False
        else:
            self.available = False

    def grade_answer_detailed(
        self,
        student_answer: str,
        model_answer: str,
        keywords: List[str],
        forbidden_words: List[str]
    ) -> Dict:
        """상세한 답안 채점 (AI 기반)"""

        if not self.available:
            return {"error": "Gemini API를 사용할 수 없습니다"}

        prompt = f"""당신은 OPR(논술형 시험) 채점 전문가입니다.

학생 답안을 모범답안과 비교하여 상세하게 채점하고, 구체적인 피드백을 제공하세요.

【채점 기준】
1. 논리·정확성 (40점)
   - 필수 키워드 포함 여부
   - 금지어 사용 시 감점 (1개당 -2점)
   - 내용의 정확성 및 논리성

2. 명확·간결성 (30점)
   - S/A/B/C/D 등급
   - 불필요한 반복, 장황한 표현
   - 35자 제한 준수

3. 완결성 (30점)
   - S/A/B/C/D 등급
   - 보고서 구조 (제목, 1/2/3, □/○/-)
   - 최소 15줄 이상

【필수 키워드】
{', '.join(keywords)}

【금지어】
{', '.join(forbidden_words)}

【모범답안】
{model_answer}

【학생 답안】
{student_answer}

다음 JSON 형식으로 상세하게 답변하세요:
{{
  "총점": 숫자,
  "논리정확성": {{
    "점수": 숫자,
    "매칭된_키워드": ["키워드1", "키워드2"],
    "누락된_키워드": ["키워드3", "키워드4"],
    "발견된_금지어": ["금지어1"],
    "잘한_점": ["구체적인 잘한 점 1", "구체적인 잘한 점 2"],
    "부족한_점": ["구체적인 부족한 점 1"],
    "피드백": "상세 설명"
  }},
  "명확간결성": {{
    "등급": "A",
    "점수": 숫자,
    "잘한_점": ["구체적인 잘한 점"],
    "부족한_점": ["구체적인 부족한 점"],
    "개선_방법": ["구체적인 개선 방법 1", "구체적인 개선 방법 2"],
    "피드백": "상세 설명"
  }},
  "완결성": {{
    "등급": "A",
    "점수": 숫자,
    "잘한_점": ["구체적인 잘한 점"],
    "부족한_점": ["구체적인 부족한 점"],
    "개선_방법": ["구체적인 개선 방법"],
    "피드백": "상세 설명"
  }},
  "종합_평가": {{
    "강점": ["전체적인 강점 1", "전체적인 강점 2"],
    "약점": ["전체적인 약점 1"],
    "보완_방법": ["구체적인 보완 방법 1", "구체적인 보완 방법 2"],
    "다음_학습_방향": "다음에 집중해야 할 학습 내용"
  }}
}}

반드시 JSON만 반환하세요."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text

            # JSON 추출
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            return {"error": f"채점 중 오류: {str(e)}"}

    def generate_exam_from_files(
        self,
        reference_texts: List[str],
        difficulty: str = "medium"
    ) -> Dict:
        """폴더의 자료들로 실전 문제 생성"""

        if not self.available:
            return {"error": "Gemini API를 사용할 수 없습니다"}

        refs_text = "\n\n==========\n\n".join(reference_texts[:5])

        diff_desc = {
            "easy": "쉬움 - 명확한 키워드와 구조",
            "medium": "보통 - 실제 시험 수준",
            "hard": "어려움 - 복잡한 구조와 많은 제시자료"
        }

        prompt = f"""당신은 OPR 문제 출제 전문가입니다.

아래 자료들을 참고하여 실제 OPR 시험과 동일한 형식의 문제를 생성하세요.

【참고 자료】
{refs_text}

【생성 조건】
- 난이도: {diff_desc.get(difficulty, "보통")}
- 실제 OPR 문제 형식 (상황, 과제, 제시자료 등)
- CEO 메시지, 이메일, 메신저 등 다양한 제시자료 포함
- 10개 이상의 제시자료

다음 JSON 형식으로 문제를 생성하세요:
{{
  "제목": "보고서 제목",
  "상황": "배경 상황 설명",
  "과제": "작성해야 할 내용",
  "보고서_구성": ["추진배경", "추진방향", "대응전략", "향후계획"],
  "제시자료": [
    {{
      "번호": 1,
      "유형": "CEO 소통 메시지",
      "내용": "실제 제시자료 내용... (200자 이상)"
    }},
    ...최소 10개
  ],
  "필수_키워드": ["키워드1", "키워드2", ...20개 이상],
  "금지어": ["금지어1", "금지어2"],
  "예상_작성_시간": "150분",
  "출제_의도": "이 문제의 출제 의도"
}}

반드시 JSON만 반환하세요."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text

            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
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

    def grade_answer(self, answer_text: str, keywords: List[str], forbidden: List[str]) -> Dict:
        """기본 채점"""
        normalized_answer = answer_text.replace(' ', '')

        # 키워드 매칭
        matched = []
        missing = []
        for kw in keywords:
            if kw.replace(' ', '') in normalized_answer:
                matched.append(kw)
            else:
                missing.append(kw)

        # 금지어
        found_forbidden = []
        for word in forbidden:
            if word in normalized_answer:
                found_forbidden.append(word)

        # 점수 계산
        logic_score = 40 * (len(matched) / len(keywords)) if keywords else 0
        logic_score = max(0, logic_score - len(found_forbidden) * 2)

        clarity_score = 21.0  # B등급
        completeness_score = 21.0  # B등급
        total = logic_score + clarity_score + completeness_score

        return {
            "총점": round(total, 1),
            "논리정확성": {
                "점수": round(logic_score, 1),
                "매칭된_키워드": matched,
                "누락된_키워드": missing,
                "발견된_금지어": found_forbidden,
                "잘한_점": ["키워드를 일부 포함함"] if matched else [],
                "부족한_점": [f"{len(missing)}개 키워드 누락"] if missing else [],
                "피드백": f"{len(matched)}/{len(keywords)}개 키워드 매칭"
            },
            "명확간결성": {
                "등급": "B",
                "점수": 21.0,
                "피드백": "기본 평가 (AI 미사용)"
            },
            "완결성": {
                "등급": "B",
                "점수": 21.0,
                "피드백": "기본 평가 (AI 미사용)"
            },
            "종합_평가": {
                "강점": ["답안을 작성함"],
                "약점": ["AI 채점을 사용하면 더 정확한 피드백을 받을 수 있습니다"],
                "보완_방법": ["Gemini API 키를 설정하세요"],
                "다음_학습_방향": "키워드 중심 작성 연습"
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
            text="📝 AI 답안 채점 (상세 피드백)",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        # 파일 선택
        file_frame = tk.LabelFrame(
            self.right_frame,
            text="1️⃣ 답안 파일 첨부 (PDF/HWP/TXT)",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        self.answer_file_var = tk.StringVar(value="파일이 선택되지 않았습니다")

        tk.Label(
            file_frame,
            textvariable=self.answer_file_var,
            font=("맑은 고딕", 9),
            bg="white",
            fg="#7f8c8d"
        ).pack(pady=5)

        file_btn_frame = tk.Frame(file_frame, bg="white")
        file_btn_frame.pack(pady=5)

        tk.Button(
            file_btn_frame,
            text="📂 파일 선택",
            command=self.select_answer_file,
            font=("맑은 고딕", 10),
            bg="#3498db",
            fg="white",
            width=20
        ).pack(side=tk.LEFT, padx=5)

        # 직접 입력
        input_frame = tk.LabelFrame(
            self.right_frame,
            text="2️⃣ 또는 직접 입력",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.answer_text = scrolledtext.ScrolledText(
            input_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD,
            height=10
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 버튼
        btn_frame = tk.Frame(self.right_frame, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="📋 샘플",
            command=self.load_sample,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="🗑️ 지우기",
            command=self.clear_answer,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="✅ AI 채점하기",
            command=self.grade_answer_ai,
            font=("맑은 고딕", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            width=20,
            height=2
        ).pack(side=tk.RIGHT, padx=5)

    def select_answer_file(self):
        """파일 선택"""
        filename = filedialog.askopenfilename(
            title="답안 파일 선택",
            filetypes=[
                ("지원 파일", "*.pdf *.txt *.hwp"),
                ("PDF 파일", "*.pdf"),
                ("텍스트 파일", "*.txt"),
                ("한글 파일", "*.hwp"),
                ("모든 파일", "*.*")
            ]
        )

        if filename:
            self.selected_file = filename
            self.answer_file_var.set(f"선택: {os.path.basename(filename)}")

            # 파일 읽기
            content = self.file_reader.read_file(filename)
            self.answer_text.delete("1.0", tk.END)
            self.answer_text.insert("1.0", content)

    def clear_answer(self):
        """답안 지우기"""
        self.answer_text.delete("1.0", tk.END)
        self.answer_file_var.set("파일이 선택되지 않았습니다")
        self.selected_file = None

    def load_sample(self):
        """샘플 답안"""
        sample = """전력망 건설 지연 대응전략 보고서

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

        self.answer_text.delete("1.0", tk.END)
        self.answer_text.insert("1.0", sample)

    def grade_answer_ai(self):
        """AI 채점 실행"""
        answer = self.answer_text.get("1.0", tk.END).strip()

        if not answer:
            messagebox.showwarning("경고", "답안을 입력하거나 파일을 선택하세요.")
            return

        # 진행 창
        progress = tk.Toplevel(self.root)
        progress.title("채점 중...")
        progress.geometry("400x150")
        progress.transient(self.root)
        progress.grab_set()

        tk.Label(
            progress,
            text="🤖 AI가 답안을 채점하고 있습니다...",
            font=("맑은 고딕", 12, "bold"),
            pady=20
        ).pack()

        tk.Label(
            progress,
            text="상세한 피드백을 생성 중입니다.\n잠시만 기다려주세요.",
            font=("맑은 고딕", 10),
            fg="#7f8c8d"
        ).pack()

        progress.update()

        try:
            # 키워드
            keywords = [
                "전력망 건설지연", "발전제약 해소", "법령 제개정", "시공기간 단축",
                "전력망혁신위원회", "전원촉진법", "입지선정위원회", "NWAs",
                "계통안정화용 ESS", "유연송전설비", "WAMS", "동적 송전용량"
            ]
            forbidden = ["HVDC", "디지털 뉴딜", "한국판 뉴딜", "코로나"]

            model_answer = "전력망 건설 지연 대응을 위한 발전제약 해소, 법령 제개정, 시공기간 단축 전략 수립"

            # AI 채점
            if self.ai_available:
                result = self.ai_client.grade_answer_detailed(
                    answer, model_answer, keywords, forbidden
                )
            else:
                result = self.basic_grader.grade_answer(answer, keywords, forbidden)

            progress.destroy()
            self.show_grading_result(result)

        except Exception as e:
            progress.destroy()
            messagebox.showerror("오류", f"채점 중 오류:\n{str(e)}")

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
            text="💾 저장",
            command=lambda: self.save_result(result),
            font=("맑은 고딕", 10),
            bg="#2ecc71",
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
        """문제지 문서 포맷"""
        doc = f"""
================================================================================
OPR 실전 연습 문제 (AI 생성)
================================================================================

【문제】

제목: {exam.get('제목', '')}

1. 보고서 작성배경 및 상황
--------------------------------------------------------------------------------

□ {exam.get('상황', '')}

□ {exam.get('과제', '')}

2. 보고서 작성 및 평가기준
--------------------------------------------------------------------------------

□ 다음 항목으로 구성된 보고서를 작성하시오:
"""
        for item in exam.get('보고서_구성', []):
            doc += f"   - {item}\n"

        doc += """
□ 작성 및 평가 주요기준
  ○ 논리·정확성 (40점): 보고서 전체의 논리가 일관되고 구체적 근거에 의거하여 작성
  ○ 명확·간결성 (30점): 불필요한 정보 없이 핵심내용 위주로 명확·간결하게 작성
  ○ 완결성 (30점): 보고 목적에 부합하는 구성으로 완결된 형식의 보고서를 작성

3. 제시자료
--------------------------------------------------------------------------------
"""

        for mat in exam.get('제시자료', [])[:10]:  # 최대 10개만
            doc += f"\n【제시자료 {mat.get('번호', '')}】 {mat.get('유형', '')}\n\n"
            doc += f"{mat.get('내용', '')}\n\n"
            doc += "-"*80 + "\n"

        doc += f"""
【참고】 필수 키워드
--------------------------------------------------------------------------------
"""
        for i, kw in enumerate(exam.get('필수_키워드', []), 1):
            doc += f"  {i}. {kw}\n"

        doc += f"""
【주의】 금지어
--------------------------------------------------------------------------------
"""
        for word in exam.get('금지어', []):
            doc += f"  ⚠️ {word}\n"

        doc += f"""
================================================================================
예상 작성 시간: {exam.get('예상_작성_시간', '')}
출제 의도: {exam.get('출제_의도', '')}
================================================================================
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
