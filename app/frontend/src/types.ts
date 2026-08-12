

export interface DocUploadResponse {
    message: string;
    document_id: number;
    document_title: string;
}

interface Chunk {
    text: string;
    header_path: string;
}

export interface QueryResponse {
    answer: string;
    chunks: Chunk[];
}