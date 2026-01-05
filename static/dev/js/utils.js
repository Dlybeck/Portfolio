const DevUtils = {
    getToken() {
        return localStorage.getItem('access_token');
    },
    
    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        document.cookie = 'session_token=; Max-Age=0; path=/;';
        window.location.href = '/dev/login';
    },
    
    navigateTo(path) {
        const token = this.getToken();
        if (token) {
            window.location.href = `${path}?tkn=${token}`;
        } else {
            window.location.href = '/dev/login';
        }
    },
    
    isMobile() {
        return window.innerWidth <= 768;
    }
};

if (typeof module !== 'undefined') module.exports = DevUtils;
