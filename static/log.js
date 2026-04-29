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


// ── Running — live pace calculation ─────────────────────────────────────────

const runDistance = document.getElementById('run-distance');
const runDuration = document.getElementById('run-duration');
const runPace     = document.getElementById('run-pace');

function updatePace() {
    const km  = parseFloat(runDistance.value);
    const min = parseFloat(runDuration.value);
    if (km > 0 && min > 0) {
        const paceDecimal = min / km;
        const paceMin     = Math.floor(paceDecimal);
        const paceSec     = Math.round((paceDecimal - paceMin) * 60).toString().padStart(2, '0');
        runPace.value = `${paceMin}:${paceSec} min/km`;
    } else {
        runPace.value = '';
    }
}

runDistance.addEventListener('change', updatePace);
runDuration.addEventListener('input',  updatePace);


// ── Climbing / Calisthenics sub-type toggle ─────────────────────────────────

const climbingRadios     = document.querySelectorAll('input[name="climbing-type"]');
const climbingFields     = document.getElementById('climbing-fields');
const calisthenicsFields = document.getElementById('calisthenics-fields');

climbingRadios.forEach(radio => {
    radio.addEventListener('change', () => {
        const isClimbing = radio.value === 'climbing';
        climbingFields.hidden     = !isClimbing;
        calisthenicsFields.hidden =  isClimbing;
    });
});