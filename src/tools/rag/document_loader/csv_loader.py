from langchain_community.document_loaders import CSVLoader
from typing import  Union,Optional,Sequence,Dict
from pathlib import Path

def load_csv_loader(file_path: Union[str, Path],
                    encoding: Optional[str] = None,
                    source_column: Optional[str] = None,
                    metadata_columns: Sequence[str] = (),
                    csv_args: Optional[Dict] = None,
                    autodetect_encoding: bool = False,
                    content_columns: Sequence[str] = ()):
    return CSVLoader(
        file_path=file_path,
        encoding=encoding,        
        source_column = source_column,
        metadata_columns = metadata_columns,
        csv_args = csv_args,
        autodetect_encoding = autodetect_encoding,
        content_columns = content_columns
    )
