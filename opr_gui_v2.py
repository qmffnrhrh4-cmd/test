#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 자동 채점 시스템 GUI V2
Claude API 기반 스마트 채점/문제생성/가이드
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import json
from typing import Optional

# V2 시스템 임포트
try:
    from auto_grading_system_v2 import AutoGradingSystemV2
    from exam_generator_v2 import ExamGeneratorV2
    from study_guide_v2 import StudyGuideSystemV2
    V2_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ V2 시스템 로드 실패: {e}")
    print("기본 시스템을 사용합니다.")
    from auto_grading_system import AutoGradingSystem, GradingCriteria
    from exam_generator import ExamGenerator
    from study_guide import StudyGuideSystem
    V2_AVAILABLE = False


class OPRSystemGUIV2:
    """OPR 시스템 GUI V2"""

    def __init__(self, root):
        self.root = root
        self.root.title("📚 OPR 자동 채점 시스템 V2 (AI 기반)")
        self.root.geometry("1200x800")

        # API 키 설정
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        # 시스템 초기화
        self.init_systems()

        # UI 생성
        self.create_widgets()

    def init_systems(self):
        """시스템 초기화"""
        try:
            if V2_AVAILABLE:
                self.grader = AutoGradingSystemV2(self.api_key)
                self.exam_gen = ExamGeneratorV2(self.api_key)
                self.study_guide = StudyGuideSystemV2(self.api_key)
                self.version = "V2 (Claude API)"
            else:
                self.grader = AutoGradingSystem()
                self.exam_gen = ExamGenerator()
                self.study_guide = StudyGuideSystem()
                self.version = "V1 (기본)"

            print(f"✅ 시스템 초기화 완료: {self.version}")

        except Exception as e:
            messagebox.showerror("초기화 오류", f"시스템 초기화 실패:\n{e}")
            self.grader = None
            self.exam_gen = None
            self.study_guide = None
            self.version = "오류"

    def create_widgets(self):
        """UI 구성"""

        # 상단 제목
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=100)
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(
            title_frame,
            text=f"📚 OPR 자동 채점 시스템 {self.version}",
            font=("맑은 고딕", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)

        subtitle_label = tk.Label(
            title_frame,
            text="모범답안 비교, 실제 문제 생성, PDF 기반 가이드",
            font=("맑은 고딕", 11),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        subtitle_label.pack()

        # 메인 컨테이너
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 왼쪽: 메뉴 버튼들
        left_frame = tk.Frame(main_container, width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        menu_label = tk.Label(
            left_frame,
            text="🎯 메뉴 선택",
            font=("맑은 고딕", 16, "bold")
        )
        menu_label.pack(pady=(0, 20))

        # 메뉴 버튼들
        buttons = [
            ("📝 답안 자동 채점 (파일 첨부)", self.show_grading_panel, "#3498db"),
            ("📄 연습 문제 생성 (AI)", self.show_exam_panel, "#2ecc71"),
            ("📚 공부 노하우 (PDF 분석)", self.show_study_guide, "#e74c3c"),
            ("📅 학습 계획 생성", self.show_study_plan, "#f39c12"),
            ("✅ 체크리스트", self.show_checklist, "#9b59b6"),
            ("⚙️ API 키 설정", self.show_api_settings, "#34495e"),
        ]

        for text, command, color in buttons:
            btn = tk.Button(
                left_frame,
                text=text,
                command=command,
                font=("맑은 고딕", 11, "bold"),
                bg=color,
                fg="white",
                activebackground=color,
                activeforeground="white",
                relief=tk.RAISED,
                bd=3,
                cursor="hand2",
                height=2,
                wraplength=250
            )
            btn.pack(fill=tk.X, pady=5)

        # 종료 버튼
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

        # 초기 화면
        self.show_welcome()

    def clear_panel(self):
        """패널 초기화"""
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    def show_welcome(self):
        """환영 화면"""
        self.clear_panel()

        welcome_text = f"""

🎓 OPR 자동 채점 시스템 V2에 오신 것을 환영합니다!

현재 버전: {self.version}

{'✅ Claude API가 활성화되어 있습니다!' if V2_AVAILABLE and self.api_key else '⚠️ Claude API 키를 설정하면 더 정확한 기능을 사용할 수 있습니다.'}

왼쪽 메뉴에서 원하는 기능을 선택하세요.


【주요 기능】

📝 답안 자동 채점
   - 텍스트/PDF 파일 첨부 가능
   - 모범답안과 비교하여 정확하게 채점
   - AI 기반 상세 피드백 제공

📄 연습 문제 생성
   - 실제 기출문제 분석
   - AI가 유사한 형식으로 문제 생성
   - 파일로 저장 가능

📚 공부 노하우
   - PDF 문서 (채점 방식, 작성 팁) 분석
   - AI 기반 학습 전략 제공
   - 개인 맞춤형 가이드

📅 학습 계획 생성
   - 4주 단계별 학습 계획
   - 체계적인 준비 로드맵

✅ 체크리스트
   - 시험 당일 확인사항
   - 12가지 체크포인트
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

        # 제목
        title = tk.Label(
            self.right_frame,
            text="📝 답안 자동 채점 (파일 첨부 가능)",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        # 파일 선택 영역
        file_frame = tk.LabelFrame(
            self.right_frame,
            text="1️⃣ 답안 파일 선택",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        self.answer_file_var = tk.StringVar(value="파일이 선택되지 않았습니다")

        file_info = tk.Label(
            file_frame,
            textvariable=self.answer_file_var,
            font=("맑은 고딕", 9),
            bg="white",
            fg="#7f8c8d"
        )
        file_info.pack(pady=5)

        file_btn_frame = tk.Frame(file_frame, bg="white")
        file_btn_frame.pack(pady=5)

        select_file_btn = tk.Button(
            file_btn_frame,
            text="📂 파일 선택 (TXT/PDF)",
            command=self.select_answer_file,
            font=("맑은 고딕", 10),
            bg="#3498db",
            fg="white",
            width=20
        )
        select_file_btn.pack(side=tk.LEFT, padx=5)

        # 또는 직접 입력
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
            height=12
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 버튼 영역
        btn_frame = tk.Frame(self.right_frame, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

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
            command=self.clear_answer,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        grade_btn = tk.Button(
            btn_frame,
            text="✅ AI 채점하기",
            command=self.grade_answer_v2,
            font=("맑은 고딕", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            width=20,
            height=2
        )
        grade_btn.pack(side=tk.RIGHT, padx=5)

    def select_answer_file(self):
        """답안 파일 선택"""
        filename = filedialog.askopenfilename(
            title="답안 파일 선택",
            filetypes=[
                ("모든 지원 파일", "*.txt *.pdf"),
                ("텍스트 파일", "*.txt"),
                ("PDF 파일", "*.pdf"),
                ("모든 파일", "*.*")
            ]
        )

        if filename:
            self.answer_file_var.set(f"선택된 파일: {os.path.basename(filename)}")
            self.selected_answer_file = filename

            # 텍스트 파일이면 내용도 표시
            if filename.endswith('.txt'):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.answer_text.delete("1.0", tk.END)
                    self.answer_text.insert("1.0", content)
                except Exception as e:
                    messagebox.showerror("오류", f"파일 읽기 오류: {e}")

    def clear_answer(self):
        """답안 지우기"""
        self.answer_text.delete("1.0", tk.END)
        self.answer_file_var.set("파일이 선택되지 않았습니다")
        self.selected_answer_file = None

    def load_sample_answer(self):
        """샘플 답안 로드"""
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

    def grade_answer_v2(self):
        """V2 채점 실행"""
        if not self.grader:
            messagebox.showerror("오류", "채점 시스템이 초기화되지 않았습니다.")
            return

        # 답안 가져오기
        answer_text = self.answer_text.get("1.0", tk.END).strip()

        if not answer_text and not hasattr(self, 'selected_answer_file'):
            messagebox.showwarning("경고", "답안을 입력하거나 파일을 선택해주세요.")
            return

        try:
            # 진행 표시
            progress_win = tk.Toplevel(self.root)
            progress_win.title("채점 중...")
            progress_win.geometry("400x150")
            progress_win.transient(self.root)
            progress_win.grab_set()

            tk.Label(
                progress_win,
                text="🤖 AI가 답안을 채점하고 있습니다...",
                font=("맑은 고딕", 12, "bold"),
                pady=20
            ).pack()

            tk.Label(
                progress_win,
                text="모범답안과 비교하여 정확하게 분석 중\n잠시만 기다려주세요.",
                font=("맑은 고딕", 10),
                fg="#7f8c8d"
            ).pack()

            progress_win.update()

            # V2 채점
            if V2_AVAILABLE and hasattr(self, 'selected_answer_file'):
                # 파일로 채점
                result = self.grader.grade_from_file(self.selected_answer_file)
            elif V2_AVAILABLE:
                # 텍스트로 채점
                result = self.grader.grade_with_model_answer(answer_text)
            else:
                # V1 채점 (폴백)
                keywords = [
                    "전력망 건설지연", "발전제약 해소", "법령 제개정", "시공기간 단축",
                    "전력망혁신위원회", "전원촉진법", "입지선정위원회", "NWAs",
                    "계통안정화용 ESS", "유연송전설비", "고객참여 부하차단",
                    "WAMS", "동적 송전용량", "신규 장비 도입", "해외인력 확보"
                ]
                forbidden = ["HVDC", "디지털 뉴딜", "한국판 뉴딜", "코로나", "재택근무"]

                criteria = GradingCriteria(
                    required_keywords=keywords,
                    forbidden_keywords=forbidden
                )
                result = self.grader.grade_answer(answer_text, criteria)

            progress_win.destroy()

            # 결과 표시
            self.show_grading_result_v2(result)

        except Exception as e:
            if 'progress_win' in locals():
                progress_win.destroy()
            messagebox.showerror("채점 오류", f"채점 중 오류가 발생했습니다:\n{e}")

    def show_grading_result_v2(self, result):
        """V2 채점 결과 표시"""
        result_window = tk.Toplevel(self.root)
        result_window.title("📊 채점 결과")
        result_window.geometry("900x700")

        # 제목
        title = tk.Label(
            result_window,
            text="📊 AI 채점 결과",
            font=("맑은 고딕", 18, "bold"),
            bg="#3498db",
            fg="white",
            pady=15
        )
        title.pack(fill=tk.X)

        # 총점 표시
        if V2_AVAILABLE and isinstance(result, dict):
            total_score = result.get("총점", 0)
        else:
            total_score = result.total_score if hasattr(result, 'total_score') else 0

        score_frame = tk.Frame(result_window, bg="#ecf0f1", pady=20)
        score_frame.pack(fill=tk.X)

        score_label = tk.Label(
            score_frame,
            text=f"총점: {total_score:.1f} / 100점",
            font=("맑은 고딕", 28, "bold"),
            bg="#ecf0f1",
            fg="#e74c3c"
        )
        score_label.pack()

        # 상세 결과
        detail_frame = tk.Frame(result_window)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        detail_text = scrolledtext.ScrolledText(
            detail_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        detail_text.pack(fill=tk.BOTH, expand=True)

        # 결과 포맷팅
        if V2_AVAILABLE and isinstance(result, dict):
            formatted = self.grader.format_result_for_display(result)
            detail_text.insert("1.0", formatted)
        else:
            # V1 형식
            feedback_text = "\n".join(result.feedback) if hasattr(result, 'feedback') else str(result)
            detail_text.insert("1.0", feedback_text)

        detail_text.config(state=tk.DISABLED)

        # 버튼
        btn_frame = tk.Frame(result_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        save_btn = tk.Button(
            btn_frame,
            text="💾 결과 저장",
            command=lambda: self.save_grading_result(result),
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

    def save_grading_result(self, result):
        """채점 결과 저장"""
        filename = filedialog.asksaveasfilename(
            title="채점 결과 저장",
            defaultextension=".json",
            filetypes=[("JSON 파일", "*.json"), ("텍스트 파일", "*.txt")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    if isinstance(result, dict):
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    else:
                        # V1 형식
                        json.dump({
                            "총점": result.total_score,
                            "논리정확성": result.logic_score,
                            "명확간결성": result.clarity_score,
                            "완결성": result.completeness_score,
                            "피드백": result.feedback
                        }, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("저장 완료", f"결과가 저장되었습니다:\n{filename}")

            except Exception as e:
                messagebox.showerror("저장 오류", f"저장 중 오류: {e}")

    def show_exam_panel(self):
        """문제 생성 패널"""
        self.clear_panel()

        # 제목
        title = tk.Label(
            self.right_frame,
            text="📄 연습 문제 생성 (AI 기반)",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        # 설명
        desc = tk.Label(
            self.right_frame,
            text="실제 기출문제를 분석하여 유사한 형식의 연습 문제를 생성합니다",
            font=("맑은 고딕", 10),
            bg="white",
            fg="#7f8c8d"
        )
        desc.pack()

        # 설정 영역
        settings_frame = tk.LabelFrame(
            self.right_frame,
            text="문제 설정",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        settings_frame.pack(fill=tk.X, padx=10, pady=15)

        # 난이도 선택
        diff_frame = tk.Frame(settings_frame, bg="white")
        diff_frame.pack(pady=10)

        tk.Label(
            diff_frame,
            text="난이도:",
            font=("맑은 고딕", 10, "bold"),
            bg="white"
        ).pack(side=tk.LEFT, padx=5)

        self.difficulty_var = tk.StringVar(value="medium")

        difficulties = [
            ("쉬움", "easy"),
            ("보통", "medium"),
            ("어려움", "hard")
        ]

        for text, value in difficulties:
            rb = tk.Radiobutton(
                diff_frame,
                text=text,
                variable=self.difficulty_var,
                value=value,
                font=("맑은 고딕", 10),
                bg="white"
            )
            rb.pack(side=tk.LEFT, padx=10)

        # 주제 입력 (선택)
        topic_frame = tk.Frame(settings_frame, bg="white")
        topic_frame.pack(pady=10)

        tk.Label(
            topic_frame,
            text="주제 (선택):",
            font=("맑은 고딕", 10, "bold"),
            bg="white"
        ).pack(side=tk.LEFT, padx=5)

        self.topic_entry = tk.Entry(
            topic_frame,
            font=("맑은 고딕", 10),
            width=40
        )
        self.topic_entry.pack(side=tk.LEFT, padx=5)
        self.topic_entry.insert(0, "비워두면 자동 선택됩니다")

        # 생성 버튼
        generate_btn = tk.Button(
            self.right_frame,
            text="✨ AI 문제 생성하기",
            command=self.generate_exam_v2,
            font=("맑은 고딕", 12, "bold"),
            bg="#2ecc71",
            fg="white",
            height=2
        )
        generate_btn.pack(pady=15)

        # 결과 표시 영역
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

    def generate_exam_v2(self):
        """V2 문제 생성"""
        if not self.exam_gen:
            messagebox.showerror("오류", "문제 생성 시스템이 초기화되지 않았습니다.")
            return

        difficulty = self.difficulty_var.get()
        topic = self.topic_entry.get().strip()

        if topic == "비워두면 자동 선택됩니다":
            topic = None

        try:
            # 진행 표시
            progress_win = tk.Toplevel(self.root)
            progress_win.title("문제 생성 중...")
            progress_win.geometry("400x150")
            progress_win.transient(self.root)
            progress_win.grab_set()

            tk.Label(
                progress_win,
                text="🤖 AI가 문제를 생성하고 있습니다...",
                font=("맑은 고딕", 12, "bold"),
                pady=20
            ).pack()

            tk.Label(
                progress_win,
                text="실제 기출문제를 분석하여 생성 중\n1-2분 정도 소요됩니다.",
                font=("맑은 고딕", 10),
                fg="#7f8c8d"
            ).pack()

            progress_win.update()

            # 문제 생성
            exam_data = self.exam_gen.generate_practice_exam(
                difficulty=difficulty,
                topic=topic
            )

            progress_win.destroy()

            # 결과 표시
            self.exam_result_text.delete("1.0", tk.END)

            if "error" in exam_data:
                self.exam_result_text.insert("1.0", f"❌ 오류:\n{exam_data['error']}")
                return

            # 문제 정보 표시
            info = f"""✅ 문제 생성 완료!

📌 제목: {exam_data.get('문제_제목', '')}
📝 상황: {exam_data.get('상황_설명', '')}
📊 제시자료: {len(exam_data.get('제시자료', []))}개
🔑 필수 키워드: {len(exam_data.get('필수_키워드', []))}개
⏱️ 예상 시간: {exam_data.get('예상_작성_시간', '150분')}

필수 키워드:
"""
            for i, kw in enumerate(exam_data.get('필수_키워드', []), 1):
                info += f"  {i}. {kw}\n"

            self.exam_result_text.insert("1.0", info)

            # 저장된 문제 데이터
            self.generated_exam_data = exam_data

            # 저장 버튼
            save_btn = tk.Button(
                self.exam_result_frame,
                text="💾 전체 문제지 파일로 저장",
                command=self.save_exam_v2,
                font=("맑은 고딕", 10, "bold"),
                bg="#3498db",
                fg="white"
            )
            save_btn.pack(pady=5)

        except Exception as e:
            if 'progress_win' in locals():
                progress_win.destroy()
            messagebox.showerror("생성 오류", f"문제 생성 중 오류:\n{e}")

    def save_exam_v2(self):
        """생성된 문제 저장"""
        if not hasattr(self, 'generated_exam_data'):
            messagebox.showwarning("경고", "생성된 문제가 없습니다.")
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
                        json.dump(self.generated_exam_data, f, ensure_ascii=False, indent=2)
                else:
                    full_doc = self.exam_gen.generate_full_exam_document(
                        self.generated_exam_data,
                        output_file=filename
                    )

                messagebox.showinfo("저장 완료", f"문제지가 저장되었습니다:\n{filename}")

            except Exception as e:
                messagebox.showerror("저장 오류", f"저장 중 오류: {e}")

    def show_study_guide(self):
        """공부 가이드 표시"""
        self.clear_panel()

        # 제목
        title = tk.Label(
            self.right_frame,
            text="📚 공부 노하우 (PDF 분석 기반)",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        # 생성 버튼
        generate_btn = tk.Button(
            self.right_frame,
            text="✨ AI 가이드 생성 (PDF 분석)",
            command=self.generate_study_guide_v2,
            font=("맑은 고딕", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            height=2
        )
        generate_btn.pack(pady=10)

        # 결과 영역
        result_frame = tk.Frame(self.right_frame, bg="white")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.guide_text = scrolledtext.ScrolledText(
            result_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        self.guide_text.pack(fill=tk.BOTH, expand=True)

    def generate_study_guide_v2(self):
        """V2 공부 가이드 생성"""
        if not self.study_guide:
            messagebox.showerror("오류", "가이드 시스템이 초기화되지 않았습니다.")
            return

        try:
            # 진행 표시
            progress_win = tk.Toplevel(self.root)
            progress_win.title("가이드 생성 중...")
            progress_win.geometry("400x150")
            progress_win.transient(self.root)
            progress_win.grab_set()

            tk.Label(
                progress_win,
                text="🤖 AI가 가이드를 생성하고 있습니다...",
                font=("맑은 고딕", 12, "bold"),
                pady=20
            ).pack()

            tk.Label(
                progress_win,
                text="PDF 문서 분석 중\n1-2분 정도 소요됩니다.",
                font=("맑은 고딕", 10),
                fg="#7f8c8d"
            ).pack()

            progress_win.update()

            # 가이드 생성
            guide_data = self.study_guide.generate_comprehensive_guide()

            progress_win.destroy()

            # 결과 표시
            self.guide_text.delete("1.0", tk.END)

            if isinstance(guide_data, dict) and V2_AVAILABLE:
                formatted = self.study_guide.format_guide_for_display(guide_data)
                self.guide_text.insert("1.0", formatted)
            else:
                # V1 형식
                self.study_guide.print_study_guide()

        except Exception as e:
            if 'progress_win' in locals():
                progress_win.destroy()
            messagebox.showerror("생성 오류", f"가이드 생성 중 오류:\n{e}")

    def show_study_plan(self):
        """학습 계획 표시"""
        self.clear_panel()

        # 간단한 학습 계획 (V2와 동일)
        plan_text = """

【4주 학습 계획】

▶ 1주차: 채점 방식 이해 및 기출문제 분석
  활동:
    • 채점 방식 문서 정독 (OPR 채점방식.pdf)
    • 작성 팁 문서 정독 (OPR 작성 팁.pdf)
    • 기출문제 3개년 분석 (구조 파악)
    • 모범답안과 채점기준 비교 분석
  ✓ 체크포인트: 채점 기준 3가지를 말할 수 있는가?

▶ 2주차: 키워드 추출 연습 및 문제 분석 훈련
  활동:
    • 문제지에서 키워드 추출 연습 (형광펜 활용)
    • 제시자료 유형별 특징 파악 (CEO 메시지, 이메일, 메신저 등)
    • 기출문제 1개 시간제한 없이 작성해보기
    • 모범답안과 비교하여 빠진 키워드 확인
  ✓ 체크포인트: 제시자료에서 키워드를 빠르게 찾을 수 있는가?

▶ 3주차: 실전 연습 및 시간 관리
  활동:
    • 기출문제 2개 실전처럼 시간 맞춰 작성 (150분)
    • 작성 후 스스로 채점해보기
    • 빠진 키워드와 구조 문제 분석
    • 자신만의 루틴 확립 (예: 15분 독해 → 10분 구조 잡기 → 120분 작성 → 5분 검토)
  ✓ 체크포인트: 150분 내에 26줄 답안을 완성할 수 있는가?

▶ 4주차: 최종 점검 및 실전 감각 유지
  활동:
    • 기출문제 2~3개 추가 실전 연습
    • 약점 파트 집중 훈련
    • 경영연구원 보고서 읽기 (회사 현안 트렌드 파악)
    • 최신 전력산업 이슈 확인
  ✓ 체크포인트: 모범답안에 가까운 답안을 작성할 수 있는가?
        """

        label = tk.Label(
            self.right_frame,
            text=plan_text,
            font=("맑은 고딕", 11),
            bg="white",
            justify=tk.LEFT
        )
        label.pack(expand=True, pady=20, padx=20)

    def show_checklist(self):
        """체크리스트 표시"""
        self.clear_panel()

        checklist_text = """

【시험 당일 체크리스트】

  □ 문제지 받으면 제목과 대제목을 먼저 작성했는가?
  □ CEO 메시지에서 추진배경과 향후 일정을 체크했는가?
  □ 처장/부장 이메일과 메신저에서 보고서 구조를 확인했는가?
  □ 제시자료를 읽으며 키워드에 형광펜으로 표시했는가?
  □ 모든 키워드를 문제지에 있는 단어 그대로 사용했는가?
  □ 금지어를 사용하지 않았는가? (메신저/쪽지에서 확인)
  □ 각 줄이 35자를 초과하지 않았는가?
  □ 총 26줄 이내로 작성했는가?
  □ 보고서 구조가 명확한가? (1, 2, 3 → □ → ○ → - 순서)
  □ CEO 중심의 향후 일정을 작성했는가?
  □ 단순 키워드 나열이 아닌 논리적 문장인가?
  □ 제목은 21자 이내인가? (HY헤드라인M, 21포인트)
        """

        label = tk.Label(
            self.right_frame,
            text=checklist_text,
            font=("맑은 고딕", 12),
            bg="white",
            justify=tk.LEFT
        )
        label.pack(expand=True, pady=20, padx=20)

    def show_api_settings(self):
        """API 설정 화면"""
        self.clear_panel()

        title = tk.Label(
            self.right_frame,
            text="⚙️ Claude API 설정",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=15)

        desc_text = """
Claude API를 사용하면 더 정확한 채점과 문제 생성이 가능합니다.

API 키를 환경변수 ANTHROPIC_API_KEY로 설정하거나,
아래 필드에 입력하세요.

Claude API 키 받기:
https://console.anthropic.com/
        """

        desc = tk.Label(
            self.right_frame,
            text=desc_text,
            font=("맑은 고딕", 10),
            bg="white",
            justify=tk.LEFT
        )
        desc.pack(pady=10)

        # 현재 상태
        status_frame = tk.LabelFrame(
            self.right_frame,
            text="현재 상태",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        status_text = f"""
버전: {self.version}
API 사용 가능: {'✅ 예' if V2_AVAILABLE and self.api_key else '❌ 아니오'}
환경변수 설정: {'✅ 예' if os.getenv("ANTHROPIC_API_KEY") else '❌ 아니오'}
        """

        status_label = tk.Label(
            status_frame,
            text=status_text,
            font=("맑은 고딕", 10),
            bg="white",
            justify=tk.LEFT
        )
        status_label.pack(padx=10, pady=10)

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

        if self.api_key:
            self.api_key_entry.insert(0, self.api_key)

        save_key_btn = tk.Button(
            key_frame,
            text="💾 저장 및 재시작",
            command=self.save_api_key,
            font=("맑은 고딕", 10, "bold"),
            bg="#2ecc71",
            fg="white"
        )
        save_key_btn.pack(pady=10)

    def save_api_key(self):
        """API 키 저장"""
        key = self.api_key_entry.get().strip()

        if not key:
            messagebox.showwarning("경고", "API 키를 입력하세요.")
            return

        # 환경변수 설정
        os.environ["ANTHROPIC_API_KEY"] = key
        self.api_key = key

        messagebox.showinfo(
            "완료",
            "API 키가 저장되었습니다.\n프로그램을 재시작하여 변경사항을 적용하세요."
        )


def main():
    """메인 함수"""
    root = tk.Tk()
    app = OPRSystemGUIV2(root)
    root.mainloop()


if __name__ == "__main__":
    main()
