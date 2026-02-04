/**
 * Authentication API client
 */
import { apiRequest, setAuthToken, removeAuthToken, API_URL } from './config';

/**
 * Register a new user
 * @param {Object} userData - { email, username, password }
 */
export const register = async (userData) => {
    const response = await apiRequest('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(userData),
    });

    // Store token
    setAuthToken(response.access_token);

    return response;
};

/**
 * Login user
 * @param {Object} credentials - { email, password }
 */
export const login = async (credentials) => {
    const response = await apiRequest('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
    });

    // Store token
    setAuthToken(response.access_token);

    return response;
};

/**
 * Logout user (local only)
 */
export const logout = () => {
    removeAuthToken();
};

/**
 * Get current user
 */
export const getCurrentUser = async () => {
    return apiRequest('/api/auth/me');
};

/**
 * Verify token validity
 */
export const verifyToken = async () => {
    return apiRequest('/api/auth/verify', { method: 'POST' });
};
