import { useEffect, useState } from 'react';
import { DocRetrievalResponse } from './types';

type Document = { 
    id: string; 
    title: string;
};

interface SidebarProps {
    activeDocumentId: string | null;
    onSelectDocument: (doc: Document) => void;
    onUploadNew: () => void;
    refreshKey: number;
}

export default function Sidebar({ activeDocumentId, onSelectDocument, onUploadNew, refreshKey }: SidebarProps) {
    const [documents, setDocuments] = useState<Document[] | null>(null);
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    // fetch list of documents upon mount
    useEffect(() => {
        let active = true;

        (async () => {
            try {
                setStatus('loading');
                const response = await fetch('http://localhost:8000/documents/', {
                    method: 'GET',
                });

                if (!response.ok) throw new Error(`Document list fetch failed. Status: ${response.status}`);

                const data: DocRetrievalResponse = await response.json();
                console.log(data);

                if (!active) return;

                const paired = data.ids.map((id, i) => ({ id, title: data.titles[i]}));
                setDocuments(paired)
                setStatus('success')
            } catch (error) {
                if (!active) return;
                setStatus('error');
                setErrorMessage(error instanceof Error ? error.message : 'unknown error fetching document list');
            }
        })();
        
        return () => {
            active = false;
        };
    }, [refreshKey]);

    return (
        <div>
            <button onClick={onUploadNew}> + Upload </button>

            {status === 'loading' && <p> Loading Documents </p>}

            {status === 'error' && <p> Error: {errorMessage} </p>}

            {status === 'success' && documents && (
                <ul>
                    {documents.map((doc) => (
                        <li key={doc.id}>
                            <button
                                onClick={() => onSelectDocument(doc)}
                                aria-current={doc.id === activeDocumentId}
                            >
                                {doc.title}
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}