from typing import List, Optional, Union, Iterable, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    PDFPlumberLoader,
    UnstructuredPDFLoader,
)
from langchain_community.document_loaders import  MathpixPDFLoader
from langchain_docling import DoclingLoader

from PyPDF2 import PdfReader
from langchain_core.documents import Document
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType

#  DoclingLoader (AI 기반, 꽤 잘나감)
def load_with_docling(
    file_paths: Union[str, Iterable[str]],
    export_type: ExportType = ExportType.DOC_CHUNKS,
    convert_kwargs: Optional[Dict[str, Any]] = None,
    md_export_kwargs: Optional[Dict[str, Any]] = None,
    chunker: Optional[Any] = None,
    meta_extractor: Optional[Any] = None,
    **kwargs: Any
) -> list[Document]:
    """
    DoclingLoader 기반 로더 함수
    - file_paths: 단일 파일 경로나 파일 리스트
    - export_type: DOC_CHUNKS or MARKDOWN
    - 나머 옵션: convert_kwargs, md_export_kwargs, chunker, meta_extractor
    """
    loader = DoclingLoader(
        file_path=file_paths,
        export_type=export_type,
        convert_kwargs=convert_kwargs,
        md_export_kwargs=md_export_kwargs,
        chunker=chunker,
        meta_extractor=meta_extractor,
        **kwargs
    )
    return loader.load()

# PyMuPDFLoader (속도+정확도 균형, OCR 불필요)
def load_with_pymupdf(
    path: str,
    **kwargs
) -> List[Document]:
    loader = PyMuPDFLoader(
        file_path=path,
        **kwargs
    )
    return loader.load()


# UnstructuredPDFLoader (OCR/테이블/이미지 자동 감지)
def load_with_unstructured(
    path: str,
    mode: str = "elements",
    strategy: str = "auto",  # "auto" | "hi_res" | "ocr_only"
    ocr_languages: str = "eng+kor",
    hi_res_model_name: str = "detectron2_onnx",
    **kwargs,
) -> List[Document]:
    """
    - OCR + 테이블 + 이미지 분석 자동
    - 텍스트 레이어 없는 PDF 자동 감지 후 OCR 수행
    """
    loader = UnstructuredPDFLoader(
        file_path=path,
        mode=mode,
        strategy=strategy,
        ocr_languages=ocr_languages,
        hi_res_model_name=hi_res_model_name,
        **kwargs,
    )
    return loader.load()


# PDFPlumberLoader (표 구조 전문)
def load_with_pdfplumber(
    path: str,
    **kwargs,
) -> List[Document]:
    """
    - 표, 컬럼 구조 분석에 강함
    - OCR 불필요, 데이터 테이블이 많은 문서용
    """
    loader = PDFPlumberLoader(
        path,
        **kwargs,
    )
    return loader.load()


# MathpixPDFLoader (논문/수식에 특화)
def load_with_mathpix(
    path: str,
    app_id: Optional[str] = None,
    app_key: Optional[str] = None,
    format: str = "markdown",
    **kwargs,
) -> List[Document]:
    """
    🧮 MathpixPDFLoader
    - Mathpix OCR API 활용
    - 수식, 그래프, 논문에 강함
    - 출력: Markdown / Text / HTML 선택 가능
    """
    loader = MathpixPDFLoader(
        file_path=path,
        format=format,
        mathpix_app_id=app_id,
        mathpix_app_key=app_key,
        **kwargs,
    )
    return loader.load()


# ─────────────────────────────────────────────────────────────
# Adaptive Loader (자동 감지형, 실무에서 제일 많이 씀)
# ─────────────────────────────────────────────────────────────
def has_text_layer(pdf_path: str) -> bool:
    """텍스트 레이어 감지 (OCR 필요 여부 판단)"""
    try:
        reader = PdfReader(pdf_path)
        for pg in reader.pages[:2]:
            txt = pg.extract_text()
            if txt and len(txt.strip()) > 50:
                return True
    except Exception:
        pass
    return False


def adaptive_loader(path: str) -> List[Document]:
    """
    - 텍스트 레이어 있으면: PyMuPDFLoader
    - 없으면: DoclingLoader → Unstructured 순 fallback
    """
    try:
        if has_text_layer(path):
            return load_with_pymupdf(path)
        try:
            return load_with_docling(path)
        except Exception:
            return load_with_unstructured(path)
    except Exception as e:
        print(f"[⚠️] 모든 로더 실패: {e}")
        raise


def best_loader(path: str) -> List[Document]:
    """
    순서대로 시도:
    1. DoclingLoader → 실패하면
    2. PDFPlumberLoader → 실패하면
    3. PyMuPDFLoader → 실패하면
    4. UnstructuredPDFLoader
    """
    try:
        print("DoclingLoader 사용")
        return load_with_docling(path, export_type=ExportType.DOC_CHUNKS)
    except Exception as e1:
        print(f"DoclingLoader 실패: {e1}")
        try:
            print("PDFPlumberLoader 사용")
            return load_with_pdfplumber(path)
        except Exception as e2:

            print(f"PDFPlumberLoader 실패: {e2}")
            try:
                print("PyMuPDFLoader 사용")
                return load_with_pymupdf(path)
            except Exception as e3:
                print(f"PyMuPDFLoader 실패: {e3}")
                print("UnstructuredPDFLoader 사용")
                return load_with_unstructured(path)

