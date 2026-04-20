// leaderboard.js — Leaderboard page interactivity

// Filter leaderboard rows by sport when a tab button is clicked
const filterButtons = document.querySelectorAll('.lb-filter-btn');
const tableRows = document.querySelectorAll('.lb-table tbody tr');

filterButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Update active tab styling
        filterButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        const selectedSport = button.dataset.sport;

        // Show rows matching the selected sport, hide the rest
        tableRows.forEach(row => {
            const rowSport = row.dataset.sport;
            if (selectedSport === 'all' || rowSport === selectedSport) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
});
