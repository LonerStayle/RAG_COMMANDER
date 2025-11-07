"""
통합 파일 로더
PDF, 마크다운, JSON 파일을 모두 지원하는 통합 로더입니다.
"""

import os
import json
import re
from typing import Dict, Any
from pathlib import Path

from tools.rag.document_loader.policy_pdf_loader import (
    PolicyPDFLoader,
    PolicyDocument,
    PolicyType
)
from tools.rag.document_loader.file_hash_manager import file_hash_manager


class PolicyFileLoader:
    """
    다양한 형식의 정책 파일을 로드하는 통합 로더
    PDF, 마크다운, JSON 파일을 지원합니다.
    """
    
    def __init__(self):
        """
        PolicyFileLoader 초기화
        PDF 로더를 내부적으로 사용합니다.
        """
        self.pdf_loader = PolicyPDFLoader()
    
    def load_file(self, file_path: str) -> PolicyDocument:
        """
        파일 형식에 따라 적절한 로더를 사용하여 파일을 로드합니다.
        
        Args:
            file_path: 로드할 파일의 경로
            
        Returns:
            PolicyDocument 객체
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 지원하지 않는 파일 형식일 때
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # 파일 확장자 확인
        file_ext = Path(file_path).suffix.lower()
        
        # 파일 형식에 따라 적절한 로더 사용
        if file_ext == '.pdf':
            return self._load_pdf(file_path)
        elif file_ext in ['.md', '.markdown']:
            return self._load_markdown(file_path)
        elif file_ext == '.json':
            return self._load_json(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_ext}")
    
    def _load_pdf(self, file_path: str) -> PolicyDocument:
        """
        PDF 파일을 로드합니다.
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            PolicyDocument 객체
        """
        return self.pdf_loader.load_pdf(file_path)
    
    def _load_markdown(self, file_path: str) -> PolicyDocument:
        """
        마크다운 파일을 로드합니다.
        
        Args:
            file_path: 마크다운 파일 경로
            
        Returns:
            PolicyDocument 객체
        """
        # 중복 파일 체크
        if file_hash_manager.is_file_loaded(file_path):
            print(f"이미 로드된 파일입니다: {file_path}")
        
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 메타데이터 추출
        policy_date = self._extract_date_from_content(content, file_path)
        policy_type = self._determine_policy_type(content, file_path)
        title = self._extract_title_from_content(content, file_path)
        
        # 메타데이터 준비
        metadata = {
            "source": file_path,
            "policy_date": policy_date,
            "policy_type": policy_type.value,
            "title": title,
            "file_type": "markdown"
        }
        
        # 파일을 로드된 것으로 표시
        file_hash_manager.mark_as_loaded(file_path)
        
        # PolicyDocument 생성
        policy_doc = PolicyDocument(
            file_path=file_path,
            policy_date=policy_date,
            policy_type=policy_type,
            title=title,
            content=content,
            metadata=metadata
        )
        
        return policy_doc
    
    def _load_json(self, file_path: str) -> PolicyDocument:
        """
        JSON 파일을 로드합니다.
        
        Args:
            file_path: JSON 파일 경로
            
        Returns:
            PolicyDocument 객체
        """
        # 중복 파일 체크
        if file_hash_manager.is_file_loaded(file_path):
            print(f"이미 로드된 파일입니다: {file_path}")
        
        # JSON 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        # JSON을 텍스트로 변환
        content = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        # 메타데이터 추출
        policy_date = json_data.get('date', self._extract_date_from_content(content, file_path))
        policy_type = self._determine_policy_type(content, file_path)
        title = json_data.get('title', self._extract_title_from_content(content, file_path))
        
        # 메타데이터 준비
        metadata = {
            "source": file_path,
            "policy_date": policy_date,
            "policy_type": policy_type.value,
            "title": title,
            "file_type": "json",
            "json_data": json_data
        }
        
        # 파일을 로드된 것으로 표시
        file_hash_manager.mark_as_loaded(file_path)
        
        # PolicyDocument 생성
        policy_doc = PolicyDocument(
            file_path=file_path,
            policy_date=policy_date,
            policy_type=policy_type,
            title=title,
            content=content,
            metadata=metadata
        )
        
        return policy_doc
    
    def _extract_date_from_content(self, content: str, file_path: str) -> str:
        """
        파일 내용에서 날짜를 추출합니다.
        
        Args:
            content: 파일 내용
            file_path: 파일 경로
            
        Returns:
            추출된 날짜 문자열 (없으면 "날짜 미상")
        """
        # 파일명에서 날짜 추출 시도
        file_name = os.path.basename(file_path)
        file_date_match = re.search(r'(\d{6}|\d{4}\.\d{1,2}\.\d{1,2})', file_name)
        
        if file_date_match:
            return file_date_match.group(1)
        
        # 문서 내용 앞부분에서 날짜 패턴 찾기
        date_patterns = [
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)',
            r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})',
            r'(\d{2}\.\s*\d{1,2}\.\s*\d{1,2})'
        ]
        
        content_start = content[:1000]
        
        for pattern in date_patterns:
            match = re.search(pattern, content_start)
            if match:
                return match.group(1)
        
        return "날짜 미상"
    
    def _determine_policy_type(self, content: str, file_path: str) -> PolicyType:
        """
        정책 문서의 유형을 자동으로 판별합니다.
        
        Args:
            content: 문서 내용
            file_path: 파일 경로
            
        Returns:
            PolicyType 열거형 값
        """
        content_lower = content.lower()
        file_lower = file_path.lower()
        
        # 대출 규제 관련 키워드 확인
        loan_keywords = ['대출', 'ltv', 'dsr', 'dti', '대출수요']
        has_loan_keyword = False
        for keyword in loan_keywords:
            if keyword in content_lower or keyword in file_lower:
                has_loan_keyword = True
                break
        
        if has_loan_keyword:
            return PolicyType.LOAN_REGULATION
        
        # 주택시장 관련 키워드 확인
        housing_keywords = ['주택시장', '부동산시장', '주택가격']
        has_housing_keyword = False
        for keyword in housing_keywords:
            if keyword in content_lower or keyword in file_lower:
                has_housing_keyword = True
                break
        
        if has_housing_keyword:
            return PolicyType.HOUSING_MARKET
        
        # 세제 관련 키워드 확인
        tax_keywords = ['세제', '취득세', '재산세', '양도세']
        has_tax_keyword = False
        for keyword in tax_keywords:
            if keyword in content_lower or keyword in file_lower:
                has_tax_keyword = True
                break
        
        if has_tax_keyword:
            return PolicyType.TAX_POLICY
        
        # 공급 관련 키워드 확인
        supply_keywords = ['공급', '분양', '입주']
        has_supply_keyword = False
        for keyword in supply_keywords:
            if keyword in content_lower or keyword in file_lower:
                has_supply_keyword = True
                break
        
        if has_supply_keyword:
            return PolicyType.SUPPLY_POLICY
        
        # 기본값
        return PolicyType.UNKNOWN
    
    def _extract_title_from_content(self, content: str, file_path: str) -> str:
        """
        파일 내용에서 제목을 추출합니다.
        
        Args:
            content: 파일 내용
            file_path: 파일 경로
            
        Returns:
            추출된 제목 문자열
        """
        # 파일명에서 제목 추출
        file_name = os.path.basename(file_path)
        title_from_file = file_name.replace('.md', '').replace('.json', '').replace('.markdown', '')
        title_from_file = re.sub(r'\d+_?', '', title_from_file)
        title_from_file = title_from_file.replace('_', ' ').strip()
        
        # 문서 내용에서 제목 찾기 (마크다운 헤더 또는 첫 번째 긴 라인)
        lines = content.split('\n')
        
        for line in lines[:20]:
            line_stripped = line.strip()
            line_length = len(line_stripped)
            
            # 마크다운 헤더 확인 (#으로 시작)
            if line_stripped.startswith('#'):
                title_candidate = line_stripped.lstrip('#').strip()
                if title_candidate:
                    return title_candidate
            
            # 적절한 길이의 라인인지 확인
            if line_length < 10 or line_length > 100:
                continue
            
            # 제목으로 사용 가능한 라인 발견
            return line_stripped
        
        # 문서에서 제목을 찾지 못한 경우 파일명 사용
        return title_from_file


# 전역 인스턴스 생성
policy_file_loader = PolicyFileLoader()