#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 자동 채점 시스템 통합 프로그램
"""

import sys
import argparse
from auto_grading_system import AutoGradingSystem, GradingCriteria
from exam_generator import ExamGenerator
from study_guide import StudyGuideSystem


class OPRSystem:
    """OPR 시스템 통합 클래스"""

    def __init__(self):
        self.grader = AutoGradingSystem()
        self.exam_gen = ExamGenerator()
        self.study_guide = StudyGuideSystem()
        print("🎓 OPR 자동 채점 시스템을 시작합니다...")

    def run_interactive_menu(self):
        """대화형 메뉴"""

        while True:
            print("\n" + "="*60)
            print("📚 OPR 자동 채점 시스템 메뉴")
            print("="*60)
            print("1. 답안 자동 채점")
            print("2. 연습 문제 생성")
            print("3. 공부 노하우 보기")
            print("4. 학습 계획 생성")
            print("5. 작성 체크리스트 보기")
            print("0. 종료")
            print("="*60)

            choice = input("\n선택하세요 (0-5): ").strip()

            if choice == "0":
                print("\n👋 프로그램을 종료합니다.")
                break
            elif choice == "1":
                self._grade_answer_interactive()
            elif choice == "2":
                self._generate_exam_interactive()
            elif choice == "3":
                self._show_study_tips()
            elif choice == "4":
                self._generate_study_plan()
            elif choice == "5":
                self._show_checklist()
            else:
                print("\n❌ 잘못된 선택입니다. 다시 선택해주세요.")

    def _grade_answer_interactive(self):
        """대화형 답안 채점"""

        print("\n" + "-"*60)
        print("📝 답안 채점")
        print("-"*60)

        print("\n답안 입력 방법을 선택하세요:")
        print("1. 직접 입력")
        print("2. 파일에서 읽기")
        print("3. 샘플 답안 사용")

        method = input("\n선택 (1-3): ").strip()

        answer_text = ""

        if method == "1":
            print("\n답안을 입력하세요 (입력 완료 후 빈 줄에서 Ctrl+D 또는 END 입력):")
            lines = []
            try:
                while True:
                    line = input()
                    if line.upper() == "END":
                        break
                    lines.append(line)
            except EOFError:
                pass
            answer_text = "\n".join(lines)

        elif method == "2":
            filename = input("파일 경로를 입력하세요: ").strip()
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    answer_text = f.read()
            except Exception as e:
                print(f"\n❌ 파일 읽기 오류: {e}")
                return

        elif method == "3":
            answer_text = self._get_sample_answer()
            print("\n✅ 샘플 답안을 사용합니다.")

        if not answer_text:
            print("\n❌ 답안이 비어있습니다.")
            return

        # 키워드 입력
        print("\n평가 키워드를 입력하세요 (쉼표로 구분, Enter로 기본값 사용):")
        keywords_input = input("키워드: ").strip()

        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",")]
        else:
            keywords = self._get_default_keywords()
            print(f"기본 키워드 사용: {', '.join(keywords[:5])}...")

        # 금지어 입력
        print("\n금지어를 입력하세요 (쉼표로 구분, Enter로 기본값 사용):")
        forbidden_input = input("금지어: ").strip()

        if forbidden_input:
            forbidden = [k.strip() for k in forbidden_input.split(",")]
        else:
            forbidden = ["HVDC", "디지털 뉴딜", "한국판 뉴딜", "코로나", "재택근무"]
            print(f"기본 금지어 사용: {', '.join(forbidden)}")

        # 채점 실행
        criteria = GradingCriteria(
            required_keywords=keywords,
            forbidden_keywords=forbidden
        )

        print("\n⏳ 채점 중...")
        result = self.grader.grade_answer(answer_text, criteria)

        # 결과 출력
        print("\n" + "="*60)
        print("📊 채점 결과")
        print("="*60)
        print("\n".join(result.feedback))

    def _generate_exam_interactive(self):
        """대화형 문제 생성"""

        print("\n" + "-"*60)
        print("📄 연습 문제 생성")
        print("-"*60)

        print("\n문제 난이도를 선택하세요:")
        print("1. 쉬움 (easy)")
        print("2. 보통 (medium)")
        print("3. 어려움 (hard)")

        difficulty_choice = input("\n선택 (1-3): ").strip()
        difficulty_map = {"1": "easy", "2": "medium", "3": "hard"}
        difficulty = difficulty_map.get(difficulty_choice, "medium")

        print(f"\n✅ 난이도 '{difficulty}' 문제를 생성합니다...")

        exam_data = self.exam_gen.create_practice_exam(difficulty=difficulty)

        print("\n" + "="*60)
        print("생성된 문제 정보")
        print("="*60)
        print(f"제목: {exam_data['title']}")
        print(f"상황: {exam_data['situation']}")
        print(f"키워드: {', '.join(exam_data['keywords'])}")
        print(f"난이도: {exam_data['difficulty']}")
        print(f"예상 시간: {exam_data['estimated_time']}")
        print(f"제시자료 개수: {exam_data['materials_count']}개")

        # 전체 문제지 생성
        print("\n전체 문제지를 생성하시겠습니까? (y/n): ", end="")
        if input().strip().lower() == 'y':
            full_exam = self.exam_gen.generate_exam_from_template(
                title=exam_data['title'],
                situation=exam_data['situation'],
                main_keywords=exam_data['keywords'],
                num_materials=exam_data['materials_count']
            )

            filename = f"practice_exam_{difficulty}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_exam)

            print(f"\n✅ 문제지가 '{filename}' 파일로 저장되었습니다.")

    def _show_study_tips(self):
        """공부 노하우 보기"""

        print("\n" + "-"*60)
        print("📚 공부 노하우")
        print("-"*60)

        self.study_guide.print_study_guide()

    def _generate_study_plan(self):
        """학습 계획 생성"""

        print("\n" + "-"*60)
        print("📅 학습 계획 생성")
        print("-"*60)

        weeks = input("\n학습 기간을 입력하세요 (주 단위, 기본 4주): ").strip()

        try:
            weeks = int(weeks) if weeks else 4
        except ValueError:
            weeks = 4

        plan = self.study_guide.generate_study_plan(weeks=weeks)

        print(f"\n{'='*60}")
        print(f"{plan['총_기간']} 학습 계획")
        print("="*60)

        for week_plan in plan["주차별_계획"]:
            print(f"\n▶ {week_plan['주차']}: {week_plan['목표']}")
            print("  활동:")
            for activity in week_plan["활동"]:
                print(f"    • {activity}")
            if "체크포인트" in week_plan:
                print(f"  ✓ 체크포인트: {week_plan['체크포인트']}")

    def _show_checklist(self):
        """작성 체크리스트 보기"""

        print("\n" + "-"*60)
        print("✅ 시험 당일 체크리스트")
        print("-"*60 + "\n")

        checklist = self.study_guide.generate_writing_checklist()
        for item in checklist:
            print(f"  {item}")

        print("\n" + "-"*60)

    def _get_sample_answer(self) -> str:
        """샘플 답안 반환"""

        return """전력망 건설 지연 대응전략 보고서

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

    def _get_default_keywords(self) -> list:
        """기본 키워드 반환"""

        return [
            "전력망 건설지연", "발전제약 해소", "법령 제개정", "시공기간 단축",
            "전력망혁신위원회", "전원촉진법", "입지선정위원회", "협의간주제",
            "NWAs", "계통안정화용 ESS", "유연송전설비", "고객참여 부하차단",
            "WAMS", "동적 송전용량", "신규 장비 도입", "해외인력 확보",
            "첨단산업", "재생에너지", "인허가", "송전능력"
        ]


