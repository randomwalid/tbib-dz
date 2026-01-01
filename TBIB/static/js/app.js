/**
 * TBIB - App Core (Alpine.js)
 * Gère : Offline Mode, Notifications, Interactions
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        isOnline: navigator.onLine,
        
        init() {
            window.addEventListener('online', () => this.isOnline = true);
            window.addEventListener('offline', () => this.isOnline = false);
        }
    }));
});
