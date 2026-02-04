import React, { useRef, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import AnalyticsCharts from './AnalyticsCharts';
import { BarChart2, TrendingDown, Trophy } from 'lucide-react';

const ChatHistory = ({ history, isLoading, onQuickAction }) => {
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [history]);

    const formatMessage = (text) => {
        if (!text) return "";
        let html = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/`(.*?)`/g, '<code class="px-1 rounded">$1</code>');
        return html;
    };

    if (history.length === 0) {
        return (
            <div className="h-100 d-flex flex-column align-items-center justify-content-center text-center">
                <div className="mb-4 position-relative">
                    <div className="position-absolute top-50 start-50 translate-middle" style={{ width: '200px', height: '200px', background: 'radial-gradient(circle, rgba(244, 63, 94, 0.2) 0%, transparent 70%)', filter: 'blur(40px)' }}></div>
                    <div className="bg-white p-4 rounded-circle shadow-sm border border-rose-100 position-relative z-10">
                        <Sparkles size={48} className="text-rose-500" />
                    </div>
                </div>
                <h1 className="fw-bold mb-2" style={{
                    background: 'linear-gradient(135deg, #111827 30%, #F43F5E 100%)',
                    WebkitBackgroundClip: 'text',
                    backgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    color: 'transparent',
                    filter: 'drop-shadow(0 2px 10px rgba(244, 63, 94, 0.2))',
                    fontSize: '2.5rem'
                }}>
                    How can I help you?
                </h1>
                <p className="text-gray-500 max-w-md fs-5">
                    I can analyze data, generate reports, or visualize trends for you.
                </p>

                <div className="d-flex gap-3 mt-4 flex-wrap justify-content-center">
                    <button onClick={() => onQuickAction("Show total sales")}
                        className="px-4 py-3 text-sm text-gray-700 hover:text-rose-600 d-flex align-items-center gap-2 transition-all shadow-sm hover:shadow-lg hover:-translate-y-1 border border-gray-100 rounded-xl"
                        style={{ background: 'linear-gradient(to bottom right, #ffffff, #f9fafb)' }}
                    >
                        <BarChart2 size={16} /> Total Sales
                    </button>
                    <button onClick={() => onQuickAction("Analyze profit trends")}
                        className="px-4 py-3 text-sm text-gray-700 hover:text-rose-600 d-flex align-items-center gap-2 transition-all shadow-sm hover:shadow-lg hover:-translate-y-1 border border-gray-100 rounded-xl"
                        style={{ background: 'linear-gradient(to bottom right, #ffffff, #f9fafb)' }}
                    >
                        <TrendingDown size={16} /> Profit Trends
                    </button>
                    <button onClick={() => onQuickAction("Top 5 products")}
                        className="px-4 py-3 text-sm text-gray-700 hover:text-rose-600 d-flex align-items-center gap-2 transition-all shadow-sm hover:shadow-lg hover:-translate-y-1 border border-gray-100 rounded-xl"
                        style={{ background: 'linear-gradient(to bottom right, #ffffff, #f9fafb)' }}
                    >
                        <Trophy size={16} /> Top Products
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-grow-1 overflow-auto p-4 custom-scrollbar d-flex flex-column" id="chat-container">
            {history.map((msg, idx) => (
                <div key={idx} className={`d-flex mb-5 gap-3 ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
                    {msg.role === 'assistant' && (
                        <div className="flex-shrink-0 mt-1">
                            <div className="rounded-circle d-flex align-items-center justify-content-center shadow-sm"
                                style={{ width: '36px', height: '36px', background: 'var(--theme-primary)' }}>
                                <Sparkles size={18} className="text-white" />
                            </div>
                        </div>
                    )}

                    <div className={`d-flex flex-column ${msg.role === 'user' ? 'align-items-end' : 'align-items-start'}`} style={{ maxWidth: '80%' }}>
                        {msg.role === 'user' ? (
                            <div className="p-3 px-4 shadow-sm"
                                style={{
                                    color: 'var(--bubble-user-text)',
                                    borderRadius: '24px 24px 0 24px',
                                    background: 'linear-gradient(135deg, #111827 0%, #1f2937 100%)' // Subtle gradient for user
                                }}>
                                {msg.content}
                            </div>
                        ) : (
                            <div className="p-4 shadow-sm"
                                style={{
                                    background: 'var(--bubble-bot-bg)',
                                    color: 'var(--bubble-bot-text)',
                                    borderRadius: '0 24px 24px 24px',
                                    border: '1px solid #E5E7EB'
                                }}>
                                <div dangerouslySetInnerHTML={{
                                    __html: formatMessage(msg.content) +
                                        (isLoading && idx === history.length - 1 && msg.role === 'assistant' ? '<span class="typing-cursor"></span>' : '')
                                }} />
                                {msg.chart && msg.chart.data && (
                                    <div className="mt-4 rounded-xl overflow-hidden border border-gray-200 bg-white p-1 shadow-sm">
                                        <AnalyticsCharts data={msg.chart.data} type={msg.chart.type} />
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            ))}
            <div ref={messagesEndRef} />
        </div>
    );
};

export default React.memo(ChatHistory);
