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


// ── Swimming stroke → distance filter ───────────────────────────────────────

const swimStrokeSelect   = document.getElementById('swim-stroke');
const swimDistanceSelect = document.getElementById('swim-exercise');
const allSwimOptions     = Array.from(swimDistanceSelect.querySelectorAll('option[data-stroke]'));

swimStrokeSelect.addEventListener('change', () => {
    const selectedStroke = swimStrokeSelect.value;

    // Remove all exercise options, then re-add only matching ones
    allSwimOptions.forEach(opt => opt.remove());

    const matching = allSwimOptions.filter(opt => opt.dataset.stroke === selectedStroke);
    matching.forEach(opt => swimDistanceSelect.appendChild(opt));

    // Reset and enable the distance dropdown
    swimDistanceSelect.value = '';
    swimDistanceSelect.disabled = matching.length === 0;
    swimDistanceSelect.querySelector('option[disabled]').textContent =
        matching.length === 0 ? 'No distances available' : 'Choose a distance';
});


// ── Calisthenics sub-type toggle ─────────────────────────────────

document.getElementById('plyo-exercise').addEventListener('change', function () {
    const units = this.options[this.selectedIndex].dataset.units;
    const isTime = units === 'seconds';
    document.getElementById('plyo-time-input').hidden = !isTime;
    document.getElementById('plyo-value-input').hidden = isTime;
    document.getElementById('plyo-value-label').textContent =
        units === 'cm' ? 'Distance (cm)' : 'Reps';
});