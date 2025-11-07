#!/usr/bin/env python
"""
부동산 정책 분석 시스템 실행 스크립트
간단한 CLI 인터페이스 제공
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 시스템 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_estate_policy_agent import (
    SmartPDFLoader,
    PolicyRetriever,
    PolicyAnalysisAgent
)

from langchain.chat_models import ChatOpenAI
import yaml


def setup_environment():
    """환경 변수 및 디렉토리 설정"""
    # OpenAI API 키 확인
    if not os.environ.get("OPENAI_API_KEY"):
        api_key = input("OpenAI API Key를 입력하세요: ")
        os.environ["OPENAI_API_KEY"] = api_key
    
    # 필요한 디렉토리 생성
    dirs_to_create = [
        Path("/home/claude/uploads"),
        Path("/home/claude/outputs"),
        Path("/home/claude/cache"),
        Path("/home/claude/logs")
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ 환경 설정 완료")


def load_additional_pdf(pdf_path: str, loader: SmartPDFLoader):
    """추가 PDF 파일 로드"""
    if not os.path.exists(pdf_path):
        print(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
        return None
    
    try:
        doc = loader.load_pdf(pdf_path)
        print(f"✅ PDF 로드 성공: {doc.title}")
        print(f"   - 날짜: {doc.policy_date}")
        print(f"   - 유형: {doc.policy_type.value}")
        print(f"   - 페이지 수: {len(doc.content.split('[페이지'))} 페이지")
        return doc
    except Exception as e:
        print(f"❌ PDF 로드 실패: {e}")
        return None


def run_comparison_analysis(
    pdf_files: list,
    target_area: str,
    main_type: str,
    total_units: int,
    output_path: str = None
):
    """정책 비교 분석 실행"""
    
    print("\n" + "="*60)
    print("🏘️  부동산 정책 비교 분석 시작")
    print("="*60)
    
    # 1. PDF 로더 초기화
    print("\n[1/5] PDF 로더 초기화...")
    pdf_loader = SmartPDFLoader()
    
    # 2. PDF 파일 로드
    print("\n[2/5] PDF 파일 로드 중...")
    policy_docs = []
    
    for pdf_file in pdf_files:
        doc = load_additional_pdf(pdf_file, pdf_loader)
        if doc:
            policy_docs.append(doc)
    
    if not policy_docs:
        print("❌ 로드된 PDF 파일이 없습니다.")
        return
    
    print(f"\n📚 총 {len(policy_docs)}개 정책 문서 로드 완료")
    
    # 3. Retriever 초기화
    print("\n[3/5] 검색 시스템 초기화...")
    
    # PostgreSQL 연결 (데모용 SQLite 사용)
    connection_string = "sqlite:///policy_vectors.db"
    
    retriever = PolicyRetriever(connection_string)
    retriever.initialize_vectorstore(policy_docs)
    print("✅ 벡터 저장소 생성 완료")
    
    # 4. Agent 초기화
    print("\n[4/5] 분석 Agent 초기화...")
    
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-4",
        max_tokens=2000
    )
    
    agent = PolicyAnalysisAgent(retriever, llm)
    
    # YAML 프롬프트 로드
    yaml_path = "/home/claude/policy_prompt.yaml"
    if os.path.exists(yaml_path):
        agent.load_yaml_prompt(yaml_path)
        print("✅ YAML 프롬프트 로드 완료")
    
    # 5. 보고서 생성
    print("\n[5/5] 비교 분석 보고서 생성 중...")
    print(f"   - 사업지: {target_area}")
    print(f"   - 주력 평형: {main_type}")
    print(f"   - 세대수: {total_units}")
    
    try:
        report = agent.generate_comparison_report(
            policy_files=pdf_files,
            target_area=target_area,
            main_type=main_type,
            total_units=total_units
        )
        
        # 보고서 저장
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/home/claude/outputs/policy_report_{timestamp}.md"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n✅ 보고서 생성 완료!")
        print(f"📄 저장 위치: {output_path}")
        
        # 보고서 미리보기
        print("\n" + "="*60)
        print("📋 보고서 미리보기 (첫 500자)")
        print("="*60)
        print(report[:500] + "...")
        
    except Exception as e:
        print(f"❌ 보고서 생성 실패: {e}")
        import traceback
        traceback.print_exc()


def interactive_mode():
    """대화형 모드"""
    print("\n🤖 부동산 정책 분석 시스템 - 대화형 모드")
    print("-" * 60)
    
    # PDF 파일 선택
    print("\n📁 분석할 PDF 파일을 선택하세요:")
    print("1. 기본 파일 사용 (uploads 폴더)")
    print("2. 직접 경로 입력")
    
    choice = input("\n선택 (1-2): ")
    
    if choice == "1":
        pdf_files = [
            "/mnt/user-data/uploads/251015_대출수요_관리_강화_방안_주요_FAQ.pdf",
            "/mnt/user-data/uploads/251015_주택시장_안정화_대책.pdf",
            "/mnt/user-data/uploads/0627.pdf"
        ]
    else:
        pdf_files = []
        while True:
            path = input("PDF 경로 입력 (완료시 엔터): ").strip()
            if not path:
                break
            pdf_files.append(path)
    
    # 사업 정보 입력
    print("\n🏘️  사업 정보를 입력하세요:")
    target_area = input("사업지 (예: 강남구): ")
    main_type = input("주력 평형 (예: 84㎡): ")
    total_units = int(input("총 세대수 (예: 500): "))
    
    # 분석 실행
    run_comparison_analysis(
        pdf_files=pdf_files,
        target_area=target_area,
        main_type=main_type,
        total_units=total_units
    )


def batch_mode(config_file: str):
    """배치 모드 - 설정 파일 기반 실행"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    for job in config['jobs']:
        print(f"\n🔄 배치 작업: {job['name']}")
        
        run_comparison_analysis(
            pdf_files=job['pdf_files'],
            target_area=job['target_area'],
            main_type=job['main_type'],
            total_units=job['total_units'],
            output_path=job.get('output_path')
        )


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='부동산 정책 비교 분석 시스템'
    )
    
    parser.add_argument(
        '--mode',
        choices=['interactive', 'batch', 'quick'],
        default='interactive',
        help='실행 모드 선택'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='배치 모드용 설정 파일 경로'
    )
    
    parser.add_argument(
        '--pdf',
        nargs='+',
        help='분석할 PDF 파일 경로들'
    )
    
    parser.add_argument(
        '--area',
        type=str,
        default='강남구',
        help='사업지 위치'
    )
    
    parser.add_argument(
        '--type',
        type=str,
        default='84㎡',
        help='주력 평형'
    )
    
    parser.add_argument(
        '--units',
        type=int,
        default=500,
        help='총 세대수'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='출력 파일 경로'
    )
    
    args = parser.parse_args()
    
    # 환경 설정
    setup_environment()
    
    # 모드별 실행
    if args.mode == 'interactive':
        interactive_mode()
    
    elif args.mode == 'batch':
        if not args.config:
            print("❌ 배치 모드는 --config 파일이 필요합니다.")
            sys.exit(1)
        batch_mode(args.config)
    
    elif args.mode == 'quick':
        # 빠른 실행 모드
        pdf_files = args.pdf or [
            "/mnt/user-data/uploads/251015_대출수요_관리_강화_방안_주요_FAQ.pdf",
            "/mnt/user-data/uploads/251015_주택시장_안정화_대책.pdf",
            "/mnt/user-data/uploads/0627.pdf"
        ]
        
        run_comparison_analysis(
            pdf_files=pdf_files,
            target_area=args.area,
            main_type=args.type,
            total_units=args.units,
            output_path=args.output
        )


if __name__ == "__main__":
    main()
