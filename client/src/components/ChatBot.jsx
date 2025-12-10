import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './ChatBot.css';

const ChatBot = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { role: 'assistant', text: '안녕하세요! 투자 관련 궁금한 점이 있으신가요?' }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = { role: 'user', text: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const res = await axios.post('http://localhost:8000/api/chat', {
                message: input,
                history: messages,
                context: "User is in Easy Mode Portfolio Analysis"
            });

            const botMsg = { role: 'assistant', text: res.data.response };
            setMessages(prev => [...prev, botMsg]);
        } catch (err) {
            console.error("Chat failed", err);
            setMessages(prev => [...prev, { role: 'assistant', text: "죄송합니다. 오류가 발생했습니다." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={`chatbot-container ${isOpen ? 'open' : ''}`}>
            {!isOpen && (
                <button className="chat-toggle-btn" onClick={() => setIsOpen(true)}>
                    💬 AI Chat
                </button>
            )}

            {isOpen && (
                <div className="chat-window card">
                    <div className="chat-header">
                        <h3>AI Assistant</h3>
                        <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
                    </div>

                    <div className="chat-messages">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`message ${msg.role}`}>
                                <div className="message-bubble">
                                    {msg.role === 'assistant' ? <ReactMarkdown>{msg.text}</ReactMarkdown> : msg.text}
                                </div>
                            </div>
                        ))}
                        {loading && <div className="message assistant"><div className="message-bubble">...</div></div>}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="chat-input-area">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="질문을 입력하세요..."
                        />
                        <button onClick={handleSend} disabled={loading}>Send</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatBot;
