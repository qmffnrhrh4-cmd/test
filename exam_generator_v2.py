#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPR 자동 문제지 생성 시스템 V2
Claude API를 활용한 실제 문제지 패턴 기반 생성
"""

import os
import json
from typing import Dict, List, Optional
from claude_api_client import ClaudeAPIClient
from pdf_utils import PDFExtractor


class ExamGeneratorV2:
    """문제지 생성기 V2 - Claude API 기반"""

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화

        Args:
            api_key: Claude API 키
        """
        try:
            self.api_client = ClaudeAPIClient(api_key)
            self.pdf_extractor = PDFExtractor()
            self.exams_dir = "./문제지"
            self.api_available = True
        except Exception as e:
            print(f"⚠️ Claude API 초기화 실패: {e}")
            print("기본 문제 생성 모드로 작동합니다.")
            self.api_available = False
            self.pdf_extractor = PDFExtractor()
            self.exams_dir = "./문제지"

    def load_reference_exams(self, count: int = 3) -> List[str]:
        """
        참고할 기출문제 로드

        Args:
            count: 로드할 문제 수

        Returns:
            기출문제 텍스트 리스트
        """
        if not os.path.exists(self.exams_dir):
            return []

        exams = self.pdf_extractor.load_exams_from_folder(self.exams_dir)

        # 최신 문제부터
        sorted_files = sorted(
            exams.keys(),
            reverse=True
        )

        reference_exams = []
        for filename in sorted_files[:count]:
            reference_exams.append(exams[filename])

        return reference_exams

    def generate_practice_exam(
        self,
        difficulty: str = "medium",
        topic: Optional[str] = None,
        use_api: bool = True
    ) -> Dict:
        """
        연습 문제 생성

        Args:
            difficulty: 난이도 (easy/medium/hard)
            topic: 주제 (선택)
            use_api: API 사용 여부

        Returns:
            생성된 문제 딕셔너리
        """
        if not use_api or not self.api_available:
            return self._generate_basic_exam(difficulty, topic)

        # 참고 문제 로드
        reference_exams = self.load_reference_exams(count=3)

        if not reference_exams:
            print("⚠️ 참고 문제를 찾을 수 없습니다. 기본 모드로 생성합니다.")
            return self._generate_basic_exam(difficulty, topic)

        # Claude API로 문제 생성
        result = self.api_client.generate_exam_from_references(
            reference_exams=reference_exams,
            difficulty=difficulty,
            topic=topic
        )

        return result

    def generate_full_exam_document(
        self,
        exam_data: Dict,
        output_file: Optional[str] = None
    ) -> str:
        """
        완전한 문제지 문서 생성

        Args:
            exam_data: 문제 데이터
            output_file: 출력 파일 경로 (선택)

        Returns:
            문제지 텍스트
        """
        output = []

        # 헤더
        output.append("="*80)
        output.append("2025년 3직급 일반승진 역량평가 연습 문제지")
        output.append("="*80)
        output.append("")

        # 문제 제목
        output.append("【문 제】")
        output.append("")
        output.append(f"제목: {exam_data.get('문제_제목', '')}")
        output.append("")

        # 상황 설명
        output.append("1. 보고서 작성배경 및 상황")
        output.append("-" * 80)
        output.append("")
        output.append(f"□ {exam_data.get('상황_설명', '')}")
        output.append("")

        # 과제 설명
        output.append(f"□ {exam_data.get('과제_설명', '')}")
        output.append("")

        # 보고서 구성
        output.append("2. 보고서 작성 및 평가기준")
        output.append("-" * 80)
        output.append("")
        composition = exam_data.get('보고서_구성', [])
        if composition:
            output.append(f"□ 다음 항목으로 구성된 보고서를 작성하시오:")
            for item in composition:
                output.append(f"   - {item}")
        output.append("")

        # 평가 기준
        output.append("□ 작성 및 평가 주요기준")
        output.append("  ○ 논리·정확성 (40점): 보고서 전체의 논리가 일관되고 구체적 근거에 의거하여 작성")
        output.append("  ○ 명확·간결성 (30점): 불필요한 정보 없이 핵심내용 위주로 명확·간결하게 작성")
        output.append("  ○ 완결성 (30점): 보고 목적에 부합하는 구성으로 완결된 형식의 보고서를 작성")
        output.append("")

        # 제시자료
        materials = exam_data.get('제시자료', [])
        if materials:
            output.append("3. 제시자료")
            output.append("-" * 80)
            output.append("")

            for material in materials:
                mat_num = material.get('번호', 0)
                mat_type = material.get('유형', '')
                mat_content = material.get('내용', '')

                output.append(f"【제시자료 {mat_num}】 {mat_type}")
                output.append("")
                output.append(mat_content)
                output.append("")
                output.append("-" * 80)
                output.append("")

        # 작성 유의사항
        output.append("4. 작성 유의사항")
        output.append("-" * 80)
        output.append("")
        output.append("□ 배점 (총 100점 만점)")
        output.append("")
        output.append("  항 목      | 논리·정확성 | 명확·간결성 | 완결성 | 합 계")
        output.append("  ----------|------------|-----------|--------|-------")
        output.append("  배 점      |     40     |     30    |   30   | 100점")
        output.append("")

        output.append("□ 작성 유의사항 (아래의 기준과 다르게 작성된 답안은 감점될 수 있음)")
        output.append("  ○ 총 26줄 이내의 개조식으로 작성")
        output.append("  ○ 글자체 및 글자크기")
        output.append("    - 제 목: HY헤드라인M, 21포인트, 최대 21자")
        output.append("    - 본 문: 신명조, 13포인트, 최대 35자(순수 글자수)")
        output.append("")

        # 참고사항
        keywords = exam_data.get('필수_키워드', [])
        if keywords:
            output.append("【참고】 필수 키워드 (채점 기준)")
            output.append("-" * 80)
            for i, kw in enumerate(keywords, 1):
                output.append(f"  {i}. {kw}")
            output.append("")

        forbidden = exam_data.get('금지어', [])
        if forbidden:
            output.append("【주의】 금지어 (사용 시 감점)")
            output.append("-" * 80)
            for word in forbidden:
                output.append(f"  ⚠️ {word}")
            output.append("")

        output.append("="*80)
        output.append(f"예상 작성 시간: {exam_data.get('예상_작성_시간', '150분')}")
        output.append("="*80)

        result = "\n".join(output)

        # 파일 저장
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ 문제지가 {output_file}에 저장되었습니다.")

        return result

    def _generate_basic_exam(self, difficulty: str, topic: Optional[str]) -> Dict:
        """
        기본 문제 생성 (API 없을 때)

        Args:
            difficulty: 난이도
            topic: 주제

        Returns:
            문제 딕셔너리
        """
        topics = {
            "easy": {
                "문제_제목": "디지털 전환 가속화 대응전략",
                "상황_설명": "4차 산업혁명 시대 대응을 위한 디지털 전환 필요성 증대",
                "필수_키워드": ["디지털전환", "AI활용", "데이터분석", "자동화"]
            },
            "medium": {
                "문제_제목": "탄소중립 달성을 위한 추진전략",
                "상황_설명": "2050 탄소중립 목표 달성을 위한 구체적 실행방안 마련 필요",
                "필수_키워드": ["탄소중립", "온실가스감축", "재생에너지", "ESG경영"]
            },
            "hard": {
                "문제_제목": "전력시장 개편 대응방안",
                "상황_설명": "전력시장 구조 개편에 따른 회사 차원의 대응 전략 수립 필요",
                "필수_키워드": ["전력시장개편", "경쟁체제", "수익성개선", "사업다각화"]
            }
        }

        selected = topics.get(difficulty, topics["medium"])

        return {
            "문제_제목": topic if topic else selected["문제_제목"],
            "상황_설명": selected["상황_설명"],
            "과제_설명": f"{selected['문제_제목']} 관련 대응전략을 수립하여 보고할 것",
            "보고서_구성": ["추진배경", "추진방향", "대응전략", "향후계획"],
            "제시자료": [
                {
                    "번호": 1,
                    "유형": "CEO 소통 메시지",
                    "내용": "(기본 모드: 실제 제시자료는 API 모드에서 생성됩니다)"
                }
            ],
            "필수_키워드": selected["필수_키워드"],
            "금지어": ["디지털 뉴딜", "한국판 뉴딜", "코로나"],
            "예상_작성_시간": "150분",
            "출제_의도": "기본 생성 모드입니다. 정확한 문제 생성을 위해 Claude API 키를 설정하세요."
        }

    def save_exam_to_folder(
        self,
        exam_data: Dict,
        folder_path: str = "./생성된_문제"
    ) -> str:
        """
        생성된 문제를 폴더에 저장

        Args:
            exam_data: 문제 데이터
            folder_path: 저장 폴더 경로

        Returns:
            저장된 파일 경로
        """
        # 폴더 생성
        os.makedirs(folder_path, exist_ok=True)

        # 파일명 생성
        title = exam_data.get('문제_제목', '연습문제')
        filename = f"{title.replace(' ', '_')}.txt"
        filepath = os.path.join(folder_path, filename)

        # 문제지 생성 및 저장
        self.generate_full_exam_document(exam_data, filepath)

        # JSON도 저장
        json_filepath = filepath.replace('.txt', '.json')
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(exam_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON 파일도 저장되었습니다: {json_filepath}")

        return filepath


def demo_exam_generation_v2():
    """문제 생성 V2 데모"""

    print("\n" + "="*70)
    print("📄 OPR 자동 문제지 생성 시스템 V2 (Claude API 기반)")
    print("="*70 + "\n")

    try:
        generator = ExamGeneratorV2()

        print("문제 생성 중... (Claude API 사용)")
        print("참고: 실제 기출문제를 분석하여 유사한 형식으로 생성합니다.")
        print("")

        # 문제 생성
        exam_data = generator.generate_practice_exam(
            difficulty="medium",
            topic=None  # 자동 선택
        )

        if "error" in exam_data:
            print(f"❌ 오류: {exam_data['error']}")
            return

        # 결과 출력
        print("✅ 문제 생성 완료!")
        print("")
        print(f"📌 제목: {exam_data.get('문제_제목', '')}")
        print(f"📝 상황: {exam_data.get('상황_설명', '')[:100]}...")
        print(f"📊 제시자료 수: {len(exam_data.get('제시자료', []))}개")
        print(f"🔑 필수 키워드: {len(exam_data.get('필수_키워드', []))}개")
        print("")

        # 폴더에 저장
        saved_path = generator.save_exam_to_folder(exam_data)
        print(f"\n✅ 문제가 저장되었습니다: {saved_path}")

        # 전체 문제지 미리보기
        print("\n" + "="*70)
        print("【문제지 미리보기】")
        print("="*70)

        full_doc = generator.generate_full_exam_document(exam_data)
        print(full_doc[:1000] + "\n\n... (이하 생략) ...")

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_exam_generation_v2()
