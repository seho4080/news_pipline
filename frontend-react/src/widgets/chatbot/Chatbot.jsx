import { useState } from 'react'
import './Chatbot.scss'

const Chatbot = ({ articleId }) => {
  const [showChat, setShowChat] = useState(false)
  const [messages, setMessages] = useState([
    { author: 'bot', text: '안녕하세요 끼룩' }
  ])
  const [inputMessage, setInputMessage] = useState("")
  
  const arr = ['호에...?', '미안하지만 말해줄 수 없다 끼룩']
  const token = localStorage.getItem('access_token')
  const headers = token
    ? {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
    : {
      'Content-Type': 'application/json'
    }

  const sendMessage = async () => {
    if (!inputMessage.trim()) return

    setMessages(prev => [...prev, { author: 'user', text: inputMessage }])
    const message = inputMessage
    setInputMessage("")

    try {
      const response = await fetch(`http://localhost:8000/api/news/${articleId}/chat/`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          "message": message
        })
      })

      if (response.ok) {
        const data = await response.json()
        
        setMessages(prev => [...prev, {
          author: 'bot', text: data.message + " 끼룩"
        }])
      } else {
        const randomItem = arr[Math.floor(Math.random() * arr.length)]
        setMessages(prev => [
          ...prev,
          { author: 'bot', text: randomItem },
          { author: 'bot', text: '다른거 뭐 도와드려요?' }
        ])
      }
    } catch (error) {
      console.log("Chatbot 요청 - ", error)
    }
  }

  const closeChat = () => {
    setShowChat(false)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage()
    }
  }

  return (
    <div className="chatbot-container">
      {showChat && (
        <div className="chatbot-bubble">
          <div className="chatbot-bubble__arrow"></div>
          <header className="chatbot-header">
            <h3>AI 비서 소봇</h3>
            <button className="close-btn" onClick={closeChat}>×</button>
          </header>
          <div className="chatbot-messages">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`chatbot-message ${msg.author}`}
              >
                <span>{msg.text}</span>
              </div>
            ))}
          </div>
          <footer className="chatbot-input-area">
            <input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
            />
            <button onClick={sendMessage}>전송</button>
          </footer>
        </div>
      )}
      <div 
        className="chatbot-emoji" 
        onClick={() => setShowChat(!showChat)} 
        title="채팅 열기"
      >
        <img src="/chatbot.png" alt="Chatbot" />
      </div>
    </div>
  )
}

export default Chatbot