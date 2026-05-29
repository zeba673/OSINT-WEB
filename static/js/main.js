document.addEventListener('DOMContentLoaded', function() {
    // Update status badge on page changes
    function updateStatus() {
        const badge = document.getElementById('status-badge');
        if (badge) {
            badge.textContent = 'Ready';
        }
    }

    // Auto-refresh for running searches
    if (document.querySelector('.progress')) {
        setTimeout(function() {
            location.reload();
        }, 5000);
    }
});
