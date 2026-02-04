/**
 * Conversations API client
 */
import { apiRequest } from './config';

/**
 * Get sidebar conversations
 * @param {number} limit - Max conversations to fetch
 */
export const getSidebar = async (limit = 50) => {
    return apiRequest(`/api/conversations/sidebar?limit=${limit}`);
};

/**
 * Create a new conversation
 * @param {Object} data - { title?, first_message? }
 */
export const createConversation = async (data = {}) => {
    return apiRequest('/api/conversations', {
        method: 'POST',
        body: JSON.stringify(data),
    });
};

/**
 * Get a specific conversation
 * @param {string} id - Conversation ID
 */
export const getConversation = async (id) => {
    return apiRequest(`/api/conversations/${id}`);
};

/**
 * Update conversation title
 * @param {string} id - Conversation ID
 * @param {string} title - New title
 */
export const updateConversationTitle = async (id, title) => {
    return apiRequest(`/api/conversations/${id}/title`, {
        method: 'PUT',
        body: JSON.stringify({ title }),
    });
};

/**
 * Delete a conversation
 * @param {string} id - Conversation ID
 */
export const deleteConversation = async (id) => {
    const response = await fetch(`${API_URL}/api/conversations/${id}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });

    if (!response.ok && response.status !== 204) {
        throw new Error('Failed to delete conversation');
    }

    return true;
};

/**
 * Get messages for a conversation (paginated)
 * @param {string} conversationId 
 * @param {number} page 
 * @param {number} pageSize 
 */
export const getMessages = async (conversationId, page = 1, pageSize = 30) => {
    return apiRequest(`/api/conversations/${conversationId}/messages?page=${page}&page_size=${pageSize}`);
};

/**
 * Send a message
 * @param {Object} data - { conversation_id?, content, role? }
 */
export const sendMessage = async (data) => {
    return apiRequest('/api/conversations/messages', {
        method: 'POST',
        body: JSON.stringify(data),
    });
};

/**
 * Get artifacts for a conversation
 * @param {string} conversationId 
 */
export const getArtifacts = async (conversationId) => {
    return apiRequest(`/api/conversations/${conversationId}/artifacts`);
};

// Import for deleteConversation
import { API_URL, authHeaders } from './config';
