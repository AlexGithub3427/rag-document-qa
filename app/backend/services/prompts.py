from langchain_core.documents import Document

from models.schemas import Chunk

def build_context_string(chunks: list[Chunk]) -> str:
    context = ""
    for i, chunk in enumerate(chunks):
        context += f"[{i+1}] {chunk.header_path}\n{chunk.text}\n\n"
    return context
    
def build_rag_prompt(question: str, document_title: str, context: str) -> str:
    return f"""Answer the question using only the context below. If the answer is not in context, say "I don't know."

    Document Title: {document_title}

    Context:

    {context}

    Question: {question}"""

def extract_header_path(chunk: Document) -> str:
    header_path = ""
    for i in range(1,4):
        header_key = f"Header {i}"
        if header_key in chunk.metadata:
            if i == 1:
                header_path += f"{chunk.metadata[header_key]}"
            else:
                header_path += f" > {chunk.metadata[header_key]}"
    return header_path