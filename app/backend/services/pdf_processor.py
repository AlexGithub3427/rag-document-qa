import io
import pymupdf

from collections import defaultdict
from collections.abc import Callable

MIN_OCCURRENCE_THRESHOLD = 2        # a heading level should appear at least twice
NOISE_RATIO_THRESHOLD = 0.15        # heading size shouldn't approach body's frequency
MAX_HEADING_WORDS = 15              # individual heading size shouldn't be too long (over a sentence length)

HEADER_HEIGHT = 60
FOOTER_HEIGHT = 60


def pdf_to_markdown(pdf: bytes) -> tuple[str, str]:
    # wrap bytes in a BytesIO buffer
    bytes_buffer = io.BytesIO(pdf)

    # 1. open file with pymupdf and iterate over spans collecting metadata
    # - first pass, find all text sizes and create cluster mapping (max of 0.1 variation)
    # - second pass, iterate over text with valuable metadata
    # - each text span represents grouped runs of text sharing the same size, flags, and char_flags
    doc = pymupdf.open(stream=bytes_buffer, filetype="pdf")

    spans = []
    current_span = {
        "text": "",
        "size": -1, 
        "flags": -1, 
        "char_flags": -1,
        "page_nums": [],
        "span_id": - 1
        }
    span_count, char_count = defaultdict(int), defaultdict(int)
    all_sizes = set()

    for page in doc:
        rect = page.rect
        content_box = pymupdf.Rect(0, HEADER_HEIGHT, rect.width, rect.height - FOOTER_HEIGHT)
        blocks = page.get_text("dict", clip=content_box, flags=11)["blocks"] 
        for b in blocks:
            for l in b["lines"]:
                for s in l["spans"]:
                    all_sizes.add(s["size"])
                
    size_mapping = sizes_to_clusters(all_sizes)

    for page in doc:
        rect = page.rect
        content_box = pymupdf.Rect(0, HEADER_HEIGHT, rect.width, rect.height - FOOTER_HEIGHT)
        blocks = page.get_text("dict", clip=content_box, flags=11)["blocks"]        
        for b in blocks:
            for l in b["lines"]:
                for s in l["spans"]:
                    if size_mapping[s["size"]] == size_mapping[current_span["size"]] and s["flags"] == current_span["flags"] and s["char_flags"] == current_span["char_flags"]:
                        current_span["text"] += s["text"]
                        if page.number not in current_span["page_nums"]:
                            current_span["page_nums"].append(page.number)
                        
                    else:
                        if size_mapping[s["size"]] != -1:
                            record = {
                                "text": current_span["text"],
                                "size": size_mapping[current_span["size"]],
                                "flags": current_span["flags"],
                                "char_flags": current_span["char_flags"],
                                "page_nums": current_span["page_nums"],
                                "span_id": len(spans)
                            }
                            spans.append(record)
                            span_count[size_mapping[current_span["size"]]] += 1
                            char_count[size_mapping[current_span["size"]]] += len(current_span["text"])
                        current_span = {
                            "text": s["text"],
                            "size": size_mapping[s["size"]],
                            "flags": s["flags"],
                            "char_flags": s["char_flags"],
                            "page_nums": [page.number],
                        }
    
    final_record = {
        "text": current_span["text"],
        "size": size_mapping[current_span["size"]],
        "flags": current_span["flags"],
        "char_flags": current_span["char_flags"],
        "page_nums": current_span["page_nums"],
        "span_id": len(spans)
    }
    spans.append(final_record)
    span_count[size_mapping[current_span["size"]]] += 1
    char_count[size_mapping[current_span["size"]]] += len(current_span["text"])


    # 2. identify title and body font size
    # - identifies candidates on first non null page
    # - extract title as first contiguous run of text prioritizing max size font, bold, and defaulting to first span
    # - remove title span(s) from markdown spans and histograms
    page_zero_spans = [s for s in spans if 0 in s["page_nums"]]
    title_candidates = [
        s for s in page_zero_spans
        if s["text"].strip()
        and not s["text"].strip().isdigit()
    ]

    if not title_candidates:
        i = 1
        while not title_candidates and i < len(doc):
            current_page_spans = [s for s in spans if i in s["page_nums"]]
            title_candidates = [
                s for s in current_page_spans
                if s["text"].strip()
                and not s["text"].strip().isdigit()
            ]
            i += 1
    
    if not title_candidates:
        return "", ""


    max_size = max(s["size"] for s in title_candidates)
    body_size = max(char_count, key=char_count.get)

    if max_size != body_size:
        title_spans = first_contiguous_run(title_candidates, lambda s: s["size"] == max_size)
    else:
        title_spans = [title_candidates[0]]

    title = " ".join(s["text"].strip() for s in title_spans).strip()

    title_span_ids = [s["span_id"] for s in title_spans]
    for s in spans:
        if s["span_id"] in title_span_ids:
            span_count[s["size"]] -= 1
            char_count[s["size"]] -= len(s["text"])

    spans = [s for s in spans if s["span_id"] not in title_span_ids]

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


    # 4. classify each span as heading or body
    classified_spans = []
    for span in spans:
        word_count = len(span["text"].split())
        trimmed_text = span["text"].strip()
        label = ""

        if not trimmed_text:
            continue
        elif span["size"] in header_sizes and word_count <= MAX_HEADING_WORDS:
            label = size_to_level[span["size"]]
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
    return title, markdown

def sizes_to_clusters(all_sizes: set, threshold: float = 0.1) -> dict:
    size_mapping = {-1: -1}
    sorted_sizes = sorted(all_sizes)
    clusters = [[sorted_sizes[0]]]

    for s in sorted_sizes[1:]:
        if s - clusters[-1][0] <= threshold:
            clusters[-1].append(s)
        else:
            clusters.append([s])

    for c in clusters:
        for s in c:
            size_mapping[s] = c[0]

    return size_mapping



def first_contiguous_run(candidates: list, predicate: Callable[[int], bool]) -> list:
    run = []
    started = False
    for s in candidates:
        if predicate(s):
            run.append(s)
            started = True
        elif started:
            break
    return run