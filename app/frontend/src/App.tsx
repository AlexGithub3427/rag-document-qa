import { useState, useEffect } from 'react';
import FileUpload from './FileUpload';
import ChatWindow from './ChatWindow';
import Sidebar from './Sidebar';

import { Document } from './types'

function App() {
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const [renderUpload, setRenderUpload] = useState(true);
  const [documentReady, setDocumentReady] = useState(false);
  const [activeDocument, setActiveDocument] = useState<Document | null>(null);

  return (
    <div className="App">
      <h1>Document Q&A</h1>
      <Sidebar 
        activeDocumentId={activeDocument ? activeDocument.id : ""}
        onSelectDocument={(doc) => {
          setActiveDocument(doc);
          setDocumentReady(true);
          setRenderUpload(false);          
        }
        }
        onUploadNew={() => {
          setRenderUpload(true)
        }}
        refreshKey={refreshKey}
      />
      {renderUpload && <FileUpload 
        onUploadSuccess={(data) => {
          setDocumentReady(true);
          const document: Document = {
            title: data.document_title,
            id: data.document_id,
          }
          setActiveDocument(document)
          setRefreshKey((prevKey) => prevKey + 1)
        }}
        onFileSelected={() => {
          setDocumentReady(false);
          setActiveDocument(null);
        }}
      />}
      

      <ChatWindow
        freshUpload={renderUpload}
        documentReady={documentReady} 
        activeDocument={activeDocument}
      />
    </div>
  );
}

export default App;