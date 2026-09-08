import { useState, useEffect, act } from 'react'

import { DocHistoryRetrievalResponse, Document, Chunk, QueryRequest, QueryResponse, Role } from './types'

interface ChatWindowProps {
    freshUpload: boolean | null;
    documentReady: boolean;
    activeDocument: Document | null;
}

type Message = {
    question: string;
    answer: string;
    citations: string;
}

export default function ChatWindow({ freshUpload, documentReady, activeDocument }: ChatWindowProps) {
    const [question, setQuestion] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    useEffect(() => {
        if (freshUpload || !activeDocument) {
            setMessages([]);
        } else {
            let active = true;

            (async () => {
                try {
                    setStatus('loading');
                    const response = await fetch(`http://localhost:8000/documents/${activeDocument.id}/history/`, {
                        method: 'GET',
                    });

                    if (!response.ok) throw new Error (`Document history fetch failed. Status: ${response.status}`);
                    
                    const data: DocHistoryRetrievalResponse = await response.json();
                    console.log(data);

                    if (!active) return;

                    const questionHistory = data.content_list
                        .map((content, i) => ({ content, i }))
                        .filter(item => data.role_list[item.i] === Role.USER)
                        .map(item => item.content);
                    const answerHistory = data.content_list
                        .map((content, i) => ({ content, i }))
                        .filter(item => data.role_list[item.i] === Role.ASSISTANT)
                        .map(item => item.content);
                    const citationHistory = data.citations_list
                        .filter(citations => citations !== null)
                        .map(citations => formatCitations(citations));
    
                    const chatHistory = questionHistory.map((content, i) => ({ 
                        question: content,  
                        answer: answerHistory[i],
                        citations: citationHistory[i]
                     }));
                    setMessages(chatHistory);
                    setStatus('idle');
                } catch (error) {
                    setStatus('error');
                    setErrorMessage(error instanceof Error ? error.message : 'unknown error loading chat history');
                }
            })();
        }
    }, [freshUpload, activeDocument]);

    function handleQuestionChange(e: React.ChangeEvent<HTMLInputElement>) {
        setQuestion(e.target.value);
    }

    async function handleSubmit() {
        console.log('Ask pressed');
        if (!activeDocument || !question || status === 'loading') return;
        setStatus('loading');

        try {
            const query_payload: QueryRequest = {
                question: question,
                document_id: activeDocument.id,
            }
            const response = await fetch('http://localhost:8000/query', {
                method: 'POST',
                headers: { "Content-Type": "application/json"},
                body: JSON.stringify(query_payload)
            });

            if (!response.ok) throw new Error(`Submission failed. Status: ${response.status}`);

            const data: QueryResponse = await response.json();
            console.log(data);
            
            setMessages(prev => [...prev, { question, answer: data.answer, citations: formatCitations(data.chunks)}]);
            
            setQuestion('');
            setStatus('idle');
        } catch (error) {
            setStatus('error');
            setErrorMessage(error instanceof Error ? error.message : 'unknown error submitting question');
        }
    }

    return (
        <div>
            <div>
                {messages.map((message, i) => (
                    <div key={i}>
                        <p><strong>Q: </strong>{message.question}</p>
                        <p><strong>A: </strong>{message.answer}</p>
                        <p><strong>citations: </strong>{message.citations}</p>
                    </div>
                ))}
            </div>

            <input
                type="text"
                value={question}
                onChange={handleQuestionChange}
                disabled={!documentReady || status=='loading'}
                placeholder={documentReady ? 'Ask a question!' : 'Upload a document.'}
            />

            <button 
                onClick={handleSubmit}
                disabled={!documentReady || status=='loading' || !question}
            >
                Ask
            </button>

            {status == 'loading' && <p>I AM THINKING RIGHT NOW!</p>}
            {status == 'error' && <p>{errorMessage}</p>}

        </div>
    );
}

// citation formatter function placeholder for now
function formatCitations(citations: Chunk[]): string {
    return citations.reduce<string>((groupedCitation, currentCitation) => {
        return groupedCitation + currentCitation.header_path + ":" + currentCitation.text + "\n";
    }, "");
}
