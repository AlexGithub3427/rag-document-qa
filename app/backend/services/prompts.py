

def build_context_string(chunks: list[str]) -> str:
    context = ""
    for i, chunk in enumerate(chunks):
        context += f"[{i+1}] {chunk}\n\n"
    return context
    
def build_rag_prompt(question: str, context: str) -> str:
    return f"""Answer the question using only the context below. If the answer is not in context, say "I don't know."

    Context:

    {context}

    Question: {question}"""