import { useState, useEffect } from 'react'

import { QueryResponse } from './types'

interface ChatWindowProps {
    documentReady: boolean;
}

type Message = {
    question: string;
    answer: string;
}

export default function ChatWindow({ documentReady }: ChatWindowProps) {
    const [question, setQuestion] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    useEffect(() => {
        if (!documentReady) {
            setMessages([]);
        }
    }, [documentReady]);

    function handleQuestionChange(e: React.ChangeEvent<HTMLInputElement>) {
        setQuestion(e.target.value);
    }

    async function handleSubmit() {
        console.log('Ask pressed');
        if (!question || status === 'loading') return;
        setStatus('loading');

        try {
            const response = await fetch('http://localhost:8000/query', {
                method: 'POST',
                headers: { "Content-Type": "application/json"},
                body: JSON.stringify({
                    question: question
                })
            });

            if (!response.ok) throw new Error(`Submission failed. Status: ${response.status}`);

            const data: QueryResponse = await response.json();
            console.log(data);
            
            setMessages(prev => [...prev, { question, answer: data.answer }]);
            
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