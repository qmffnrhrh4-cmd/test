#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 유틸리티 모듈
PDF 파일에서 텍스트 추출
"""

import os
from typing import List, Dict, Optional
from PyPDF2 import PdfReader


class PDFExtractor:
    """PDF 텍스트 추출기"""

    def __init__(self, pdf_dir: str = "./"):
        self.pdf_dir = pdf_dir

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        PDF 파일에서 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            추출된 텍스트
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""

            for page in reader.pages:
                text += page.extract_text() + "\n"

            return text.strip()

        except Exception as e:
            return f"PDF 읽기 오류: {str(e)}"

    def load_model_answers_from_folder(self, folder_path: str) -> Dict[str, str]:
        """
        모범답안 폴더에서 모든 PDF 읽기

        Args:
            folder_path: 모범답안 폴더 경로

        Returns:
            {파일명: 텍스트} 딕셔너리
        """
        model_answers = {}

        if not os.path.exists(folder_path):
            return model_answers

        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                text = self.extract_text_from_pdf(pdf_path)
                model_answers[filename] = text

        return model_answers

    def load_exams_from_folder(self, folder_path: str) -> Dict[str, str]:
        """
        문제지 폴더에서 모든 PDF 읽기

        Args:
            folder_path: 문제지 폴더 경로

        Returns:
            {파일명: 텍스트} 딕셔너리
        """
        exams = {}

        if not os.path.exists(folder_path):
            return exams

        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                text = self.extract_text_from_pdf(pdf_path)
                exams[filename] = text

        return exams

    def get_grading_guides(self, folder_path: str) -> Dict[str, str]:
        """
        채점 관련 PDF 파일들 읽기

        Args:
            folder_path: 모범답안 폴더 경로

        Returns:
            {문서 유형: 텍스트} 딕셔너리
        """
        guides = {}

        if not os.path.exists(folder_path):
            return guides

        # 특정 파일들 찾기
        target_files = {
            "채점방식": "OPR 채점방식.pdf",
            "작성팁": "OPR 작성 팁.pdf"
        }

        for key, filename in target_files.items():
            pdf_path = os.path.join(folder_path, filename)
            if os.path.exists(pdf_path):
                text = self.extract_text_from_pdf(pdf_path)
                guides[key] = text

        return guides

    def get_specific_model_answers(
        self,
        folder_path: str,
        year: Optional[str] = None,
        session: Optional[str] = None
    ) -> List[str]:
        """
        특정 연도/교시의 모범답안 가져오기

        Args:
            folder_path: 모범답안 폴더 경로
            year: 연도 (예: "25년")
            session: 교시 (예: "1교시")

        Returns:
            모범답안 텍스트 리스트
        """
        answers = []

        if not os.path.exists(folder_path):
            return answers

        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                # 필터링
                if year and year not in filename:
                    continue
                if session and session not in filename:
                    continue

                # "고득점" 파일만 (채점기준 제외)
                if "고득점" in filename and "채점기준" not in filename:
                    pdf_path = os.path.join(folder_path, filename)
                    text = self.extract_text_from_pdf(pdf_path)
                    answers.append(text)

        return answers


def demo_pdf_extraction():
    """PDF 추출 데모"""

    extractor = PDFExtractor()

    print("\n" + "="*70)
    print("📄 PDF 추출 데모")
    print("="*70 + "\n")

    # 모범답안 폴더
    model_answers_dir = "./모범답안"
    if os.path.exists(model_answers_dir):
        print("【1】 모범답안 폴더 분석")
        print("-" * 70)

        # 채점 가이드 읽기
        guides = extractor.get_grading_guides(model_answers_dir)
        for key, text in guides.items():
            print(f"\n• {key} 문서 추출: {len(text)}자")
            print(f"  미리보기: {text[:200]}...")

        # 특정 연도 모범답안 읽기
        answers_25 = extractor.get_specific_model_answers(
            model_answers_dir,
            year="25년",
            session="1교시"
        )
        print(f"\n• 25년 1교시 모범답안: {len(answers_25)}개")
        if answers_25:
            print(f"  첫 번째 답안 미리보기: {answers_25[0][:200]}...")

    # 문제지 폴더
    exams_dir = "./문제지"
    if os.path.exists(exams_dir):
        print("\n\n【2】 문제지 폴더 분석")
        print("-" * 70)

        exams = extractor.load_exams_from_folder(exams_dir)
        print(f"• 문제지 파일 수: {len(exams)}개")

        for filename in list(exams.keys())[:3]:
            print(f"\n• {filename}: {len(exams[filename])}자")
            print(f"  미리보기: {exams[filename][:200]}...")

    print("\n" + "="*70)
    print("✅ PDF 추출 완료")
    print("="*70 + "\n")


if __name__ == "__main__":
    demo_pdf_extraction()
