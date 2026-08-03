from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

def split_text(text: str) -> list[Document]:
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
        ("#####", "Header 5")
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    return text_splitter.split_text(text)
