/**
 * Authentication Service
 * Manages automatic token refresh to keep users logged in for 7 days
 */

class AuthService {
    constructor() {
        this.refreshInterval = null;
        this.CHECK_INTERVAL = 5 * 60 * 1000; // Check every 5 minutes
        this.REFRESH_BEFORE_EXPIRY = 5 * 60; // Refresh 5 minutes before expiration
    }

    /**
     * Start automatic token refresh monitoring
     */
    startAutoRefresh() {
        console.log('[AuthService] Starting automatic token refresh...');

        // Check immediately on start
        this.checkAndRefreshToken();

        // Then check every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.checkAndRefreshToken();
        }, this.CHECK_INTERVAL);
    }

    /**
     * Stop automatic token refresh monitoring
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('[AuthService] Stopped automatic token refresh');
        }
    }

    /**
     * Check if token needs refresh and refresh if needed
     */
    async checkAndRefreshToken() {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        const expiresIn = localStorage.getItem('expires_in');
        const loginTime = localStorage.getItem('login_time');

        if (!accessToken || !refreshToken || !expiresIn || !loginTime) {
            console.log('[AuthService] Missing token data, skipping refresh check');
            return;
        }

        // Calculate token age
        const now = Math.floor(Date.now() / 1000);
        const tokenAge = now - parseInt(loginTime);
        const expiresInSeconds = parseInt(expiresIn);
        const timeUntilExpiry = expiresInSeconds - tokenAge;

        console.log(`[AuthService] Token age: ${tokenAge}s, expires in: ${timeUntilExpiry}s`);

        // Refresh if less than 5 minutes until expiry
        if (timeUntilExpiry <= this.REFRESH_BEFORE_EXPIRY) {
            console.log('[AuthService] Token expiring soon, refreshing...');
            await this.refreshAccessToken(refreshToken);
        } else {
            console.log('[AuthService] Token still valid, no refresh needed');
        }
    }

    /**
     * Refresh the access token using the refresh token
     */
    async refreshAccessToken(refreshToken) {
        try {
            const response = await fetch('/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });

            if (response.ok) {
                const data = await response.json();

                // Update tokens in localStorage
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                localStorage.setItem('expires_in', data.expires_in.toString());
                localStorage.setItem('login_time', Math.floor(Date.now() / 1000).toString());

                console.log('[AuthService] Token refreshed successfully');
                return true;
            } else {
                console.error('[AuthService] Token refresh failed:', response.status);

                // If refresh fails, clear tokens and redirect to login
                if (response.status === 401) {
                    this.handleAuthFailure();
                }
                return false;
            }
        } catch (error) {
            console.error('[AuthService] Token refresh error:', error);
            return false;
        }
    }

    /**
     * Handle authentication failure (expired refresh token)
     */
    handleAuthFailure() {
        console.log('[AuthService] Authentication failed, redirecting to login...');

        // Clear all tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('expires_in');
        localStorage.removeItem('login_time');

        // Stop refresh interval
        this.stopAutoRefresh();

        // Redirect to login page
        window.location.href = '/dev/login';
    }

    /**
     * Store tokens after login
     */
    storeTokens(accessToken, refreshToken, expiresIn) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        localStorage.setItem('expires_in', expiresIn.toString());
        localStorage.setItem('login_time', Math.floor(Date.now() / 1000).toString());

        console.log('[AuthService] Tokens stored, expires in:', expiresIn, 'seconds');
    }

    /**
     * Clear all tokens and stop refresh
     */
    logout() {
        this.stopAutoRefresh();

        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('expires_in');
        localStorage.removeItem('login_time');

        console.log('[AuthService] Logged out and cleared tokens');
    }

    /**
     * Get session status for display
     */
    getSessionStatus() {
        const loginTime = localStorage.getItem('login_time');
        const expiresIn = localStorage.getItem('expires_in');

        if (!loginTime || !expiresIn) {
            return null;
        }

        const now = Math.floor(Date.now() / 1000);
        const tokenAge = now - parseInt(loginTime);
        const expiresInSeconds = parseInt(expiresIn);
        const timeUntilExpiry = expiresInSeconds - tokenAge;

        return {
            loginTime: new Date(parseInt(loginTime) * 1000),
            expiresIn: timeUntilExpiry,
            isValid: timeUntilExpiry > 0
        };
    }
}

// Create global instance
window.authService = new AuthService();
