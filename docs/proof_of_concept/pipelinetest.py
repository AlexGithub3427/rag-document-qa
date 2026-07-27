import os
import chromadb

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Setup
# ------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=api_key
)

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="my_collection")

# 2. PDF Extraction
# ------------------------------------------------------------------
reader = PdfReader("Official_Standard_Dachshund.pdf")
pdf_string = ""
for page in reader.pages:
    pdf_string += page.extract_text()

# 3. Chunking
# - currently using recursive character text splitting as baseline
# ------------------------------------------------------------------
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
chunks = text_splitter.split_text(pdf_string)

# 4. Embedding and Storing
# ------------------------------------------------------------------
curr_id = 0
ids_list = []
embeddings_list = []
documents_list = []

for i, chunk in enumerate(chunks):
    response = client.embeddings.create(
        input=chunk,
        model="text-embedding-3-small"
    )
    ids_list.append("chunk_" + str(i))
    embeddings_list.append(response.data[0].embedding)
    documents_list.append(chunk)

collection.add(
    ids=ids_list,
    embeddings=embeddings_list,
    documents=documents_list
)

# 5. Querying
# - embeds question and queries the Chroma collection and retrieves the 3 most similar chunks
# ------------------------------------------------------------------
question = "What is the temperament of a Dachshund?"
embedding_response = client.embeddings.create(
    input=question,
    model="text-embedding-3-small"
)

retrieved_chunks = collection.query(
    query_embeddings=[embedding_response.data[0].embedding],
    n_results=5
)

# 6. Generation
# - takes the 3 retrieved chunks and formats them into a context string
# - make final OpenAI query with context
# - print question, answer, and source chunks used
# ------------------------------------------------------------------
context = ""
for i, chunk in enumerate(retrieved_chunks["documents"][0]):
    context += f"[{i+1}] {chunk}\n\n"

system_prompt = f"""Answer the question using only the context below. If the anwer is not in context, say "I don't know."

Context:

{context}

Question: {question}"""

response = client.responses.create(
    model="gpt-4o-mini",
    input=system_prompt,
)

print(question)
print(response.output_text)
print(context)
print(len(chunks))
