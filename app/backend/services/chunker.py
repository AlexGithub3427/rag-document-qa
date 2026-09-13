from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from services.prompts import extract_header_path

MAX_CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

def split_markdown(text: str) -> list[Document]:
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4")
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    documents = text_splitter.split_text(text)

    final_documents = []
    recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=MAX_CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    for document in documents:
        header_path = extract_header_path(document)
        for key in list(document.metadata.keys()):
            if "Header" in key:
                del document.metadata[key]

        if len(document.page_content) > MAX_CHUNK_SIZE:
            splitted_text = recursive_splitter.split_text(document.page_content)
            for text_split in splitted_text:
                document = Document(page_content=text_split, metadata={"header_path": header_path})
                final_documents.append(document)
        else:
            document.metadata["header_path"] = header_path
            final_documents.append(document)

    breakpoint()

    return final_documents
