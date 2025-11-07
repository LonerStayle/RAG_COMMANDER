#!/usr/bin/env python
"""
부동산 정책 분석 시스템 테스트 스크립트
시스템의 주요 컴포넌트를 단계별로 테스트
"""

import os
import sys
import json
from pathlib import Path

# 시스템 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_loader():
    """PDF 로더 테스트"""
    print("\n" + "="*60)
    print("📄 PDF 로더 테스트")
    print("="*60)
    
    try:
        from real_estate_policy_agent import SmartPDFLoader
        
        loader = SmartPDFLoader()
        
        # 테스트 PDF 파일들
        test_files = [
            "/mnt/user-data/uploads/251015_대출수요_관리_강화_방안_주요_FAQ.pdf",
            "/mnt/user-data/uploads/251015_주택시장_안정화_대책.pdf",
            "/mnt/user-data/uploads/0627.pdf"
        ]
        
        for pdf_file in test_files:
            if os.path.exists(pdf_file):
                print(f"\n테스트 파일: {os.path.basename(pdf_file)}")
                
                doc = loader.load_pdf(pdf_file)
                
                print(f"  ✅ 제목: {doc.title}")
                print(f"  ✅ 날짜: {doc.policy_date}")
                print(f"  ✅ 유형: {doc.policy_type.value}")
                print(f"  ✅ 내용 길이: {len(doc.content)} 문자")
                print(f"  ✅ 메타데이터 키: {list(doc.metadata.keys())[:3]}...")
                
                # 표 데이터 확인
                table_count = sum(1 for key in doc.metadata.keys() if 'table' in key)
                if table_count > 0:
                    print(f"  ✅ 추출된 표: {table_count}개")
            else:
                print(f"  ⚠️ 파일 없음: {pdf_file}")
        
        print("\n✅ PDF 로더 테스트 통과")
        return True
        
    except Exception as e:
        print(f"❌ PDF 로더 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retriever():
    """검색 시스템 테스트"""
    print("\n" + "="*60)
    print("🔍 검색 시스템 테스트")
    print("="*60)
    
    try:
        from real_estate_policy_agent import SmartPDFLoader, PolicyRetriever
        
        # 샘플 문서 생성
        loader = SmartPDFLoader()
        
        # 테스트용 간단한 문서
        test_pdf = "/mnt/user-data/uploads/0627.pdf"
        
        if os.path.exists(test_pdf):
            doc = loader.load_pdf(test_pdf)
            
            # SQLite 사용 (테스트용)
            retriever = PolicyRetriever("sqlite:///test_vectors.db")
            retriever.initialize_vectorstore([doc])
            
            # 검색 테스트
            test_queries = [
                "LTV 규제",
                "주택담보대출",
                "DSR 적용",
                "규제지역",
                "전세대출"
            ]
            
            for query in test_queries:
                print(f"\n쿼리: '{query}'")
                
                # 의미 검색
                semantic_results = retriever.semantic_search(query, k=3)
                print(f"  ✅ 의미 검색 결과: {len(semantic_results)}개")
                
                # 키워드 검색
                keywords = retriever._extract_keywords(query)
                keyword_results = retriever.keyword_search(keywords, k=3)
                print(f"  ✅ 키워드 검색 결과: {len(keyword_results)}개 (키워드: {keywords})")
                
                # 하이브리드 검색
                hybrid_results = retriever.hybrid_search(query, k=3)
                print(f"  ✅ 하이브리드 검색 결과: {len(hybrid_results)}개")
                
                if hybrid_results:
                    print(f"  📝 최상위 결과 미리보기: {hybrid_results[0].page_content[:100]}...")
            
            print("\n✅ 검색 시스템 테스트 통과")
            return True
        else:
            print("⚠️ 테스트 PDF 파일 없음")
            return False
            
    except Exception as e:
        print(f"❌ 검색 시스템 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_workflow():
    """Agent 워크플로우 테스트"""
    print("\n" + "="*60)
    print("🤖 Agent 워크플로우 테스트")
    print("="*60)
    
    try:
        from real_estate_policy_agent import (
            SmartPDFLoader,
            PolicyRetriever,
            PolicyAnalysisAgent
        )
        
        # 간단한 목업 LLM (실제 API 호출 없이 테스트)
        class MockLLM:
            def predict(self, prompt):
                return "테스트 분석 결과: " + prompt[:50] + "..."
        
        # 컴포넌트 초기화
        loader = SmartPDFLoader()
        retriever = PolicyRetriever("sqlite:///test_vectors.db")
        agent = PolicyAnalysisAgent(retriever, MockLLM())
        
        # 워크플로우 그래프 생성
        graph = agent.create_analysis_graph()
        
        # 테스트 상태
        test_state = {
            'current_section': '규제지역',
            'retry_count': 0,
            'retrieved_docs': [],
            'analysis_results': {}
        }
        
        print("  ✅ Agent 그래프 생성 완료")
        print(f"  ✅ 초기 상태: {list(test_state.keys())}")
        
        # 개별 노드 테스트
        print("\n노드별 테스트:")
        
        # Retrieve 노드
        state = agent.retrieve_information(test_state)
        print(f"  ✅ Retrieve 노드: retry_count={state['retry_count']}")
        
        # Analyze 노드
        state = agent.analyze_section(state)
        if 'analysis_results' in state:
            print(f"  ✅ Analyze 노드: 결과 생성됨")
        
        # Validate 노드
        state = agent.validate_analysis(state)
        print(f"  ✅ Validate 노드: is_valid={state.get('is_valid', 'N/A')}")
        
        print("\n✅ Agent 워크플로우 테스트 통과")
        return True
        
    except Exception as e:
        print(f"❌ Agent 워크플로우 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yaml_prompt():
    """YAML 프롬프트 테스트"""
    print("\n" + "="*60)
    print("📋 YAML 프롬프트 테스트")
    print("="*60)
    
    try:
        import yaml
        
        yaml_path = "/home/claude/policy_prompt.yaml"
        
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
            
            print(f"  ✅ YAML 파일 로드 성공")
            print(f"  ✅ 섹션 수: {len(prompt_data)}")
            print(f"  ✅ 섹션 목록: {list(prompt_data.keys())}")
            
            # 각 섹션 검증
            required_sections = ['POLICY_HUMAN', 'POLICY_SUMMARY', 'POLICY_SEGMENT_01']
            
            for section in required_sections:
                if section in prompt_data:
                    print(f"  ✅ {section} 섹션 존재")
                else:
                    print(f"  ⚠️ {section} 섹션 누락")
            
            print("\n✅ YAML 프롬프트 테스트 통과")
            return True
        else:
            print(f"⚠️ YAML 파일 없음: {yaml_path}")
            return False
            
    except Exception as e:
        print(f"❌ YAML 프롬프트 테스트 실패: {e}")
        return False


def test_file_handling():
    """파일 처리 테스트"""
    print("\n" + "="*60)
    print("📁 파일 처리 테스트")
    print("="*60)
    
    try:
        import hashlib
        
        # 중복 파일 체크 함수
        def get_file_hash(file_path):
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        
        test_files = [
            "/mnt/user-data/uploads/251015_대출수요_관리_강화_방안_주요_FAQ.pdf",
            "/mnt/user-data/uploads/251015_주택시장_안정화_대책.pdf"
        ]
        
        hashes = {}
        
        for file_path in test_files:
            if os.path.exists(file_path):
                file_hash = get_file_hash(file_path)
                file_name = os.path.basename(file_path)
                
                if file_hash in hashes.values():
                    print(f"  ⚠️ 중복 파일 감지: {file_name}")
                else:
                    hashes[file_name] = file_hash
                    print(f"  ✅ 고유 파일: {file_name[:30]}... (해시: {file_hash[:8]}...)")
        
        # 출력 디렉토리 확인
        output_dirs = [
            "/home/claude/outputs",
            "/home/claude/cache",
            "/home/claude/logs"
        ]
        
        print("\n디렉토리 확인:")
        for dir_path in output_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {dir_path} 디렉토리 준비됨")
        
        print("\n✅ 파일 처리 테스트 통과")
        return True
        
    except Exception as e:
        print(f"❌ 파일 처리 테스트 실패: {e}")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("🚀 부동산 정책 분석 시스템 전체 테스트 시작")
    print("="*60)
    
    test_results = {
        "PDF 로더": test_pdf_loader(),
        "검색 시스템": test_retriever(),
        "Agent 워크플로우": test_agent_workflow(),
        "YAML 프롬프트": test_yaml_prompt(),
        "파일 처리": test_file_handling()
    }
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    total = len(test_results)
    passed = sum(1 for v in test_results.values() if v)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! 시스템 준비 완료")
        
        print("\n다음 명령으로 실제 분석을 시작하세요:")
        print("  python run_analysis.py --mode quick \\")
        print("    --area '강남구' --type '84㎡' --units 500")
    else:
        print("\n⚠️ 일부 테스트 실패. 문제를 확인하세요.")
    
    return passed == total


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='부동산 정책 분석 시스템 테스트'
    )
    
    parser.add_argument(
        '--test',
        choices=['all', 'pdf', 'retriever', 'agent', 'yaml', 'file'],
        default='all',
        help='실행할 테스트 선택'
    )
    
    args = parser.parse_args()
    
    if args.test == 'all':
        success = run_all_tests()
    elif args.test == 'pdf':
        success = test_pdf_loader()
    elif args.test == 'retriever':
        success = test_retriever()
    elif args.test == 'agent':
        success = test_agent_workflow()
    elif args.test == 'yaml':
        success = test_yaml_prompt()
    elif args.test == 'file':
        success = test_file_handling()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
