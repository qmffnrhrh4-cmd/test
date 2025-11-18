#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 자동 채점 시스템 V2
Claude API를 활용한 정확한 채점
모범답안 파일과 비교하여 채점
"""

import os
import json
from typing import Dict, List, Optional
from claude_api_client import ClaudeAPIClient
from pdf_utils import PDFExtractor


class AutoGradingSystemV2:
    """자동 채점 시스템 V2 - Claude API 기반"""

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
            print("기본 채점 모드로 작동합니다.")
            self.api_available = False
            self.pdf_extractor = PDFExtractor()
            self.model_answers_dir = "./모범답안"

    def load_model_answer_by_problem(
        self,
        problem_title: str,
        year: Optional[str] = None
    ) -> Optional[str]:
        """
        문제 제목으로 모범답안 찾기

        Args:
            problem_title: 문제 제목
            year: 연도 (예: "25년")

        Returns:
            모범답안 텍스트 (없으면 None)
        """
        if not os.path.exists(self.model_answers_dir):
            return None

        # 연도 지정된 경우 해당 연도 모범답안 찾기
        model_answers = self.pdf_extractor.get_specific_model_answers(
            self.model_answers_dir,
            year=year
        )

        # 가장 최근 모범답안 반환
        return model_answers[0] if model_answers else None

    def get_latest_model_answers(self, count: int = 3) -> List[str]:
        """
        최신 모범답안 가져오기

        Args:
            count: 가져올 개수

        Returns:
            모범답안 리스트
        """
        all_answers = []

        # 연도별로 수집
        for year in ["25년", "24년", "23년", "22년", "21년"]:
            answers = self.pdf_extractor.get_specific_model_answers(
                self.model_answers_dir,
                year=year
            )
            all_answers.extend(answers)

            if len(all_answers) >= count:
                break

        return all_answers[:count]

    def grade_with_model_answer(
        self,
        student_answer: str,
        model_answer: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        forbidden_words: Optional[List[str]] = None
    ) -> Dict:
        """
        모범답안과 비교하여 채점

        Args:
            student_answer: 학생 답안
            model_answer: 모범답안 (없으면 자동 로드)
            keywords: 필수 키워드
            forbidden_words: 금지어

        Returns:
            채점 결과 딕셔너리
        """
        # API 사용 불가능한 경우 기본 채점
        if not self.api_available:
            return self._basic_grading(student_answer, keywords, forbidden_words)

        # 모범답안 없으면 최신 것 사용
        if model_answer is None:
            model_answers = self.get_latest_model_answers(1)
            model_answer = model_answers[0] if model_answers else "모범답안 없음"

        # 키워드 기본값
        if keywords is None:
            keywords = self._extract_default_keywords()

        if forbidden_words is None:
            forbidden_words = self._get_default_forbidden_words()

        # Claude API로 채점
        result = self.api_client.grade_answer_with_model_answer(
            student_answer=student_answer,
            model_answer=model_answer,
            keywords=keywords,
            forbidden_words=forbidden_words
        )

        return result

    def grade_from_file(
        self,
        answer_file_path: str,
        model_answer_file_path: Optional[str] = None
    ) -> Dict:
        """
        파일에서 답안 읽어서 채점

        Args:
            answer_file_path: 학생 답안 파일 경로 (.txt, .pdf)
            model_answer_file_path: 모범답안 파일 경로 (선택)

        Returns:
            채점 결과
        """
        # 학생 답안 읽기
        if answer_file_path.endswith('.pdf'):
            student_answer = self.pdf_extractor.extract_text_from_pdf(answer_file_path)
        else:
            with open(answer_file_path, 'r', encoding='utf-8') as f:
                student_answer = f.read()

        # 모범답안 읽기
        model_answer = None
        if model_answer_file_path:
            if model_answer_file_path.endswith('.pdf'):
                model_answer = self.pdf_extractor.extract_text_from_pdf(
                    model_answer_file_path
                )
            else:
                with open(model_answer_file_path, 'r', encoding='utf-8') as f:
                    model_answer = f.read()

        return self.grade_with_model_answer(
            student_answer=student_answer,
            model_answer=model_answer
        )

    def _extract_default_keywords(self) -> List[str]:
        """기본 키워드 추출"""
        return [
            "전력망 건설지연", "발전제약 해소", "법령 제개정", "시공기간 단축",
            "전력망혁신위원회", "전원촉진법", "입지선정위원회", "협의간주제",
            "NWAs", "계통안정화용 ESS", "유연송전설비", "고객참여 부하차단",
            "WAMS", "동적 송전용량", "신규 장비 도입", "해외인력 확보"
        ]

    def _get_default_forbidden_words(self) -> List[str]:
        """기본 금지어"""
        return [
            "HVDC", "디지털 뉴딜", "한국판 뉴딜", "코로나", "재택근무"
        ]

    def _basic_grading(
        self,
        student_answer: str,
        keywords: Optional[List[str]],
        forbidden_words: Optional[List[str]]
    ) -> Dict:
        """
        기본 채점 (API 없을 때)

        Args:
            student_answer: 학생 답안
            keywords: 키워드 리스트
            forbidden_words: 금지어 리스트

        Returns:
            채점 결과
        """
        if keywords is None:
            keywords = self._extract_default_keywords()
        if forbidden_words is None:
            forbidden_words = self._get_default_forbidden_words()

        # 간단한 키워드 매칭
        matched = []
        missing = []
        for keyword in keywords:
            if keyword.replace(' ', '') in student_answer.replace(' ', ''):
                matched.append(keyword)
            else:
                missing.append(keyword)

        # 금지어 체크
        forbidden_found = []
        for word in forbidden_words:
            if word in student_answer:
                forbidden_found.append(word)

        # 점수 계산
        logic_score = 40 * (len(matched) / len(keywords)) if keywords else 0
        logic_score = max(0, logic_score - len(forbidden_found) * 2)

        return {
            "논리정확성": {
                "점수": round(logic_score, 1),
                "매칭된_키워드": matched,
                "누락된_키워드": missing,
                "발견된_금지어": forbidden_found,
                "피드백": f"{len(matched)}/{len(keywords)}개 키워드 매칭"
            },
            "명확간결성": {
                "등급": "B",
                "점수": 21.0,
                "피드백": "기본 평가 (API 미사용)"
            },
            "완결성": {
                "등급": "B",
                "점수": 21.0,
                "피드백": "기본 평가 (API 미사용)"
            },
            "총점": round(logic_score + 42.0, 1),
            "종합_피드백": "기본 채점 모드입니다. 정확한 채점을 위해 Claude API 키를 설정하세요."
        }

    def format_result_for_display(self, result: Dict) -> str:
        """
        채점 결과를 보기 좋게 포맷팅

        Args:
            result: 채점 결과 딕셔너리

        Returns:
            포맷팅된 문자열
        """
        output = []
        output.append("="*70)
        output.append("📊 채점 결과")
        output.append("="*70)
        output.append("")

        if "error" in result:
            output.append(f"❌ 오류: {result['error']}")
            return "\n".join(output)

        # 총점
        output.append(f"🎯 총점: {result.get('총점', 0)}/100점")
        output.append("")

        # 논리·정확성
        logic = result.get("논리정확성", {})
        output.append(f"【1】 논리·정확성: {logic.get('점수', 0)}/40점")
        output.append("-" * 70)

        matched = logic.get("매칭된_키워드", [])
        missing = logic.get("누락된_키워드", [])
        forbidden = logic.get("발견된_금지어", [])

        output.append(f"✅ 매칭된 키워드 ({len(matched)}개):")
        if matched:
            for kw in matched[:10]:  # 최대 10개만
                output.append(f"   - {kw}")
            if len(matched) > 10:
                output.append(f"   ... 외 {len(matched)-10}개")

        if missing:
            output.append(f"\n❌ 누락된 키워드 ({len(missing)}개):")
            for kw in missing[:10]:
                output.append(f"   - {kw}")
            if len(missing) > 10:
                output.append(f"   ... 외 {len(missing)-10}개")

        if forbidden:
            output.append(f"\n⚠️ 금지어 발견 (-{len(forbidden)*2}점):")
            for word in forbidden:
                output.append(f"   - {word}")

        output.append(f"\n💬 피드백: {logic.get('피드백', '')}")
        output.append("")

        # 명확·간결성
        clarity = result.get("명확간결성", {})
        output.append(f"【2】 명확·간결성: {clarity.get('등급', '-')}등급 ({clarity.get('점수', 0)}/30점)")
        output.append("-" * 70)
        output.append(f"💬 피드백: {clarity.get('피드백', '')}")
        output.append("")

        # 완결성
        completeness = result.get("완결성", {})
        output.append(f"【3】 완결성: {completeness.get('등급', '-')}등급 ({completeness.get('점수', 0)}/30점)")
        output.append("-" * 70)
        output.append(f"💬 피드백: {completeness.get('피드백', '')}")
        output.append("")

        # 종합 피드백
        output.append("【종합 피드백】")
        output.append("=" * 70)
        output.append(result.get("종합_피드백", ""))
        output.append("")
        output.append("="*70)

        return "\n".join(output)


def demo_grading_v2():
    """채점 시스템 V2 데모"""

    print("\n" + "="*70)
    print("📝 OPR 자동 채점 시스템 V2 (Claude API 기반)")
    print("="*70 + "\n")

    try:
        grader = AutoGradingSystemV2()

        # 샘플 답안
        sample_answer = """전력망 건설 지연 대응전략 보고서

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

        print("채점 중... (Claude API 사용)")
        print("")

        result = grader.grade_with_model_answer(student_answer)

        # 결과 출력
        formatted = grader.format_result_for_display(result)
        print(formatted)

        # JSON 저장
        output_file = "/home/user/test/grading_result_v2.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 채점 결과가 {output_file}에 저장되었습니다.")

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_grading_v2()
