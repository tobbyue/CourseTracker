/**
 * CourseTracker - Main JavaScript
 * Group CT - Course Management and Tracking System
 *
 * Provides client-side interactivity for:
 * - CSRF token handling for AJAX requests
 * - Auto-dismiss alerts
 *
 * Loaded with defer attribute for non-blocking performance [Day 12].
 */
'use strict';

// ============================================================
// CSRF Token Helper (required for Django AJAX POST requests)
// ============================================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// ============================================================
// Auto-dismiss success/info alerts after 5 seconds
// defer ensures DOM is ready, so no DOMContentLoaded needed
// ============================================================
(function () {
    const alerts = document.querySelectorAll('.alert-success, .alert-info');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
})();
