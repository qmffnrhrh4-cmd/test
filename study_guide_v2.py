#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 공부 노하우 시스템 V2
Claude API를 활용한 PDF 문서 기반 가이드 생성
"""

import os
import json
from typing import Dict, List, Optional
from claude_api_client import ClaudeAPIClient
from pdf_utils import PDFExtractor


class StudyGuideSystemV2:
    """공부 노하우 시스템 V2 - Claude API 기반"""

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화

        Args:
            api_key: Claude API 키
        """
        try:
            self.api_client = ClaudeAPIClient(api_key)
            self.pdf_extractor = PDFExtractor()
            self.model_answers_dir = "./모범답안"
            self.api_available = True
        except Exception as e:
            print(f"⚠️ Claude API 초기화 실패: {e}")
            print("기본 가이드 모드로 작동합니다.")
            self.api_available = False
            self.pdf_extractor = PDFExtractor()
            self.model_answers_dir = "./모범답안"

    def load_guide_documents(self) -> Dict[str, str]:
        """
        채점 가이드 문서 로드

        Returns:
            {문서 유형: 텍스트} 딕셔너리
        """
        return self.pdf_extractor.get_grading_guides(self.model_answers_dir)

    def generate_comprehensive_guide(
        self,
        use_api: bool = True
    ) -> Dict:
        """
        종합 공부 가이드 생성

        Args:
            use_api: API 사용 여부

        Returns:
            가이드 딕셔너리
        """
        if not use_api or not self.api_available:
            return self._generate_basic_guide()

        # 문서 로드
        guides = self.load_guide_documents()

        if not guides:
            print("⚠️ 가이드 문서를 찾을 수 없습니다. 기본 모드로 생성합니다.")
            return self._generate_basic_guide()

        grading_guide = guides.get("채점방식", "")
        writing_tips = guides.get("작성팁", "")

        # Claude API로 가이드 생성
        result = self.api_client.generate_study_guide_from_documents(
            grading_guide=grading_guide,
            writing_tips=writing_tips
        )

        return result

    def format_guide_for_display(self, guide_data: Dict) -> str:
        """
        가이드를 보기 좋게 포맷팅

        Args:
            guide_data: 가이드 데이터

        Returns:
            포맷팅된 문자열
        """
        output = []

        output.append("\n" + "="*80)
        output.append("📚 OPR 종합 공부 가이드")
        output.append("="*80 + "\n")

        # 에러 체크
        if "error" in guide_data:
            output.append(f"❌ 오류: {guide_data['error']}")
            return "\n".join(output)

        # 핵심 전략 TOP5
        top_strategies = guide_data.get('핵심_전략_TOP5', [])
        if top_strategies:
            output.append("【1】 핵심 전략 TOP 5 (필수!)")
            output.append("-" * 80)
            output.append("")

            for strategy in top_strategies:
                rank = strategy.get('순위', 0)
                title = strategy.get('제목', '')
                desc = strategy.get('설명', '')
                examples = strategy.get('예시', [])
                importance = strategy.get('중요도', '')

                output.append(f"🎯 {rank}. {title} [{importance}]")
                output.append(f"   {desc}")

                if examples:
                    output.append("   예시:")
                    for ex in examples:
                        output.append(f"     • {ex}")

                output.append("")

        # 채점 방식 이해
        grading_understanding = guide_data.get('채점_방식_이해', {})
        if grading_understanding:
            output.append("\n【2】 채점 방식 이해")
            output.append("-" * 80)
            output.append("")

            for criterion, description in grading_understanding.items():
                output.append(f"• {criterion}")
                output.append(f"  {description}")
                output.append("")

        # 작성 노하우
        writing_tips = guide_data.get('작성_노하우', [])
        if writing_tips:
            output.append("\n【3】 작성 노하우")
            output.append("-" * 80)
            output.append("")

            for tip in writing_tips:
                category = tip.get('카테고리', '')
                tips_list = tip.get('팁', [])

                output.append(f"📌 {category}")
                for t in tips_list:
                    output.append(f"   ✓ {t}")
                output.append("")

        # 금지사항
        forbidden = guide_data.get('금지사항', [])
        if forbidden:
            output.append("\n【4】 금지사항 (반드시 피하세요!)")
            output.append("-" * 80)
            output.append("")

            for item in forbidden:
                output.append(f"   ⚠️ {item}")
            output.append("")

        # 4주 학습 계획
        study_plan = guide_data.get('4주_학습_계획', [])
        if study_plan:
            output.append("\n【5】 4주 학습 계획")
            output.append("-" * 80)
            output.append("")

            for week in study_plan:
                week_num = week.get('주차', '')
                goal = week.get('목표', '')
                activities = week.get('활동', [])
                checkpoint = week.get('체크포인트', '')

                output.append(f"▶ {week_num}: {goal}")
                output.append("  활동:")
                for activity in activities:
                    output.append(f"    • {activity}")
                output.append(f"  ✓ 체크포인트: {checkpoint}")
                output.append("")

        # 시험 당일 체크리스트
        checklist = guide_data.get('시험_당일_체크리스트', [])
        if checklist:
            output.append("\n【6】 시험 당일 체크리스트")
            output.append("-" * 80)
            output.append("")

            for i, item in enumerate(checklist, 1):
                output.append(f"   □ {item}")
            output.append("")

        output.append("="*80)
        output.append("💡 핵심 요약: 제시문의 키워드를 그대로, 최대한 많이 사용하라!")
        output.append("="*80 + "\n")

        return "\n".join(output)

    def _generate_basic_guide(self) -> Dict:
        """
        기본 가이드 생성 (API 없을 때)

        Returns:
            가이드 딕셔너리
        """
        return {
            "핵심_전략_TOP5": [
                {
                    "순위": 1,
                    "제목": "제시문의 단어를 그대로 사용하라",
                    "설명": "모든 단어는 문제지에 있는 단어만 쓰고, 있는 그대로 작성하는 게 중요합니다.",
                    "예시": [
                        "❌ 온실가스 억제 → ✅ 온실가스 저감",
                        "❌ 친환경 기술수준 부족 → ✅ 친환경 기술수준 미흡"
                    ],
                    "중요도": "매우 높음"
                },
                {
                    "순위": 2,
                    "제목": "키워드를 최대한 많이 넣어라",
                    "설명": "채점자는 200명 답안을 빠르게 채점하므로, 키워드 중심으로 채점합니다.",
                    "예시": [
                        "정 모르겠으면 관련 키워드를 최대한 많이 작성",
                        "문제 지문에서 중요해 보이는 단어는 모두 포함"
                    ],
                    "중요도": "매우 높음"
                },
                {
                    "순위": 3,
                    "제목": "시험지 받으면 먼저 제목, 대제목 작성",
                    "설명": "문제에서 제목, 대제목 등 틀을 잡고 시작합니다.",
                    "예시": [
                        "1단계: 제목, 대제목 먼저 써놓기",
                        "2단계: 읽으면서 채워나가기"
                    ],
                    "중요도": "높음"
                },
                {
                    "순위": 4,
                    "제목": "CEO 메시지에서 추진배경과 향후 일정 추출",
                    "설명": "CEO 메시지는 주로 추진배경과 향후 일정을 언급합니다.",
                    "예시": [
                        "CEO가 '~를 하자' → 무조건 향후 계획",
                        "전사 행사, 토론회 등 → 향후 계획"
                    ],
                    "중요도": "높음"
                },
                {
                    "순위": 5,
                    "제목": "부장과 컴케에서 보고서 틀 확인",
                    "설명": "보통 2, 3번 보고서 틀이 잡히고, 주의사항도 언급됩니다.",
                    "예시": [
                        "부장: '추진방향은 A, B, C로 구분해서 작성하세요'",
                        "→ 이것까지 잡아놓고 시작!"
                    ],
                    "중요도": "높음"
                }
            ],
            "채점_방식_이해": {
                "논리정확성": "키워드 매칭 중심, 금지어 사용 시 감점 (40점)",
                "명확간결성": "S/A/B/C/D 등급, 불필요한 반복이나 장황한 표현 확인 (30점)",
                "완결성": "S/A/B/C/D 등급, 보고서 구조와 형식 확인 (30점)"
            },
            "작성_노하우": [
                {
                    "카테고리": "키워드 전략",
                    "팁": [
                        "문제에서 키워드를 잘 골라서 작성",
                        "최대한 문제에서 키워드를 추출",
                        "모든 단어는 문제지에 있는 단어만 사용"
                    ]
                },
                {
                    "카테고리": "구조 전략",
                    "팁": [
                        "전체적인 보고서 구성을 잘 갖추기",
                        "1, 2, 3 → □ → ○ → - 순서로 작성",
                        "제목 21자 이내, 본문 35자 이내"
                    ]
                }
            ],
            "금지사항": [
                "금지어 사용 (메신저/쪽지에서 확인)",
                "디지털 뉴딜, 한국판 뉴딜 등 타 사업 관련",
                "CEO 중심이 아닌 일정 작성"
            ],
            "4주_학습_계획": [
                {
                    "주차": "1주차",
                    "목표": "채점 방식 이해 및 기출문제 분석",
                    "활동": [
                        "채점 방식 문서 정독",
                        "작성 팁 문서 정독",
                        "기출문제 3개년 분석"
                    ],
                    "체크포인트": "채점 기준 3가지를 말할 수 있는가?"
                },
                {
                    "주차": "2주차",
                    "목표": "키워드 추출 연습 및 문제 분석 훈련",
                    "활동": [
                        "키워드 추출 연습",
                        "제시자료 유형별 특징 파악",
                        "기출문제 1개 작성"
                    ],
                    "체크포인트": "제시자료에서 키워드를 빠르게 찾을 수 있는가?"
                },
                {
                    "주차": "3주차",
                    "목표": "실전 연습 및 시간 관리",
                    "활동": [
                        "기출문제 2개 실전 연습 (150분)",
                        "자가 채점",
                        "자신만의 루틴 확립"
                    ],
                    "체크포인트": "150분 내에 26줄 답안을 완성할 수 있는가?"
                },
                {
                    "주차": "4주차",
                    "목표": "최종 점검 및 실전 감각 유지",
                    "활동": [
                        "기출문제 2~3개 추가 연습",
                        "약점 파트 집중 훈련",
                        "최신 전력산업 이슈 확인"
                    ],
                    "체크포인트": "모범답안에 가까운 답안을 작성할 수 있는가?"
                }
            ],
            "시험_당일_체크리스트": [
                "문제지 받으면 제목과 대제목을 먼저 작성",
                "CEO 메시지에서 추진배경과 향후 일정 체크",
                "처장/부장 이메일과 메신저에서 보고서 구조 확인",
                "제시자료를 읽으며 키워드에 형광펜 표시",
                "모든 키워드를 문제지에 있는 단어 그대로 사용",
                "금지어를 사용하지 않았는지 확인",
                "각 줄이 35자를 초과하지 않는지 확인",
                "총 26줄 이내로 작성",
                "보고서 구조가 명확한지 확인",
                "CEO 중심의 향후 일정 작성",
                "단순 키워드 나열이 아닌 논리적 문장",
                "제목은 21자 이내"
            ],
            "메시지": "기본 가이드입니다. 정확한 가이드를 위해 Claude API 키를 설정하세요."
        }

    def save_guide_to_file(
        self,
        guide_data: Dict,
        output_file: str = "/home/user/test/study_guide_v2.json"
    ):
        """
        가이드를 파일로 저장

        Args:
            guide_data: 가이드 데이터
            output_file: 출력 파일 경로
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(guide_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 가이드가 {output_file}에 저장되었습니다.")


def demo_study_guide_v2():
    """공부 가이드 V2 데모"""

    print("\n" + "="*70)
    print("📚 OPR 공부 노하우 시스템 V2 (Claude API 기반)")
    print("="*70 + "\n")

    try:
        guide_system = StudyGuideSystemV2()

        print("가이드 생성 중... (Claude API 사용)")
        print("참고: 채점 방식 및 작성 팁 PDF를 분석하여 가이드를 생성합니다.")
        print("")

        # 가이드 생성
        guide_data = guide_system.generate_comprehensive_guide()

        # 결과 출력
        formatted = guide_system.format_guide_for_display(guide_data)
        print(formatted)

        # 파일 저장
        guide_system.save_guide_to_file(guide_data)

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_study_guide_v2()
