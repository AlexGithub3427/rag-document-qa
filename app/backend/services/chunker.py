from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

from services.prompts import extract_header_path

def split_markdown(text: str) -> list[Document]:
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4")
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    documents = text_splitter.split_text(text)


    for document in documents:
        document.metadata["header_path"] = extract_header_path(document)
        for key in list(document.metadata.keys()):
            if "Header" in key:
                del document.metadata[key]

    return documents
