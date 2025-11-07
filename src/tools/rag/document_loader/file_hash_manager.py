"""
파일 중복 체크 관리
MD5 해시를 사용해서 이미 로드된 파일인지 확인
"""
import hashlib
import os
from typing import Set

class FileHashManager:
    """
    파일 해시를 관리하여 중복 파일을 체크하는 클래스
    메모리에서 해시를 관리하여 중복 파일을 체크
    """
    def __init__(self):
        """
        FileHashManager 초기화
        로드된 파일의 해시를 저장할 집합(set) 생성
        """
        self.loaded_hashes: Set[str] = set()
    
    def get_file_hash(self, file_path: str) -> str:
        """
        파일의 MD5 해시를 계산하여 반환
        파일이 존재하지 않으면 None 반환
        """
        try:
            with open(file_path, 'rb') as file:
                file_content = file.read()
                hash_value = hashlib.md5(file_content).hexdigest()
                return hash_value
        except Exception as e:
            print(f"파일 해시 계산 실패: {file_path}, 오류: {e}")
            return ""
    
    def is_file_loaded(self, file_path: str) -> bool:
        """
        파일이 이미 로드된 것인지 확인합니다.

        Args:
            file_path: 확인할 파일의 경로
        
        returns:
            이미 로드된 파일이면 True, 아니면 False
        """
        if not os.path.exists(file_path):
            return False
        
        file_hash = self.get_file_hash(file_path)

        if not file_hash:
            return False

        return file_hash in self.get_file_hash

    def mark_as_loaded(self, file_path: str) -> None:
        """
        파일을 로드된 것으로 표시합니다.

        Args:
            file_path: 로드된 파일의 경로
        """
        file_hash = self.get_file_hash(file_path)

        if file_hash:
            self.loaded_hashes.add(file_hash)

    def clear(self) -> None:
        """
        저장된 모든 해시를 삭제합니다.
        """
        self.loaded_hashes.clear()

    def get_loaded_hashes(self) -> int:
        """
        현재 로드된 파일의 개수를 반환합니다.

        returns:
            로드된 파일의 개수
        """
        return len(self.loaded_hashes)

# 다른 모듈에서 이 인스턴스 사용 가능능
file_hash_manager = FileHashManager()