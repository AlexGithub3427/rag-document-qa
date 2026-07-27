

export interface DocUploadResponse {
    message: string;
    chunks: number;
}

interface Chunk {
    text: string;
}

export interface QueryResponse {
    answer: string;
    chunks: Chunk[];
}