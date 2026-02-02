import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { AnalysisSection } from './components/AnalyticsCharts'
import { ModernTable, ModernThead, ModernTbody, ModernTr, ModernTh, ModernTd } from './components/MarkdownComponents'

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Chart Error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="p-4 m-4 bg-red-900/20 border border-red-500 rounded text-red-200">
                    <p className="font-bold">Chart Failed to Render</p>
                    <pre className="text-xs mt-2 overflow-auto">{this.state.error.toString()}</pre>
                </div>
            );
        }
        return this.props.children;
    }
}

function AnimatedMessage({ content, role, isLast }) {
    const [display, setDisplay] = useState('')

    useEffect(() => {
        // If not AI or not the last message, show immediately
        if (role !== 'ai' || !isLast) {
            setDisplay(content)
            return
        }

        // Typing logic for active AI message
        if (display === content) return

        // If content grew, schedule next character
        if (content.length > display.length) {
            const timeout = setTimeout(() => {
                setDisplay(content.slice(0, display.length + 1))
            }, 15) // Speed: 15ms per char
            return () => clearTimeout(timeout)
        } else {
            // If content shrank (reset?), reset display
            setDisplay(content)
        }
    }, [content, role, isLast, display])

    return (
        <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
                table: ModernTable,
                thead: ModernThead,
                tbody: ModernTbody,
                tr: ModernTr,
                th: ModernTh,
                td: ModernTd
            }}
        >
            {display}
        </ReactMarkdown>
    )
}

