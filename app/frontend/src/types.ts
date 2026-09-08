
export interface Chunk {
    text: string;
    header_path: string;
}


export const enum Role {
    USER = "user",
    ASSISTANT = "assistant",
}

export interface Document {
    title: string;
    id: string;
}

export interface DocUploadResponse {
    message: string;
    document_title: string;
    document_id: string;
}

export interface DocRetrievalResponse {
    ids: string[];
    titles: string[];
}

export interface DocHistoryRetrievalResponse {
    role_list: Role[];
    content_list: string[];
    citations_list: (Chunk[] | null)[];
}

export interface QueryRequest {
    question: string;
    document_id: string;
}

export interface QueryResponse {
    answer: string;
    chunks: Chunk[];
}