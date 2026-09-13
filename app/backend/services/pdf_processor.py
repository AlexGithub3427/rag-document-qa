import re
import io
import pymupdf

from collections import defaultdict
from collections.abc import Callable

MIN_OCCURRENCE_THRESHOLD = 2        # a heading level should appear at least twice
NOISE_RATIO_THRESHOLD = 0.15        # heading size shouldn't approach body's frequency
MAX_HEADING_WORDS = 15              # individual heading size shouldn't be too long (over a sentence length)
REPETITION_PAGE_THRESHOLD = 3       
BOUNDARY_SPAN_WINDOW = 5
TABLE_OVERLAP_THRESHOLD = 0.5

HEADER_HEIGHT = 60
FOOTER_HEIGHT = 60


def pdf_to_markdown(pdf: bytes) -> tuple[str, str]:
    #

    # 1. open file with pymupdf and iterate over spans collecting metadata
    # - first pass, find all tables (if any) and skip text span collection in these areas
    # - second pass, find all text sizes and create cluster mapping (max of 0.1 variation)
    # - second pass, iterate over text with valuable metadata
    # - each text span represents grouped runs of text sharing the same size, flags, and char_flags
    bytes_buffer = io.BytesIO(pdf)
    doc = pymupdf.open(stream=bytes_buffer, filetype="pdf")

    page_tables = defaultdict(list)
    for page in doc:
        rect = page.rect
        content_box = pymupdf.Rect(0, HEADER_HEIGHT, rect.width, rect.height - FOOTER_HEIGHT)
        try:
            tables = page.find_tables(clip=content_box, strategy="lines_strict")
        except Exception:
            tables = []
        for table in tables:
            try:
                markdown = table.to_markdown()
            except Exception:
                continue
            if markdown.strip():
                bbox = pymupdf.Rect(table.bbox)
                page_tables[page.number].append({
                    "bbox": bbox,
                    "markdown": markdown,
                    "y0": bbox.y0
                })


    spans = []
    current_span = {
        "text": "",
        "size": -1, 
        "flags": -1, 
        "char_flags": -1,
        "page_nums": [],
        "y0": 0.0,
        "span_id": - 1
        }
    span_count, char_count = defaultdict(int), defaultdict(int)
    all_sizes = set()

    for page in doc:
        rect = page.rect
        content_box = pymupdf.Rect(0, HEADER_HEIGHT, rect.width, rect.height - FOOTER_HEIGHT)
        blocks = page.get_text("dict", clip=content_box, flags=11)["blocks"]
        blocks = get_reading_order(blocks, content_box)
        for b in blocks:
            for l in b["lines"]:
                for s in l["spans"]:
                    all_sizes.add(s["size"])
                
    size_mapping = sizes_to_clusters(all_sizes)

    for page in doc:
        rect = page.rect
        content_box = pymupdf.Rect(0, HEADER_HEIGHT, rect.width, rect.height - FOOTER_HEIGHT)
        blocks = page.get_text("dict", clip=content_box, flags=11)["blocks"]
        blocks = get_reading_order(blocks, content_box)
        tables_on_page = page_tables[page.number]        
        for b in blocks:
            for l in b["lines"]:
                line_bbox = pymupdf.Rect(l["bbox"])
                if in_any_table(line_bbox, tables_on_page):
                    continue
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
                                "y0": current_span["y0"],
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
                            "y0": line_bbox.y0,
                        }
    
    final_record = {
        "text": current_span["text"],
        "size": size_mapping[current_span["size"]],
        "flags": current_span["flags"],
        "char_flags": current_span["char_flags"],
        "page_nums": current_span["page_nums"],
        "y0": current_span["y0"],
        "span_id": len(spans)
    }
    spans.append(final_record)
    span_count[size_mapping[current_span["size"]]] += 1
    char_count[size_mapping[current_span["size"]]] += len(current_span["text"])


    # 2. identify title and body font size
    # - identifies candidates on first non null page
    # - extract title as first contiguous run of text prioritizing max size font, bold, and defaulting to first span
    # - remove title span(s) from markdown spans and histograms
    # - filter out all text spans preceding title (assume to be junk/boilerplate text)
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

    
    first_title_id = title_spans[0]["span_id"] if title_spans else -1

    spans = [s for s in spans 
             if s["span_id"] not in title_span_ids 
             and s["span_id"] > first_title_id]

    # 3. determine header levels
    # - header candidates are all font sizes greater than body font
    # - sort by descending, filter based on minimum occurence threshold (header will appear at least
    #   X ammount of times) and char count maximum (header char count will be significantly lower than
    #   body char count)
    # - take largest and cap at 4 header levels
    header_candidates = sorted([key for key, _ in span_count.items() if key > body_size], reverse=True)
    header_candidates[:] = [
        size for size in header_candidates
        if span_count[size] >= MIN_OCCURRENCE_THRESHOLD
        and char_count[size] < char_count[body_size] * NOISE_RATIO_THRESHOLD
    ]

    header_sizes = header_candidates[:4]
    size_to_level = { size: f"H{i+1}" for i, size in enumerate(header_sizes)}


    # 4. classify each span as heading or body
    # - header validation function: header must be nonempty and word count must be
    #   less than MAX_HEADING_WORDS and must be majority alphanumeric characters
    # - filter boundary spans () if repeated across mulitple pages (junk headers/footers)
    classified_spans = []
    for span in spans:
        word_count = len(span["text"].split())
        trimmed_text = span["text"].strip()
        label = ""

        if not trimmed_text:
            continue
        elif span["size"] in header_sizes and is_header_shaped(trimmed_text, word_count):
            label = size_to_level[span["size"]]
        else: 
            label = "body"

        classified_spans.append({**span, "label": label})

    boundary_span_ids = get_boundary_span_ids(spans)
    normalized_pages = defaultdict(set)
    for span in classified_spans:
        if span["span_id"] in boundary_span_ids:
            key = normalize_for_repetition(span["text"])
            normalized_pages[key].update(span["page_nums"])

    repeating_keys = {
        key for key, pages in normalized_pages.items()
        if len(pages) >= REPETITION_PAGE_THRESHOLD
    }

    classified_spans = [
        span for span in classified_spans
        if not (span["span_id"] in boundary_span_ids and normalize_for_repetition(span["text"]) in repeating_keys)
    ]

    # 5. merge in table blocks at correct reading-order position
    table_blocks = []
    for page_num, tables in page_tables.items():
        for table in tables:
            table_blocks.append({
                "text": table["markdown"],
                "page_nums": [page_num],
                "y0": table["y0"],
                "label": "table",
            })

    merged_spans = list(classified_spans)
    for table in sorted(table_blocks, key=lambda t: (t["page_nums"][0], t["y0"]), reverse=True):
        page_num = table["page_nums"][0]
        insert_at = len(merged_spans)
        for i in range(len(merged_spans) -1, -1, -1):
            span = merged_spans[i]
            if page_num in span["page_nums"] and span["y0"] <= table["y0"]:
                insert_at = i + 1
                break
            if span["page_nums"] and span["page_nums"][0]< page_num:
                insert_at = i + 1
                break
        merged_spans.insert(insert_at, table)
    
    # 6. build markdown string
    markdown_array = []
    current_paragraph = []

    for span in merged_spans:

        if span["label"] == "body":
            current_paragraph.append(span["text"])
        elif span["label"] == "table":
            if current_paragraph:
                paragraph_text = "".join(current_paragraph)
                markdown_array.append(paragraph_text.strip())
                current_paragraph = []
            markdown_array.append(span["text"].strip())
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

