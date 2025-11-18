#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 자동 채점 시스템 GUI 버전
하나의 파일 실행으로 모든 기능 사용 가능
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from auto_grading_system import AutoGradingSystem, GradingCriteria
from exam_generator import ExamGenerator
from study_guide import StudyGuideSystem
import json


class OPRSystemGUI:
    """OPR 시스템 GUI 메인 클래스"""

    def __init__(self, root):
        self.root = root
        self.root.title("📚 OPR 자동 채점 시스템")
        self.root.geometry("1000x700")

        # 시스템 초기화
        self.grader = AutoGradingSystem()
        self.exam_gen = ExamGenerator()
        self.study_guide = StudyGuideSystem()

        # UI 생성
        self.create_widgets()

    def create_widgets(self):
        """UI 구성"""

        # 상단 제목
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(
            title_frame,
            text="📚 OPR 자동 채점 시스템",
            font=("맑은 고딕", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)

        # 메인 컨테이너
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 왼쪽: 메뉴 버튼들
        left_frame = tk.Frame(main_container, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        menu_label = tk.Label(
            left_frame,
            text="🎯 메뉴 선택",
            font=("맑은 고딕", 16, "bold")
        )
        menu_label.pack(pady=(0, 20))

        # 메뉴 버튼들
        buttons = [
            ("📝 답안 자동 채점", self.show_grading_panel, "#3498db"),
            ("📄 연습 문제 생성", self.show_exam_panel, "#2ecc71"),
            ("📚 공부 노하우 보기", self.show_study_guide, "#e74c3c"),
            ("📅 학습 계획 생성", self.show_study_plan, "#f39c12"),
            ("✅ 체크리스트 보기", self.show_checklist, "#9b59b6"),
        ]

        for text, command, color in buttons:
            btn = tk.Button(
                left_frame,
                text=text,
                command=command,
                font=("맑은 고딕", 12, "bold"),
                bg=color,
                fg="white",
                activebackground=color,
                activeforeground="white",
                relief=tk.RAISED,
                bd=3,
                cursor="hand2",
                height=2
            )
            btn.pack(fill=tk.X, pady=5)

        # 종료 버튼
        exit_btn = tk.Button(
            left_frame,
            text="🚪 종료",
            command=self.root.quit,
            font=("맑은 고딕", 12, "bold"),
            bg="#34495e",
            fg="white",
            activebackground="#2c3e50",
            activeforeground="white",
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

        welcome_text = """

🎓 OPR 자동 채점 시스템에 오신 것을 환영합니다!

왼쪽 메뉴에서 원하는 기능을 선택하세요.


📝 답안 자동 채점
   - 작성한 답안을 자동으로 채점합니다
   - 키워드 매칭 및 금지어 검사
   - 상세한 피드백 제공

📄 연습 문제 생성
   - 새로운 연습 문제를 생성합니다
   - 난이도별 선택 가능

📚 공부 노하우 보기
   - 채점 방식 및 작성 전략
   - 고득점 비법 제공

📅 학습 계획 생성
   - 4주 단계별 학습 계획
   - 체계적인 준비 가이드

✅ 체크리스트 보기
   - 시험 당일 확인사항
   - 12가지 체크포인트
        """

        label = tk.Label(
            self.right_frame,
            text=welcome_text,
            font=("맑은 고딕", 12),
            bg="white",
            justify=tk.LEFT
        )
        label.pack(expand=True)

    def show_grading_panel(self):
        """채점 패널"""
        self.clear_panel()

        # 제목
        title = tk.Label(
            self.right_frame,
            text="📝 답안 자동 채점",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=10)

        # 답안 입력 영역
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

        # 버튼 영역
        btn_frame = tk.Frame(self.right_frame, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        load_btn = tk.Button(
            btn_frame,
            text="📂 파일에서 불러오기",
            command=self.load_answer_file,
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white"
        )
        load_btn.pack(side=tk.LEFT, padx=5)

        sample_btn = tk.Button(
            btn_frame,
            text="📋 샘플 답안 사용",
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
            font=("맑은 고딕", 11, "bold"),
            bg="#3498db",
            fg="white",
            width=15
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

        # 기본 키워드
        keywords = [
            "전력망 건설지연", "발전제약 해소", "법령 제개정", "시공기간 단축",
            "전력망혁신위원회", "전원촉진법", "입지선정위원회", "협의간주제",
            "NWAs", "계통안정화용 ESS", "유연송전설비", "고객참여 부하차단",
            "WAMS", "동적 송전용량", "신규 장비 도입", "해외인력 확보"
        ]

        forbidden = ["HVDC", "디지털 뉴딜", "한국판 뉴딜", "코로나", "재택근무"]

        # 채점 실행
        criteria = GradingCriteria(
            required_keywords=keywords,
            forbidden_keywords=forbidden
        )

        result = self.grader.grade_answer(answer, criteria)

        # 결과 표시
        self.show_grading_result(result)

    def show_grading_result(self, result):
        """채점 결과 표시"""
        result_window = tk.Toplevel(self.root)
        result_window.title("📊 채점 결과")
        result_window.geometry("700x600")

        # 제목
        title = tk.Label(
            result_window,
            text="📊 채점 결과",
            font=("맑은 고딕", 18, "bold"),
            bg="#3498db",
            fg="white",
            pady=15
        )
        title.pack(fill=tk.X)

        # 총점 표시
        score_frame = tk.Frame(result_window, bg="#ecf0f1", pady=20)
        score_frame.pack(fill=tk.X)

        score_label = tk.Label(
            score_frame,
            text=f"총점: {result.total_score:.1f} / 100점",
            font=("맑은 고딕", 24, "bold"),
            bg="#ecf0f1",
            fg="#e74c3c"
        )
        score_label.pack()

        # 상세 결과
        detail_text = scrolledtext.ScrolledText(
            result_window,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        detail_text.insert("1.0", "\n".join(result.feedback))
        detail_text.config(state=tk.DISABLED)

        # 닫기 버튼
        close_btn = tk.Button(
            result_window,
            text="닫기",
            command=result_window.destroy,
            font=("맑은 고딕", 11),
            bg="#95a5a6",
            fg="white",
            width=15
        )
        close_btn.pack(pady=10)

    def show_exam_panel(self):
        """문제 생성 패널"""
        self.clear_panel()

        # 제목
        title = tk.Label(
            self.right_frame,
            text="📄 연습 문제 생성",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=20)

        # 난이도 선택
        diff_frame = tk.LabelFrame(
            self.right_frame,
            text="난이도 선택",
            font=("맑은 고딕", 12, "bold"),
            bg="white"
        )
        diff_frame.pack(pady=20)

        self.difficulty_var = tk.StringVar(value="medium")

        difficulties = [
            ("쉬움 (Easy)", "easy"),
            ("보통 (Medium)", "medium"),
            ("어려움 (Hard)", "hard")
        ]

        for text, value in difficulties:
            rb = tk.Radiobutton(
                diff_frame,
                text=text,
                variable=self.difficulty_var,
                value=value,
                font=("맑은 고딕", 11),
                bg="white"
            )
            rb.pack(anchor=tk.W, padx=20, pady=5)

        # 생성 버튼
        generate_btn = tk.Button(
            self.right_frame,
            text="🎲 문제 생성하기",
            command=self.generate_exam,
            font=("맑은 고딕", 12, "bold"),
            bg="#2ecc71",
            fg="white",
            width=20,
            height=2
        )
        generate_btn.pack(pady=20)

        # 결과 표시 영역
        self.exam_result_frame = tk.LabelFrame(
            self.right_frame,
            text="생성된 문제 정보",
            font=("맑은 고딕", 11, "bold"),
            bg="white"
        )
        self.exam_result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def generate_exam(self):
        """문제 생성"""
        difficulty = self.difficulty_var.get()

        self.exam_gen.load_exam_patterns()
        exam_data = self.exam_gen.create_practice_exam(difficulty=difficulty)

        # 기존 결과 지우기
        for widget in self.exam_result_frame.winfo_children():
            widget.destroy()

        # 결과 표시
        info_text = f"""
📌 제목: {exam_data['title']}

📝 상황:
{exam_data['situation']}

🔑 주요 키워드:
{', '.join(exam_data['keywords'])}

⏱️ 예상 시간: {exam_data['estimated_time']}

📚 제시자료: {exam_data['materials_count']}개

🎯 난이도: {exam_data['difficulty']}
        """

        result_label = tk.Label(
            self.exam_result_frame,
            text=info_text,
            font=("맑은 고딕", 11),
            bg="white",
            justify=tk.LEFT
        )
        result_label.pack(padx=10, pady=10, anchor=tk.W)

        # 전체 문제지 생성 버튼
        save_btn = tk.Button(
            self.exam_result_frame,
            text="💾 전체 문제지 파일로 저장",
            command=lambda: self.save_full_exam(exam_data),
            font=("맑은 고딕", 10),
            bg="#3498db",
            fg="white"
        )
        save_btn.pack(pady=10)

    def save_full_exam(self, exam_data):
        """전체 문제지 파일로 저장"""
        full_exam = self.exam_gen.generate_exam_from_template(
            title=exam_data['title'],
            situation=exam_data['situation'],
            main_keywords=exam_data['keywords'],
            num_materials=exam_data['materials_count']
        )

        filename = filedialog.asksaveasfilename(
            title="문제지 저장",
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_exam)
                messagebox.showinfo("성공", f"문제지가 저장되었습니다:\n{filename}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 오류: {e}")

    def show_study_guide(self):
        """공부 가이드 표시"""
        self.clear_panel()

        # 제목
        title = tk.Label(
            self.right_frame,
            text="📚 공부 노하우",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=10)

        # 텍스트 영역
        text_area = scrolledtext.ScrolledText(
            self.right_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 가이드 내용
        guide_content = """
【핵심 작성 전략 TOP 5】

1️⃣ 제시문의 단어를 그대로 사용하라
   - ❌ 온실가스 억제 → ✅ 온실가스 저감
   - ❌ 친환경 기술수준 부족 → ✅ 친환경 기술수준 미흡
   - 모든 단어는 문제지에 있는 단어만 사용!

2️⃣ 키워드를 최대한 많이 넣어라
   - 채점자는 200명 답안을 빠르게 채점
   - 키워드를 보고 채점함
   - 정 모르겠으면 관련 키워드 최대한 많이 작성

3️⃣ 시험지 받으면 먼저 제목, 대제목 작성
   - 문제에서 틀을 잡고 시작
   - 읽으면서 채워나가기
   - 쉽게 찾을 수 있는 항목들은 먼저 써놓기

4️⃣ CEO 메시지에서 추진배경과 향후 일정 추출
   - CEO가 "~하자" → 무조건 향후 계획
   - 전사 행사, 토론회, 워크샵 → 향후 계획
   - CEO 중심의 일정으로 정리

5️⃣ 부장과 컴케에서 보고서 틀 확인
   - 2, 3번에서 보고서 구조 확인
   - 주의사항도 여기서 체크


【채점 방식 이해】

🔍 채점자 환경:
   • 4명이 한 조로 200명 답안 채점
   • 모니터 화면 보고 마우스로 점수 입력
   • 하루종일 집중 불가능
   → 키워드 중심으로 채점!

📊 채점 기준:
   • 논리·정확성 (40점): 키워드 매칭 + 금지어 감점
   • 명확·간결성 (30점): S/A/B/C/D 등급
   • 완결성 (30점): S/A/B/C/D 등급


【금지사항】

⚠️ 금지어 사용 시 감점
   - 메신저/쪽지에서 주의사항 확인
   - CEO 중심이 아닌 일정 (예: BP 발표 자료 준비)

⚠️ 타 신재생 사업 관련 금지
   - 디지털 뉴딜, 한국판 뉴딜
   - 코로나, 재택근무


【작성 팁】

✅ 화살표(→)나 한자 사용 가능
   - 뜻이 통하면 OK

✅ 특정 단어 반복은 영향 거의 없음
   - 필요/확보/제고/추진 등

✅ 검토배경 키워드 전부 포함되면 □ 개수 무관


💡 핵심 요약: 제시문의 키워드를 그대로, 최대한 많이!
        """

        text_area.insert("1.0", guide_content)
        text_area.config(state=tk.DISABLED)

    def show_study_plan(self):
        """학습 계획 표시"""
        self.clear_panel()

        # 제목
        title = tk.Label(
            self.right_frame,
            text="📅 4주 학습 계획",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=10)

        # 텍스트 영역
        text_area = scrolledtext.ScrolledText(
            self.right_frame,
            font=("맑은 고딕", 10),
            wrap=tk.WORD
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 학습 계획 생성
        plan = self.study_guide.generate_study_plan(weeks=4)

        plan_text = f"{'='*60}\n"
        plan_text += f"  {plan['총_기간']} 학습 계획\n"
        plan_text += f"{'='*60}\n\n"

        for week_plan in plan["주차별_계획"]:
            plan_text += f"▶ {week_plan['주차']}: {week_plan['목표']}\n"
            plan_text += f"{'─'*60}\n"
            plan_text += "  📌 활동:\n"
            for activity in week_plan["활동"]:
                plan_text += f"    • {activity}\n"
            plan_text += f"\n  ✓ 체크포인트: {week_plan['체크포인트']}\n"
            plan_text += "\n\n"

        text_area.insert("1.0", plan_text)
        text_area.config(state=tk.DISABLED)

    def show_checklist(self):
        """체크리스트 표시"""
        self.clear_panel()

        # 제목
        title = tk.Label(
            self.right_frame,
            text="✅ 시험 당일 체크리스트",
            font=("맑은 고딕", 18, "bold"),
            bg="white"
        )
        title.pack(pady=10)

        # 체크리스트 프레임
        checklist_frame = tk.Frame(self.right_frame, bg="white")
        checklist_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        checklist = self.study_guide.generate_writing_checklist()

        # 체크박스들
        self.check_vars = []
        for i, item in enumerate(checklist):
            var = tk.BooleanVar()
            self.check_vars.append(var)

            cb = tk.Checkbutton(
                checklist_frame,
                text=item,
                variable=var,
                font=("맑은 고딕", 11),
                bg="white",
                anchor=tk.W
            )
            cb.pack(fill=tk.X, pady=3)

        # 전체 선택/해제 버튼
        btn_frame = tk.Frame(self.right_frame, bg="white")
        btn_frame.pack(pady=10)

        select_all_btn = tk.Button(
            btn_frame,
            text="✅ 전체 선택",
            command=lambda: self.toggle_all_checks(True),
            font=("맑은 고딕", 10),
            bg="#2ecc71",
            fg="white"
        )
        select_all_btn.pack(side=tk.LEFT, padx=5)

        deselect_all_btn = tk.Button(
            btn_frame,
            text="❌ 전체 해제",
            command=lambda: self.toggle_all_checks(False),
            font=("맑은 고딕", 10),
            bg="#e74c3c",
            fg="white"
        )
        deselect_all_btn.pack(side=tk.LEFT, padx=5)

    def toggle_all_checks(self, state):
        """전체 체크박스 토글"""
        for var in self.check_vars:
            var.set(state)


def main():
    """메인 함수"""
    root = tk.Tk()
    app = OPRSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
