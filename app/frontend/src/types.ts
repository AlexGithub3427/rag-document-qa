
interface Chunk {
    text: string;
    header_path: string;
}

type RecordOrNone = Record<string, unknown> | null | undefined;

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
    citations_list: RecordOrNone[];
}

export interface QueryRequest {
    question: string;
    document_id: string;
}

export interface QueryResponse {
    answer: string;
    chunks: Chunk[];
}