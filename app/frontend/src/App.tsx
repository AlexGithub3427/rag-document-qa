import { useState } from 'react';
import FileUpload from './FileUpload';
import ChatWindow from './ChatWindow';

import { useEffect } from 'react';

function App() {
  const [documentReady, setDocumentReady] = useState(false)
  // const [documentId, setDocumentId] = useState(null);

  return (
    <div className="App">
      <h1>Document Q&A</h1>
      <FileUpload 
        onUploadSuccess={(data) => {
          setDocumentReady(true)
        }}
        onFileSelected={() => {
          setDocumentReady(false)
        }}
      />
      <ChatWindow documentReady={documentReady}
      />
    </div>
  );
}

export default App;