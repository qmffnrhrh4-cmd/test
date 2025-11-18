#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 생성 유틸리티
reportlab을 사용한 한글 PDF 생성
"""

import os
from datetime import datetime
from typing import Dict, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    # Define dummy values for when reportlab is not available
    A4 = (595.27, 841.89)  # A4 size in points
    mm = 2.834645669  # mm to points conversion


class PDFGenerator:
    """PDF 생성기"""

    def __init__(self):
        if not PDF_AVAILABLE:
            raise ImportError("reportlab이 설치되지 않았습니다. 'pip install reportlab Pillow'를 실행하세요.")

        self.page_width, self.page_height = A4
        self.margin = 20 * mm
        self.font_loaded = False

    def _setup_fonts(self, c):
        """한글 폰트 설정"""
        if self.font_loaded:
            return

        # Windows 기본 폰트 경로 시도
        font_paths = [
            "C:\\Windows\\Fonts\\malgun.ttf",  # 맑은 고딕
            "C:\\Windows\\Fonts\\gulim.ttc",   # 굴림
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Linux
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('Korean', font_path))
                    self.font_loaded = True
                    print(f"[PDF] 폰트 로드 성공: {font_path}")
                    return
                except:
                    continue

        print("[PDF] 한글 폰트를 찾을 수 없습니다. 기본 폰트 사용")

    def generate_grading_result_pdf(self, result: Dict, filename: str) -> bool:
        """채점 결과 PDF 생성"""
        try:
            c = canvas.Canvas(filename, pagesize=A4)
            self._setup_fonts(c)

            # 폰트 설정
            if self.font_loaded:
                title_font = 'Korean'
                body_font = 'Korean'
            else:
                title_font = 'Helvetica-Bold'
                body_font = 'Helvetica'

            # 현재 y 위치
            y = self.page_height - self.margin

            # 제목
            c.setFont(title_font, 24)
            c.drawString(self.margin, y, "OPR 채점 결과")
            y -= 15 * mm

            # 날짜
            c.setFont(body_font, 10)
            date_str = datetime.now().strftime("%Y년 %m월 %d일")
            c.drawString(self.margin, y, f"채점일: {date_str}")
            y -= 10 * mm

            # 구분선
            c.setStrokeColor(colors.grey)
            c.setLineWidth(2)
            c.line(self.margin, y, self.page_width - self.margin, y)
            y -= 10 * mm

            # 총점 (크게)
            c.setFont(title_font, 20)
            c.setFillColor(colors.red)
            total_score = result.get('총점', 0)
            c.drawString(self.margin, y, f"총점: {total_score} / 100점")
            c.setFillColor(colors.black)
            y -= 15 * mm

            # 논리정확성
            y = self._draw_section(c, y, "논리·정확성", result.get('논리정확성', {}), title_font, body_font)

            # 페이지가 부족하면 새 페이지
            if y < 100 * mm:
                c.showPage()
                y = self.page_height - self.margin
                self._setup_fonts(c)

            # 명확간결성
            y = self._draw_section(c, y, "명확·간결성", result.get('명확간결성', {}), title_font, body_font)

            if y < 100 * mm:
                c.showPage()
                y = self.page_height - self.margin
                self._setup_fonts(c)

            # 완결성
            y = self._draw_section(c, y, "완결성", result.get('완결성', {}), title_font, body_font)

            if y < 100 * mm:
                c.showPage()
                y = self.page_height - self.margin
                self._setup_fonts(c)

            # 종합평가
            overall = result.get('종합_평가', {})
            if overall:
                y -= 5 * mm
                c.setFont(title_font, 14)
                c.drawString(self.margin, y, "종합 평가")
                y -= 7 * mm

                c.setFont(body_font, 10)
                if overall.get('강점'):
                    c.drawString(self.margin, y, "강점:")
                    y -= 5 * mm
                    for item in overall['강점'][:3]:
                        c.drawString(self.margin + 5 * mm, y, f"• {item[:60]}")
                        y -= 5 * mm

                if overall.get('약점'):
                    y -= 2 * mm
                    c.drawString(self.margin, y, "약점:")
                    y -= 5 * mm
                    for item in overall['약점'][:3]:
                        c.drawString(self.margin + 5 * mm, y, f"• {item[:60]}")
                        y -= 5 * mm

                if overall.get('다음_학습_방향'):
                    y -= 2 * mm
                    c.drawString(self.margin, y, f"다음 학습 방향: {overall['다음_학습_방향'][:70]}")
                    y -= 5 * mm

            # 하단
            c.setFont(body_font, 8)
            c.setFillColor(colors.grey)
            c.drawString(self.margin, 15 * mm, "OPR 자동 채점 시스템 - Gemini AI")

            c.save()
            print(f"[PDF] 채점 결과 PDF 생성 완료: {filename}")
            return True

        except Exception as e:
            print(f"[ERROR] PDF 생성 실패: {e}")
            return False

    def _draw_section(self, c, y, title, data, title_font, body_font):
        """섹션 그리기"""
        c.setFont(title_font, 14)
        score = data.get('점수', 0)
        grade = data.get('등급', '')

        if grade:
            c.drawString(self.margin, y, f"{title}: {grade}등급 ({score}점)")
        else:
            c.drawString(self.margin, y, f"{title}: {score}점")
        y -= 7 * mm

        c.setFont(body_font, 10)

        # 잘한 점
        if data.get('잘한_점'):
            c.setFillColor(colors.green)
            c.drawString(self.margin, y, "잘한 점:")
            c.setFillColor(colors.black)
            y -= 5 * mm
            for item in data['잘한_점'][:3]:
                c.drawString(self.margin + 5 * mm, y, f"• {item[:60]}")
                y -= 5 * mm

        # 부족한 점
        if data.get('부족한_점'):
            y -= 2 * mm
            c.setFillColor(colors.orange)
            c.drawString(self.margin, y, "부족한 점:")
            c.setFillColor(colors.black)
            y -= 5 * mm
            for item in data['부족한_점'][:3]:
                c.drawString(self.margin + 5 * mm, y, f"• {item[:60]}")
                y -= 5 * mm

        # 개선 방법
        if data.get('개선_방법'):
            y -= 2 * mm
            c.setFillColor(colors.blue)
            c.drawString(self.margin, y, "개선 방법:")
            c.setFillColor(colors.black)
            y -= 5 * mm
            for item in data['개선_방법'][:3]:
                c.drawString(self.margin + 5 * mm, y, f"• {item[:60]}")
                y -= 5 * mm

        # 피드백
        if data.get('피드백'):
            y -= 2 * mm
            c.drawString(self.margin, y, f"피드백: {data['피드백'][:70]}")
            y -= 5 * mm

        # 매칭 키워드 (논리정확성만)
        if title == "논리·정확성" and data.get('매칭된_키워드'):
            matched = data['매칭된_키워드']
            y -= 2 * mm
            c.drawString(self.margin, y, f"매칭된 키워드 ({len(matched)}개):")
            y -= 5 * mm
            keywords_str = ", ".join(matched[:10])
            if len(keywords_str) > 70:
                keywords_str = keywords_str[:70] + "..."
            c.drawString(self.margin + 5 * mm, y, keywords_str)
            y -= 5 * mm

        y -= 5 * mm
        return y


def test_pdf():
    """PDF 생성 테스트"""
    if not PDF_AVAILABLE:
        print("reportlab이 설치되지 않았습니다.")
        return

    # 테스트 데이터
    result = {
        "총점": 75.5,
        "논리정확성": {
            "점수": 32,
            "매칭된_키워드": ["키워드1", "키워드2", "키워드3"],
            "잘한_점": ["핵심 키워드 포함", "구체적인 수치 사용"],
            "부족한_점": ["일부 키워드 누락"],
            "피드백": "전반적으로 우수합니다."
        },
        "명확간결성": {
            "등급": "A",
            "점수": 25,
            "잘한_점": ["간결한 문장"],
            "부족한_점": [],
            "개선_방법": ["35자 제한 준수"],
            "피드백": "명확하고 간결합니다."
        },
        "완결성": {
            "등급": "B",
            "점수": 21,
            "잘한_점": ["기본 구조 갖춤"],
            "부족한_점": ["기호 미사용"],
            "개선_방법": ["□/○ 기호 사용"],
            "피드백": "보고서 형식을 더 갖추세요."
        },
        "종합_평가": {
            "강점": ["키워드 풍부", "논리적"],
            "약점": ["형식 미비"],
            "다음_학습_방향": "보고서 형식 연습"
        }
    }

    generator = PDFGenerator()
    generator.generate_grading_result_pdf(result, "test_result.pdf")
    print("테스트 PDF 생성 완료: test_result.pdf")


if __name__ == "__main__":
    test_pdf()
