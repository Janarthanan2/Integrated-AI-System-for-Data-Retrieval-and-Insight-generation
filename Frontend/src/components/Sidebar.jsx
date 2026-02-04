/**
 * Sidebar Component
 * Displays conversation history with search and new chat functionality
 */
import React, { useState } from 'react';
import {
    MessageSquare,
    Plus,
    Search,
    Trash2,
    Edit3,
    Check,
    X,
    Clock,
    Loader
} from 'lucide-react';
import { useConversations } from '../contexts/ConversationsContext';

const Sidebar = ({ isOpen, onClose }) => {
    const {
        conversations,
        activeConversationId,
        isLoadingSidebar,
        selectConversation,
        startNewChat,
        deleteConversation,
        updateTitle,
    } = useConversations();

    const [searchQuery, setSearchQuery] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editTitle, setEditTitle] = useState('');
    const [deletingId, setDeletingId] = useState(null);

    // Filter conversations by search
    const filteredConversations = conversations.filter(conv =>
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.last_message?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Format relative time
    const formatTime = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    // Start editing title
    const handleStartEdit = (e, conv) => {
        e.stopPropagation();
        setEditingId(conv.id);
        setEditTitle(conv.title);
    };

    // Save edited title
    const handleSaveEdit = async (e) => {
        e.stopPropagation();
        if (editTitle.trim()) {
            await updateTitle(editingId, editTitle.trim());
        }
        setEditingId(null);
    };

    // Cancel editing
    const handleCancelEdit = (e) => {
        e.stopPropagation();
        setEditingId(null);
    };

    // Handle delete
    const handleDelete = async (e, convId) => {
        e.stopPropagation();
        setDeletingId(convId);
        try {
            await deleteConversation(convId);
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <div
            className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}
            style={{
                width: '280px',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: '#FAFAFA',
                borderRight: '1px solid #E5E7EB',
            }}
        >
            {/* Header */}
            <div className="p-3 border-bottom">
                <button
                    onClick={startNewChat}
                    className="btn w-100 d-flex align-items-center justify-content-center gap-2 py-2"
                    style={{
                        background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)',
                        border: 'none',
                        color: 'white',
                        borderRadius: '10px',
                        fontWeight: '500',
                    }}
                >
                    <Plus size={18} />
                    New Chat
                </button>
            </div>

            {/* Search */}
            <div className="px-3 py-2">
                <div className="position-relative">
                    <Search
                        size={16}
                        className="position-absolute text-muted"
                        style={{ left: '12px', top: '50%', transform: 'translateY(-50%)' }}
                    />
                    <input
                        type="text"
                        placeholder="Search conversations..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="form-control form-control-sm"
                        style={{
                            paddingLeft: '36px',
                            backgroundColor: '#F3F4F6',
                            border: 'none',
                            borderRadius: '8px',
                        }}
                    />
                </div>
            </div>

            {/* Conversations List */}
            <div
                className="flex-grow-1 overflow-auto px-2 py-1"
                style={{ scrollbarWidth: 'thin' }}
            >
                {isLoadingSidebar ? (
                    <div className="d-flex justify-content-center align-items-center py-4">
                        <Loader size={24} className="text-muted animate-spin" />
                    </div>
                ) : filteredConversations.length === 0 ? (
                    <div className="text-center py-4 text-muted small">
                        {searchQuery ? 'No matching conversations' : 'No conversations yet'}
                    </div>
                ) : (
                    filteredConversations.map(conv => (
                        <div
                            key={conv.id}
                            onClick={() => selectConversation(conv.id)}
                            className={`conversation-item p-2 rounded-2 mb-1 cursor-pointer ${activeConversationId === conv.id ? 'active' : ''
                                }`}
                            style={{
                                backgroundColor: activeConversationId === conv.id ? '#FFE5E5' : 'transparent',
                                cursor: 'pointer',
                                transition: 'all 0.15s ease',
                            }}
                        >
                            <div className="d-flex align-items-start gap-2">
                                <MessageSquare
                                    size={16}
                                    className="mt-1 flex-shrink-0"
                                    style={{ color: activeConversationId === conv.id ? '#FF6B6B' : '#9CA3AF' }}
                                />

                                <div className="flex-grow-1 min-width-0">
                                    {editingId === conv.id ? (
                                        <div className="d-flex gap-1">
                                            <input
                                                type="text"
                                                value={editTitle}
                                                onChange={(e) => setEditTitle(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                className="form-control form-control-sm py-0"
                                                style={{ fontSize: '13px' }}
                                                autoFocus
                                            />
                                            <button
                                                className="btn btn-link p-0 text-success"
                                                onClick={handleSaveEdit}
                                            >
                                                <Check size={14} />
                                            </button>
                                            <button
                                                className="btn btn-link p-0 text-muted"
                                                onClick={handleCancelEdit}
                                            >
                                                <X size={14} />
                                            </button>
                                        </div>
                                    ) : (
                                        <>
                                            <div
                                                className="fw-medium text-truncate"
                                                style={{ fontSize: '13px', color: '#374151' }}
                                            >
                                                {conv.title}
                                            </div>
                                            {conv.last_message && (
                                                <div
                                                    className="text-truncate text-muted"
                                                    style={{ fontSize: '11px' }}
                                                >
                                                    {conv.last_message}
                                                </div>
                                            )}
                                            <div
                                                className="d-flex align-items-center gap-1 text-muted mt-1"
                                                style={{ fontSize: '10px' }}
                                            >
                                                <Clock size={10} />
                                                {formatTime(conv.updated_at)}
                                            </div>
                                        </>
                                    )}
                                </div>

                                {/* Actions */}
                                {editingId !== conv.id && (
                                    <div className="conversation-actions d-flex gap-1">
                                        <button
                                            className="btn btn-link p-1 text-muted"
                                            onClick={(e) => handleStartEdit(e, conv)}
                                            title="Rename"
                                        >
                                            <Edit3 size={12} />
                                        </button>
                                        <button
                                            className="btn btn-link p-1 text-danger"
                                            onClick={(e) => handleDelete(e, conv.id)}
                                            disabled={deletingId === conv.id}
                                            title="Delete"
                                        >
                                            {deletingId === conv.id ? (
                                                <Loader size={12} className="animate-spin" />
                                            ) : (
                                                <Trash2 size={12} />
                                            )}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Footer */}
            <div className="p-2 border-top text-center">
                <small className="text-muted" style={{ fontSize: '10px' }}>
                    {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
                </small>
            </div>
        </div>
    );
};

export default Sidebar;
