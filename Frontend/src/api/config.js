/**
 * API Configuration
 */
// export const API_URL = "http://127.0.0.1:8000";
export const API_URL = ""; // Relative path for proxying
export const AUTH_TOKEN_KEY = "nova_auth_token";

/**
 * Get stored auth token
 */
export const getAuthToken = () => {
    return localStorage.getItem(AUTH_TOKEN_KEY);
};

/**
 * Set auth token
 */
export const setAuthToken = (token) => {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
};

/**
 * Remove auth token
 */
export const removeAuthToken = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
};

/**
 * Create headers with auth token
 */
export const authHeaders = () => {
    const token = getAuthToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * API request helper with auth
 */
export const apiRequest = async (endpoint, options = {}) => {
    const url = `${API_URL}${endpoint}`;
    const headers = {
        "Content-Type": "application/json",
        ...authHeaders(),
        ...options.headers,
    };

    const response = await fetch(url, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
};
