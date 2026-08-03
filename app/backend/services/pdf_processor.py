import io
import pymupdf
import pymupdf4llm
import re

from collections import defaultdict, Counter

MIN_OCCURRENCE_THRESHOLD = 2        # a heading level should appear at least twice
NOISE_RATIO_THRESHOLD = 0.15        # heading size shouldn't approach body's frequency
MAX_HEADING_WORDS = 15              # individual heading size shouldn't be too long (over a sentence length)


def extract_text(pdf: bytes) -> str:
    # wrap bytes in a BytesIO buffer
    bytes_buffer = io.BytesIO(pdf)

    # 1. open file with pymupdf, iterate over spans with metadata
    doc = pymupdf.open(stream=bytes_buffer, filetype="pdf")
    spans = []
    span_count, char_count = defaultdict(int), defaultdict(int)


    for page in doc:
        blocks = page.get_text("dict", flags=11)["blocks"]
        for b in blocks:
            for l in b["lines"]:
                line_spans = l["spans"]
                for i, s in enumerate(line_spans):
                    record = {
                        "text": s["text"],
                        "size": s["size"],
                        "is_bold": bool(s["flags"] & 2 ** 4),
                        "page_num": page.number,
                        "is_line_start": i == 0
                    }
                    spans.append(record)
                    span_count[s["size"]] += 1
                    char_count[s["size"]] += len(s["text"])


    # 2. determine body font size
    body_size = max(char_count, key=char_count.get)

    # 3. determine header levels
    # - header candidates are all font sizes greater than body font
    # - sort by descending, filter based on minimum occurence threshold (header will appear at least
    #   X ammount of times) and char count maximum (header char count will be significantly lower than
    #   body char count)
    # - take largest and cap at 4 header levels
    # - check if bold-at-body-size behaves like a heading level, and use bold fall_back if necessary
    header_candidates = sorted([key for key, _ in span_count.items() if key > body_size], reverse=True)
    header_candidates[:] = [
        size for size in header_candidates
        if span_count[size] >= MIN_OCCURRENCE_THRESHOLD
        and char_count[size] < char_count[body_size] * NOISE_RATIO_THRESHOLD
    ]

    header_sizes = header_candidates[:4]
    size_to_level = { size: f"H{i+1}" for i, size in enumerate(header_sizes)}


    bold_body_spans = [
        s for s in spans 
        if s["is_bold"] 
        and s["size"] == body_size
        and s["is_line_start"]
        and len(s["text"].split()) <= MAX_HEADING_WORDS]
    
    bold_occurrence_count = len(bold_body_spans)

    use_bold_fallback = bold_occurrence_count >= MIN_OCCURRENCE_THRESHOLD

    if use_bold_fallback:
        bold_level = f"H{len(header_sizes) + 1}"

    # 4. classify each span as heading or body
    classified_spans = []
    for span in spans:
        word_count = len(span["text"].split())
        trimmed_text = span["text"].strip()
        label = ""

        if not trimmed_text:
            continue
        elif span["size"] in header_sizes:
            if word_count <= MAX_HEADING_WORDS:
                label = size_to_level[span["size"]]
            else:
                label = "body"
        elif (use_bold_fallback and span["is_bold"] and span["is_line_start"]
            and word_count <= MAX_HEADING_WORDS and span["size"] == body_size):
            label = bold_level
        else: 
            label = "body"

        classified_spans.append({**span, "label": label})
        
    # 5. build markdown string
    markdown_array = []
    current_paragraph = []

    for span in classified_spans:

        if span["label"] == "body":
            current_paragraph.append(span["text"])
        else:
            if current_paragraph:
                paragraph_text = "".join(current_paragraph)
                markdown_array.append(paragraph_text.strip())
                current_paragraph = []
            level_num = int(span["label"][1])
            heading_text = span["text"].strip()
            markdown_array.append("#" * level_num + " " + heading_text)
    
    if current_paragraph:
        paragraph_text = "".join(current_paragraph)
        markdown_array.append(paragraph_text.strip())
        current_paragraph = []

    markdown = "\n\n".join(markdown_array)
    markdown = re.sub(r'Page \d+ of \d+', ' ', markdown)
    markdown = re.sub(r' {2,}', ' ', markdown)

    return markdown