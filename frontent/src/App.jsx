import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hello! Put pdf through inbox msg...I give to you better Insight' }
  ])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleQuery = async () => {
    if (!query.trim()) return

    const userMessage = { role: 'user', text: query }
    setMessages((prev) => [...prev, userMessage])
    setQuery('')
    setLoading(true)

    try {
      const res = await fetch('http://127.0.0.1:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.text })
      })

      if (!res.ok) throw new Error('Backend server is not responding!')
      const data = await res.json()
      
      setMessages((prev) => [...prev, { 
        role: 'bot', 
        text: data.response || 'No response returned.' 
      }])
    } catch (err) {
      setMessages((prev) => [...prev, { 
        role: 'bot', 
        text: 'Error: Make sure your FastAPI server is running on port 8000!' 
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Show the user that we are uploading
    setMessages((prev) => [...prev, { role: 'user', text: `📄 Uploading document: ${file.name}` }]);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Failed to upload file');
      
      const data = await res.json();
      setMessages((prev) => [...prev, { 
        role: 'bot', 
        text: data.message || `Successfully processed ${file.name}. You can now ask questions about it!` 
      }]);
    } catch (err) {
      setMessages((prev) => [...prev, { 
        role: 'bot', 
        text: `Error uploading ${file.name}. Make sure your backend has an /api/upload endpoint.` 
      }]);
    } finally {
      setLoading(false);
      // Reset the input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="container">
      <div className="chat-header">
        <h1>RAG Chatbot</h1>
      </div>
      
      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.role}`}>
            <div className="message-bubble">
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message-wrapper bot">
            <div className="message-bubble typing">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-group">
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleFileUpload}
        />
        <button 
          className="upload-btn" 
          onClick={() => fileInputRef.current?.click()} 
          disabled={loading}
          title="Upload Document"
        >
          📎
        </button>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your message..."
          onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          disabled={loading}
        />
        <button className="send-btn" onClick={handleQuery} disabled={loading || !query.trim()}>
          Send
        </button>
      </div>
    </div>
  )
}

export default App