function App() {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [followUps, setFollowUps] = useState([])
    const messagesEndRef = useRef(null)
    const abortControllerRef = useRef(null)

    // Function to handle stop
    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort()
            abortControllerRef.current = null
        }
        setIsLoading(false)
        setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last.role === 'ai') {
                return [...prev.slice(0, -1), { ...last, content: last.content + ' [Stopped]' }]
            }
            return prev
        })
    }

    const sendMessage = async (queryOverride = null) => {
        const textToSend = typeof queryOverride === 'string' ? queryOverride : input
        if (!textToSend.trim()) return

        // Abort previous if any
        if (abortControllerRef.current) abortControllerRef.current.abort()

        const controller = new AbortController()
        abortControllerRef.current = controller

        const userMsg = { role: 'user', content: textToSend }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setFollowUps([])
        setIsLoading(true)

        try {
            // Initial placeholder for AI response
            const aiMsgId = Date.now()
            setMessages(prev => [...prev, {
                role: 'ai',
                id: aiMsgId,
                content: '',
                thoughts: [],
                tool: null,
                chart: null
            }])

            // Convert existing messages to history format (User/AI)
            const history = messages
                .filter(m => m.role !== 'system') // Filter out system messages if any
                .map(m => ({
                    role: m.role,
                    content: m.content
                }));

            const response = await fetch('http://localhost:8000/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: textToSend,
                    history: history
                }),
                signal: controller.signal
            })

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ''

            // Streaming Loop
            while (true) {
                const { value, done } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop() // Keep incomplete line in buffer

                for (const line of lines) {
                    if (!line.trim()) continue

                    try {
                        const event = JSON.parse(line)

                        setMessages(prev => prev.map(msg => {
                            if (msg.id !== aiMsgId) return msg

                            if (event.type === 'thought') {
                                return { ...msg, thoughts: [...(msg.thoughts || []), event.content] }
                            }
                            if (event.type === 'tool') {
                                return { ...msg, tool: event.content }
                            }
                            if (event.type === 'token') {
                                return { ...msg, content: msg.content + event.chunk }
                            }
                            if (event.type === 'meta') {
                                return {
                                    ...msg,
                                    tool: `${event.intent} (${event.scope || 'Global'})`,
                                    chart: event.chart ? { ...event.chart, title: `${event.intent} Analysis` } : null
                                }
                            }
                            if (event.type === 'error') {
                                return { ...msg, content: msg.content + `\n\n[Error: ${event.content}]` }
                            }
                            return msg
                        }))

                    } catch (e) {
                        console.error("JSON Parse Error", e)
                    }
                }
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Request aborted')
            } else {
                setMessages(prev => [...prev, { role: 'ai', content: "Error: Could not connect to the backend." }])
            }
        } finally {
            if (abortControllerRef.current === controller) {
                setIsLoading(false)
                abortControllerRef.current = null
            }
        }
    }

    const getIconForQuestion = (text) => {
        // ... (No changes) ...
        const lower = text.toLowerCase()
        if (lower.includes('trend') || lower.includes('growth') || lower.includes('time')) return '📈'
        if (lower.includes('breakdown') || lower.includes('category') || lower.includes('distribution')) return '🗂'
        if (lower.includes('why') || lower.includes('cause') || lower.includes('reason') || lower.includes('analysis')) return '🔍'
        if (lower.includes('compare') || lower.includes('difference')) return '⚖️'
        return '✨'
    }

    const preprocessMarkdown = (text) => {
        if (!text) return text
        // Fix: Remove leading whitespace from every line to prevent accidental code blocks
        return text.split('\n').map(line => line.trimStart()).join('\n')
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !isLoading) sendMessage()
    }

    return (
        <div className="container">
            <div className="background-mesh">
                <div className="blob blob-1"></div>
                <div className="blob blob-2"></div>
                <div className="blob blob-3"></div>
            </div>
            <header>
                <div className="glass-panel" style={{ padding: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Sparkles size={24} color="#818cf8" />
                </div>
                <h1>AI Analytics System</h1>
            </header>

            <main className="glass-panel chat-container">
                <div className="messages-area">
                    {messages.length === 0 && (
                        <div style={{
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            textAlign: 'center',
                            opacity: 0.9,
                            animation: 'fadeInUp 0.6s ease-out'
                        }}>
                            <div style={{
                                background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                padding: '1.5rem',
                                borderRadius: '24px',
                                marginBottom: '1.5rem',
                                boxShadow: '0 10px 25px -5px rgba(99, 102, 241, 0.4)'
                            }}>
                                <Sparkles size={48} color="white" />
                            </div>
                            <h2 style={{
                                fontSize: '2rem',
                                fontWeight: '700',
                                marginBottom: '0.5rem',
                                background: 'linear-gradient(to right, #fff, #cbd5e1)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent'
                            }}>
                                How can I help you today?
                            </h2>
                            <p style={{ color: '#94a3b8', maxWidth: '400px', lineHeight: '1.6', marginBottom: '2.5rem' }}>
                                I can analyze your sales data, identify trends, and generate reports instantly.
                            </p>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', width: '100%', maxWidth: '600px' }}>
                                {[
                                    { icon: '📈', text: 'Analyze monthly sales trends' },
                                    { icon: '🌍', text: 'Compare regional performance' },
                                    { icon: '⚠️', text: 'Identify declining categories' },
                                    { icon: '📊', text: 'Show top selling products' }
                                ].map((item, i) => (
                                    <button
                                        key={i}
                                        onClick={() => sendMessage(item.text)}
                                        style={{
                                            background: 'rgba(30, 41, 59, 0.4)',
                                            border: '1px solid rgba(255, 255, 255, 0.05)',
                                            padding: '1.2rem',
                                            borderRadius: '16px',
                                            color: '#e2e8f0',
                                            textAlign: 'left',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '1rem',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s',
                                            fontSize: '0.95rem',
                                            width: 'auto',
                                            height: 'auto'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.background = 'rgba(30, 41, 59, 0.7)'
                                            e.currentTarget.style.transform = 'translateY(-2px)'
                                            e.currentTarget.style.borderColor = '#6366f1'
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.background = 'rgba(30, 41, 59, 0.4)'
                                            e.currentTarget.style.transform = 'translateY(0)'
                                            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.05)'
                                        }}
                                    >
                                        <span style={{ fontSize: '1.5rem' }}>{item.icon}</span>
                                        {item.text}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`message ${msg.role}`}>
                            {msg.tool && <span className="tool-badge">Source: {msg.tool}</span>}
                            <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
                                {msg.role === 'ai' ? <Bot size={20} /> : <User size={20} />}
                                <div className="markdown-content">
                                    <AnimatedMessage
                                        content={preprocessMarkdown(msg.content)}
                                        role={msg.role}
                                        isLast={idx === messages.length - 1}
                                    />
                                    {msg.chart && (
                                        <ErrorBoundary>
                                            <AnalysisSection
                                                type={msg.chart.type}
                                                title={msg.chart.title}
                                                data={msg.chart.data}
                                                loading={false}
                                            />
                                        </ErrorBoundary>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}


                    {!isLoading && followUps.length > 0 && (
                        <div className="follow-up-container">
                            <span className="follow-up-label">Suggested Actions:</span>
                            <div className="chips-grid">
                                {followUps.map((q, idx) => (
                                    <button
                                        key={idx}
                                        className="chip"
                                        onClick={() => sendMessage(q)}
                                        disabled={isLoading}
                                    >
                                        <span className="chip-icon">{getIconForQuestion(q)}</span>
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="input-area">
                    <input
                        type="text"
                        placeholder="Ask a question (e.g., 'Total sales from tables' or 'Explain regional performance')"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        disabled={isLoading}
                    />
                    {isLoading ? (
                        <button
                            onClick={handleStop}
                            style={{
                                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                                border: '1px solid rgba(239, 68, 68, 0.4)',
                                color: '#fca5a5'
                            }}
                            title="Stop Generation"
                        >
                            <div style={{ width: '12px', height: '12px', background: 'currentColor', borderRadius: '2px' }}></div>
                        </button>
                    ) : (
                        <button onClick={() => sendMessage()} disabled={isLoading}>
                            <Send size={20} />
                        </button>
                    )}
                </div>
            </main>
        </div>
    )
}

export default App
