import io
from pypdf import PdfReader

def extract_text(pdf: bytes) -> str:
    # wrap bytes in a BytesIO buffer
    bytes_buffer = io.BytesIO(pdf)

    # pass to PdfReader
    reader = PdfReader(bytes_buffer)

    # loop pages, extract and concatenate text
    pdf_string = ""
    for page in reader.pages:
        pdf_string += page.extract_text()
    
    # return full text string
    return pdf_string