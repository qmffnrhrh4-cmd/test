#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 자동 채점 시스템
- 키워드 기반 자동 채점
- 금지어 감점 처리
- 정성평가 요소 분석
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
import json


@dataclass
class GradingCriteria:
    """채점 기준"""
    required_keywords: List[str]  # 필수 키워드 (가점)
    forbidden_keywords: List[str]  # 금지어 (감점)
    max_logic_score: int = 40  # 논리·정확성 최대 점수
    max_clarity_score: int = 30  # 명확·간결성 최대 점수
    max_completeness_score: int = 30  # 완결성 최대 점수


@dataclass
class GradingResult:
    """채점 결과"""
    logic_score: float  # 논리·정확성 점수
    clarity_score: str  # 명확·간결성 등급 (S/A/B/C/D)
    completeness_score: str  # 완결성 등급 (S/A/B/C/D)
    total_score: float  # 총점
    feedback: List[str]  # 피드백
    keyword_matches: Dict[str, int]  # 키워드 매칭 결과
    forbidden_found: List[str]  # 발견된 금지어


class AutoGradingSystem:
    """자동 채점 시스템"""

    def __init__(self):
        self.grade_to_score = {
            'S': 1.0,
            'A': 0.85,
            'B': 0.70,
            'C': 0.55,
            'D': 0.40
        }

    def extract_keywords_from_answer(self, answer_text: str) -> List[str]:
        """답안에서 키워드 추출"""
        # 공백 제거 후 명사/동사 패턴 추출
        words = re.findall(r'[\w]+', answer_text.replace(' ', ''))
        return words

    def calculate_logic_score(
        self,
        answer_text: str,
        criteria: GradingCriteria
    ) -> Tuple[float, Dict[str, int], List[str]]:
        """논리·정확성 점수 계산 (키워드 기반)"""

        # 답안 텍스트 정규화 (공백 제거)
        normalized_answer = answer_text.replace(' ', '')

        # 키워드 매칭
        keyword_matches = {}
        for keyword in criteria.required_keywords:
            normalized_keyword = keyword.replace(' ', '')
            count = normalized_answer.count(normalized_keyword)
            if count > 0:
                keyword_matches[keyword] = count

        # 금지어 체크
        forbidden_found = []
        for forbidden in criteria.forbidden_keywords:
            normalized_forbidden = forbidden.replace(' ', '')
            if normalized_forbidden in normalized_answer:
                forbidden_found.append(forbidden)

        # 점수 계산
        match_rate = len(keyword_matches) / len(criteria.required_keywords) if criteria.required_keywords else 0
        base_score = criteria.max_logic_score * match_rate

        # 금지어 감점 (금지어 1개당 -2점)
        penalty = len(forbidden_found) * 2
        final_score = max(0, base_score - penalty)

        return final_score, keyword_matches, forbidden_found

    def evaluate_clarity(self, answer_text: str) -> Tuple[str, List[str]]:
        """명확·간결성 평가"""
        feedback = []
        score = 85  # 기본 점수

        # 불필요한 반복 체크
        repeated_words = self._check_repetition(answer_text)
        if repeated_words:
            score -= 10
            feedback.append(f"반복되는 단어 발견: {', '.join(repeated_words[:3])}")

        # 문장 길이 체크 (35자 제한)
        lines = answer_text.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line.replace(' ', '')) > 35]
        if long_lines:
            score -= 5
            feedback.append(f"35자 초과 줄: {long_lines[:3]}")

        # 키워드 나열식 작성 체크
        if self._is_keyword_listing(answer_text):
            score -= 10
            feedback.append("단순 키워드 나열식 작성으로 보임")

        # 등급 변환
        if score >= 90:
            grade = 'S'
        elif score >= 80:
            grade = 'A'
        elif score >= 70:
            grade = 'B'
        elif score >= 60:
            grade = 'C'
        else:
            grade = 'D'

        return grade, feedback

    def evaluate_completeness(self, answer_text: str) -> Tuple[str, List[str]]:
        """완결성 평가"""
        feedback = []
        score = 85  # 기본 점수

        # 보고서 구조 체크
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

        # 내용의 완결성 체크 (최소 줄 수)
        lines = [l for l in answer_text.split('\n') if l.strip()]
        if len(lines) < 15:
            score -= 10
            feedback.append(f"내용이 부족함 (총 {len(lines)}줄)")

        # 등급 변환
        if score >= 90:
            grade = 'S'
        elif score >= 80:
            grade = 'A'
        elif score >= 70:
            grade = 'B'
        elif score >= 60:
            grade = 'C'
        else:
            grade = 'D'

        return grade, feedback

    def _check_repetition(self, text: str) -> List[str]:
        """반복되는 단어 체크"""
        words = re.findall(r'[\w]{2,}', text)
        word_count = {}
        for word in words:
            if len(word) >= 2:  # 2글자 이상만
                word_count[word] = word_count.get(word, 0) + 1

        # 5번 이상 반복되는 단어
        repeated = [w for w, c in word_count.items() if c >= 5]
        return repeated

    def _is_keyword_listing(self, text: str) -> bool:
        """키워드 나열식인지 체크"""
        # 짧은 문장이 많으면 키워드 나열식으로 판단
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        short_lines = [l for l in lines if len(l) < 15]
        return len(short_lines) / len(lines) > 0.5 if lines else False

    def grade_answer(
        self,
        answer_text: str,
        criteria: GradingCriteria
    ) -> GradingResult:
        """답안 채점"""

        # 1. 논리·정확성 채점
        logic_score, keyword_matches, forbidden_found = self.calculate_logic_score(
            answer_text, criteria
        )

        # 2. 명확·간결성 평가
        clarity_grade, clarity_feedback = self.evaluate_clarity(answer_text)

        # 3. 완결성 평가
        completeness_grade, completeness_feedback = self.evaluate_completeness(answer_text)

        # 4. 총점 계산
        clarity_score = criteria.max_clarity_score * self.grade_to_score[clarity_grade]
        completeness_score = criteria.max_completeness_score * self.grade_to_score[completeness_grade]
        total_score = logic_score + clarity_score + completeness_score

        # 5. 피드백 생성
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


def demo_grading():
    """채점 시스템 데모"""

    # 예시 채점 기준
    criteria = GradingCriteria(
        required_keywords=[
            "전력망 건설지연", "발전제약 해소", "법령 제개정", "시공기간 단축",
            "전력망혁신위원회", "전원촉진법", "입지선정위원회", "협의간주제",
            "NWAs", "계통안정화용 ESS", "유연송전설비", "고객참여 부하차단",
            "WAMS", "동적 송전용량", "신규 장비 도입", "해외인력 확보"
        ],
        forbidden_keywords=[
            "HVDC", "디지털 뉴딜", "한국판 뉴딜", "코로나", "재택근무"
        ]
    )

    # 예시 답안
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

    # 채점 실행
    system = AutoGradingSystem()
    result = system.grade_answer(sample_answer, criteria)

    # 결과 출력
    print("\n" + "="*60)
    print("📝 OPR 자동 채점 시스템")
    print("="*60)
    print("\n".join(result.feedback))

    return result


if __name__ == "__main__":
    result = demo_grading()