def in_any_table(bbox: pymupdf.Rect, tables_on_page: list, overlap_threshold: float = TABLE_OVERLAP_THRESHOLD) -> bool:
    bbox_area = bbox.get_area()
    if bbox_area == 0:
        return False
    for t in tables_on_page:
        intersection = bbox & t["bbox"]
        if not intersection.is_empty:
            if (intersection.get_area() / bbox_area) > overlap_threshold:
                return True
    return False

def get_reading_order(blocks: list, content_box: pymupdf.Rect, 
                      column_gap_ratio: float = 0.03, full_width_ratio: float = 0.65,
                      min_column_blocks: int = 3) -> list:
    """
    Reorders blocks into column-aware reading order. Full-width blocks are interleaved 
    only by y0, while remaing blocks are clustered into N columns by x0 gaps and sorted
    by column top-to-bottom.
    """
    if not blocks: 
        return []

    content_width = content_box.width
    gap_threshold = content_width * column_gap_ratio
    full_width_threshold = content_width * full_width_ratio

    full_width_blocks = []
    column_candidates = []

    # categorize full_width blocks and column blocks
    for block in blocks:
        bbox = pymupdf.Rect(block["bbox"])
        if bbox.width >= full_width_threshold:
            full_width_blocks.append(block)
        else:
            column_candidates.append(block)

    if not column_candidates:
        return sorted(full_width_blocks, key=lambda block: block["bbox"][1])

    # cluster column blocks by x0 gap
    sorted_by_x0 = sorted(column_candidates, key=lambda block: block["bbox"][0])
    columns = [[sorted_by_x0[0]]]
    for block in sorted_by_x0[1:]:
        prev_x0 = columns[-1][-1]["bbox"][0]
        if block["bbox"][0] - prev_x0 <= gap_threshold:
            columns[-1].append(block)
        else:
            columns.append([block])

    # merge columns under minimum_block_threshold by
    # folding into closest neighbor
    if len(columns) > 1:
        merged = True
        while merged and len(columns) > 1:
            merged = False
            for i, column in enumerate(columns):
                if len(column) < min_column_blocks:
                    left_dist = (column[0]["bbox"][0] - columns[i - 1][-1]["bbox"][0]) if i > 0 else None
                    right_dist = (columns[i + 1][0]["bbox"][0] - column[0]["bbox"][0]) if i < len(columns) - 1 else None

                    if left_dist is None and right_dist is None:
                        break
                    if right_dist is None or (left_dist is not None and left_dist <= right_dist):
                        target = i - 1
                    else: 
                        target = i + 1

                    columns[target].extend(column)
                    columns[target].sort(key=lambda block: block["bbox"][0])
                    del columns[i]
                    merged = True
                    break
                    
    # sort within columns by y0
    for column in columns:
        column.sort(key=lambda block: block["bbox"][1])

    ordered_columns = [block for column in columns for block in column]

    if not full_width_blocks:
        return ordered_columns

    # sort full width blocks by y0
    full_width_blocks.sort(key=lambda block: block["bbox"][1])

    merged = []
    full_width_index = 0
    column_index = 0

    while column_index < len(ordered_columns) or full_width_index < len(full_width_blocks):
        if full_width_index >= len(full_width_blocks):
            merged.append(ordered_columns[column_index])
            column_index += 1
        elif column_index >= len(ordered_columns):
            merged.append(full_width_blocks[full_width_index])
            full_width_index += 1
        else:
            full_width_y0 = full_width_blocks[full_width_index]["bbox"][1]
            column_y0 = ordered_columns[column_index]["bbox"][1]
            if full_width_y0 <= column_y0:
                merged.append(full_width_blocks[full_width_index])
                full_width_index += 1
            else:
                merged.append(ordered_columns[column_index])
                column_index += 1

    return merged

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

def is_header_shaped(trimmed_text: str, word_count: int) -> bool:
    if not trimmed_text or word_count > MAX_HEADING_WORDS:
        return False
    alnum_chars = sum(c.isalnum() for c in trimmed_text)
    return (alnum_chars / len(trimmed_text)) > 0.5

def get_boundary_span_ids(spans: list, window: int = BOUNDARY_SPAN_WINDOW) -> set:
    page_first, page_last = defaultdict(list), defaultdict(list)
    for s in spans:
        for p in s["page_nums"]:
            page_first[p].append(s["span_id"])
            page_last[p].append(s["span_id"])

    boundary_ids = set()
    for p in page_first:
        ids_sorted = sorted(page_first[p])
        boundary_ids.update(ids_sorted[:window])
        boundary_ids.update(ids_sorted[-window:])
    return boundary_ids

def normalize_for_repetition(text: str) -> str:
    return re.sub(r"\d+", "#", text.strip().lower())