def main():
    """메인 함수"""

    parser = argparse.ArgumentParser(
        description="OPR 자동 채점 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python opr_system.py                    # 대화형 메뉴
  python opr_system.py --grade sample.txt # 답안 파일 채점
  python opr_system.py --exam             # 문제 생성
  python opr_system.py --guide            # 공부 가이드 보기
        """
    )

    parser.add_argument(
        "--grade",
        metavar="FILE",
        help="답안 파일을 채점합니다"
    )

    parser.add_argument(
        "--exam",
        action="store_true",
        help="연습 문제를 생성합니다"
    )

    parser.add_argument(
        "--guide",
        action="store_true",
        help="공부 노하우를 출력합니다"
    )

    args = parser.parse_args()

    system = OPRSystem()

    if args.grade:
        # 파일 채점
        try:
            with open(args.grade, 'r', encoding='utf-8') as f:
                answer_text = f.read()

            criteria = GradingCriteria(
                required_keywords=system._get_default_keywords(),
                forbidden_keywords=["HVDC", "디지털 뉴딜", "한국판 뉴딜"]
            )

            result = system.grader.grade_answer(answer_text, criteria)
            print("\n".join(result.feedback))
        except Exception as e:
            print(f"오류: {e}")
            sys.exit(1)

    elif args.exam:
        # 문제 생성
        exam_data = system.exam_gen.create_practice_exam()
        print(f"제목: {exam_data['title']}")
        print(f"키워드: {', '.join(exam_data['keywords'])}")

    elif args.guide:
        # 공부 가이드
        system.study_guide.print_study_guide()

    else:
        # 대화형 메뉴
        system.run_interactive_menu()


if __name__ == "__main__":
    main()
