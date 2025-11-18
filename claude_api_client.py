#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude API 클라이언트 모듈
모든 AI 기능을 Claude API를 통해 처리
"""

import os
import json
from typing import Dict, List, Optional
from anthropic import Anthropic


class ClaudeAPIClient:
    """Claude API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        """
        API 클라이언트 초기화

        Args:
            api_key: Claude API 키 (없으면 환경변수에서 읽음)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Claude API 키가 필요합니다. "
                "환경변수 ANTHROPIC_API_KEY를 설정하거나 api_key 인자로 전달하세요."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def grade_answer_with_model_answer(
        self,
        student_answer: str,
        model_answer: str,
        keywords: List[str],
        forbidden_words: List[str]
    ) -> Dict:
        """
        모범답안과 비교하여 학생 답안 채점

        Args:
            student_answer: 학생 답안
            model_answer: 모범답안
            keywords: 필수 키워드 리스트
            forbidden_words: 금지어 리스트

        Returns:
            채점 결과 딕셔너리
        """

        prompt = f"""당신은 OPR(논술형 시험) 채점 전문가입니다.

다음 기준에 따라 학생 답안을 채점하고 상세한 피드백을 제공하세요.

【채점 기준】
1. 논리·정확성 (40점)
   - 모범답안의 키워드가 학생 답안에 포함되어 있는지 확인
   - 키워드 매칭률에 따라 점수 부여
   - 금지어 사용 시 1개당 2점 감점

2. 명확·간결성 (30점)
   - S/A/B/C/D 등급으로 평가
   - 불필요한 반복, 장황한 표현 확인
   - 35자 제한 준수 여부 확인
   - 키워드 나열식 작성 여부 확인

3. 완결성 (30점)
   - S/A/B/C/D 등급으로 평가
   - 보고서 구조 (제목, 1/2/3 대항목, □/○/- 중항목)
   - 최소 15줄 이상의 내용
   - 26줄 이내 제한 준수

【필수 키워드】
{json.dumps(keywords, ensure_ascii=False, indent=2)}

【금지어】
{json.dumps(forbidden_words, ensure_ascii=False, indent=2)}

【모범답안】
{model_answer}

【학생 답안】
{student_answer}

다음 JSON 형식으로 채점 결과를 반환하세요:
{{
  "논리정확성": {{
    "점수": 숫자 (0-40),
    "매칭된_키워드": ["키워드1", "키워드2", ...],
    "누락된_키워드": ["키워드1", "키워드2", ...],
    "발견된_금지어": ["금지어1", ...],
    "피드백": "상세 설명"
  }},
  "명확간결성": {{
    "등급": "S/A/B/C/D 중 하나",
    "점수": 숫자 (0-30),
    "피드백": "상세 설명"
  }},
  "완결성": {{
    "등급": "S/A/B/C/D 중 하나",
    "점수": 숫자 (0-30),
    "피드백": "상세 설명"
  }},
  "총점": 숫자 (0-100),
  "종합_피드백": "전체 답안에 대한 종합 평가 및 개선 방향"
}}

반드시 JSON 형식만 반환하고, 추가 설명은 붙이지 마세요."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result_text = response.content[0].text
            # JSON 추출 (```json ... ``` 형태로 올 수 있음)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            return {
                "error": str(e),
                "총점": 0,
                "종합_피드백": f"채점 중 오류가 발생했습니다: {str(e)}"
            }

    def generate_exam_from_references(
        self,
        reference_exams: List[str],
        difficulty: str = "medium",
        topic: Optional[str] = None
    ) -> Dict:
        """
        실제 기출문제를 참고하여 새로운 연습 문제 생성

        Args:
            reference_exams: 참고할 기출문제 리스트
            difficulty: 난이도 (easy/medium/hard)
            topic: 주제 (없으면 자동 생성)

        Returns:
            생성된 문제 딕셔너리
        """

        refs_text = "\n\n==========\n\n".join(reference_exams[:3])  # 최대 3개만

        difficulty_desc = {
            "easy": "쉬움 - 명확한 키워드와 구조",
            "medium": "보통 - 실제 시험 수준",
            "hard": "어려움 - 복잡한 구조와 많은 제시자료"
        }

        topic_instruction = f"주제: {topic}" if topic else "주제는 최신 전력/에너지 산업 트렌드에서 선택"

        prompt = f"""당신은 OPR 문제 출제 전문가입니다.

아래 기출문제들을 참고하여 새로운 연습 문제를 생성하세요.

【기출문제 참고자료】
{refs_text}

【생성 조건】
- 난이도: {difficulty_desc.get(difficulty, "보통")}
- {topic_instruction}
- 실제 OPR 문제와 동일한 형식 (상황, 과제, 제시자료, 작성 유의사항 등)
- CEO 메시지, 처장/부장 이메일, 메신저 대화 등 다양한 제시자료 포함

다음 JSON 형식으로 문제를 생성하세요:
{{
  "문제_제목": "보고서 제목",
  "상황_설명": "배경 상황",
  "과제_설명": "작성해야 할 보고서 내용",
  "보고서_구성": ["추진배경", "추진방향", "대응전략", "향후계획"],
  "제시자료": [
    {{
      "번호": 1,
      "유형": "CEO 소통 메시지",
      "내용": "실제 제시자료 내용..."
    }},
    ...최소 8개
  ],
  "필수_키워드": ["키워드1", "키워드2", ...],
  "금지어": ["금지어1", "금지어2", ...],
  "예상_작성_시간": "150분",
  "출제_의도": "이 문제의 출제 의도 설명"
}}

반드시 JSON 형식만 반환하고, 추가 설명은 붙이지 마세요."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result_text = response.content[0].text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            return {
                "error": str(e),
                "문제_제목": "문제 생성 실패",
                "상황_설명": f"문제 생성 중 오류: {str(e)}"
            }

    def generate_study_guide_from_documents(
        self,
        grading_guide: str,
        writing_tips: str
    ) -> Dict:
        """
        채점 기준 및 작성 팁 문서를 기반으로 공부 가이드 생성

        Args:
            grading_guide: 채점 방식 문서 내용
            writing_tips: 작성 팁 문서 내용

        Returns:
            공부 가이드 딕셔너리
        """

        prompt = f"""당신은 OPR 시험 준비 전문 컨설턴트입니다.

