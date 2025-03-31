// Global analytics tracking
const analytics = {
    startTime: new Date(),
    viewedSections: new Set(),
    
    init() {
        // Send initial page view
        this.trackPageView();
        
        // Track when user leaves the page
        window.addEventListener('beforeunload', () => this.trackPageExit());
        
        // Track section views
        document.querySelectorAll('[data-track-section]').forEach(element => {
            element.addEventListener('click', () => {
                const section = element.getAttribute('data-track-section');
                this.viewedSections.add(section);
            });
        });
    },
    
    trackPageView() {
        fetch('/track-demo-view', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                page: window.location.pathname,
                timestamp: new Date().toISOString(),
                sections_viewed: [],
                session_duration: 0
            })
        }).catch(error => console.error('Analytics error:', error));
    },
    
    trackPageExit() {
        const endTime = new Date();
        const duration = Math.round((endTime - this.startTime) / 1000); // Duration in seconds
        
        fetch('/track-demo-view', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                page: window.location.pathname,
                timestamp: new Date().toISOString(),
                sections_viewed: Array.from(this.viewedSections),
                session_duration: duration
            })
        });
    }
};

// Initialize analytics when the page loads
document.addEventListener('DOMContentLoaded', () => analytics.init()); 