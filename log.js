// log.js — Log Exercise page interactivity

// ── Sport selector ──────────────────────────────────────────────────────────

const sportButtons = document.querySelectorAll('.lb-filter-btn[data-sport]');
const sportForms   = document.querySelectorAll('.log-sport-form');

sportButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Update active pill styling
        sportButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        const selectedSport = button.dataset.sport;

        // Hide all sport forms, then reveal the matching one
        sportForms.forEach(form => {
            form.hidden = form.dataset.sport !== selectedSport;
        });
    });
});


// ── Climbing / Calisthenics sub-type toggle ─────────────────────────────────

const climbingRadios      = document.querySelectorAll('input[name="climbing-type"]');
const climbingFields      = document.getElementById('climbing-fields');
const calisthenicsFields  = document.getElementById('calisthenics-fields');

climbingRadios.forEach(radio => {
    radio.addEventListener('change', () => {
        const isClimbing = radio.value === 'climbing';
        climbingFields.hidden     = !isClimbing;
        calisthenicsFields.hidden =  isClimbing;
    });
});