아래 문서들을 분석하여 수험생을 위한 종합 공부 가이드를 작성하세요.

【채점 방식 문서】
{grading_guide[:5000]}  # 너무 길면 제한

【작성 팁 문서】
{writing_tips[:5000]}

다음 JSON 형식으로 가이드를 작성하세요:
{{
  "핵심_전략_TOP5": [
    {{
      "순위": 1,
      "제목": "전략 제목",
      "설명": "상세 설명",
      "예시": ["예시1", "예시2"],
      "중요도": "매우 높음/높음/보통"
    }},
    ...
  ],
  "채점_방식_이해": {{
    "논리정확성": "설명...",
    "명확간결성": "설명...",
    "완결성": "설명..."
  }},
  "작성_노하우": [
    {{
      "카테고리": "키워드 전략/구조 전략/시간 관리 등",
      "팁": ["팁1", "팁2", ...]
    }},
    ...
  ],
  "금지사항": [
    "금지사항1",
    "금지사항2",
    ...
  ],
  "4주_학습_계획": [
    {{
      "주차": "1주차",
      "목표": "목표",
      "활동": ["활동1", "활동2", ...],
      "체크포인트": "확인사항"
    }},
    ...
  ],
  "시험_당일_체크리스트": [
    "체크항목1",
    "체크항목2",
    ...
  ]
}}

반드시 JSON 형식만 반환하고, 추가 설명은 붙이지 마세요."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=6000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result_text = response.content[0].text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            return {
                "error": str(e),
                "핵심_전략_TOP5": [],
                "종합_메시지": f"가이드 생성 중 오류: {str(e)}"
            }

    def analyze_model_answers(
        self,
        model_answers: List[str]
    ) -> Dict:
        """
        여러 모범답안을 분석하여 패턴 추출

        Args:
            model_answers: 모범답안 리스트

        Returns:
            분석 결과 딕셔너리
        """

        answers_text = "\n\n=====답안 구분=====\n\n".join(model_answers[:5])

        prompt = f"""당신은 OPR 답안 분석 전문가입니다.

아래 모범답안들을 분석하여 공통 패턴과 특징을 추출하세요.

【모범답안들】
{answers_text}

다음 JSON 형식으로 분석 결과를 반환하세요:
{{
  "공통_구조_패턴": {{
    "제목_특징": "설명",
    "대항목_구성": ["항목1", "항목2", ...],
    "중항목_특징": "설명"
  }},
  "자주_사용되는_키워드": [
    "키워드1", "키워드2", ...
  ],
  "문장_패턴": [
    "패턴1 예시",
    "패턴2 예시",
    ...
  ],
  "고득점_작성_팁": [
    "팁1",
    "팁2",
    ...
  ]
}}

반드시 JSON 형식만 반환하고, 추가 설명은 붙이지 마세요."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result_text = response.content[0].text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            return {
                "error": str(e),
                "공통_구조_패턴": {},
                "메시지": f"분석 중 오류: {str(e)}"
            }


def test_api_client():
    """API 클라이언트 테스트"""

    try:
        client = ClaudeAPIClient()
        print("✅ Claude API 클라이언트 초기화 성공")

        # 간단한 테스트
        test_result = client.grade_answer_with_model_answer(
            student_answer="테스트 답안입니다.",
            model_answer="모범 답안입니다.",
            keywords=["테스트", "키워드"],
            forbidden_words=["금지어"]
        )

        print(f"\n테스트 채점 결과: {json.dumps(test_result, ensure_ascii=False, indent=2)}")
        return True

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


if __name__ == "__main__":
    test_api_client()
