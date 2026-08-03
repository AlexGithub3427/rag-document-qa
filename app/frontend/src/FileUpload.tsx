import { useState } from 'react'
import { DocUploadResponse } from './types.ts'

interface FileUploadProps {
    onFileSelected: () => void;
    onUploadSuccess: (data: DocUploadResponse) => void;
}

export default function FileUpload({ onFileSelected, onUploadSuccess }: FileUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState<'idle' | 'uploading' | 'success'| 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
        if (!e.target.files) return
        setFile(e.target.files[0]);
        onFileSelected()
    }

    async function handleUpload() {
        if (!file) return;
        setStatus('uploading');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/documents/', {
                method: 'POST',
                body: formData,
            });
            
            if (!response.ok) throw new Error(`Upload failed. Status: ${response.status}`);

            const data: DocUploadResponse = await response.json();
            console.log(data);
            setStatus('success');
            onUploadSuccess(data);

        } catch (error) {
            setStatus('error');
            setErrorMessage(error instanceof Error ? error.message : 'unknown error uploading file');
        }
    }

    return (
        // JSX that wires up handleFileChange to onChange, handleUpload to onClick
        <div>
            <input 
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            />

            {file && status !== 'uploading' && (
                <button onClick={handleUpload}>
                    Upload File
                </button>
            )}

            {status === 'uploading' && <p>Uploading...</p>}

            {status === 'success' && <p>Upload successful!</p>}

            {status === 'error' && <p>{errorMessage}</p>}
        </div>
    );
}