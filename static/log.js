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


// ── Running form submission ──────────────────────────────────────────────────

const runSubmitBtn  = document.getElementById('run-submit-btn');
const runFeedback   = document.getElementById('run-feedback');

runSubmitBtn.addEventListener('click', async () => {
    const exerciseId = parseInt(document.getElementById('run-exercise').value);
    const minutes    = parseFloat(document.getElementById('run-minutes').value) || 0;
    const seconds    = parseFloat(document.getElementById('run-seconds').value) || 0;

    if (!exerciseId) { showFeedback(runFeedback, 'Please select a distance.', true); return; }
    if (minutes === 0 && seconds === 0) { showFeedback(runFeedback, 'Please enter a time.', true); return; }

    const statValue = -((minutes * 60) + seconds);

    runSubmitBtn.disabled = true;
    runSubmitBtn.textContent = 'Saving…';

    try {
        const result = await postLog(exerciseId, statValue);
        if (result.success) {
            showFeedback(runFeedback, `Saved ${result.exercise}!`, false);
        } else {
            showFeedback(runFeedback, result.error || 'Something went wrong.', true);
        }
    } catch {
        showFeedback(runFeedback, 'Network error — could not save.', true);
    } finally {
        runSubmitBtn.disabled = false;
        runSubmitBtn.textContent = 'Save Session';
    }
});


// ── Swimming form submission ─────────────────────────────────────────────────

function showFeedback(feedbackEl, message, isError) {
    feedbackEl.textContent = message;
    feedbackEl.style.display = 'block';
    feedbackEl.style.color = isError ? '#f87171' : '#00c896';
}

async function postLog(exerciseId, statValue) {
    const response = await fetch('/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exercise_id: exerciseId, stat_value: statValue })
    });
    return response.json();
}

const swimSubmitBtn = document.getElementById('swim-submit-btn');
const swimFeedback  = document.getElementById('swim-feedback');

swimSubmitBtn.addEventListener('click', async () => {
    const exerciseId = parseInt(swimDistanceSelect.value);
    const minutes    = parseFloat(document.getElementById('swim-minutes').value) || 0;
    const seconds    = parseFloat(document.getElementById('swim-seconds').value) || 0;

    if (!exerciseId) { showFeedback(swimFeedback, 'Please select a stroke and distance.', true); return; }
    if (minutes === 0 && seconds === 0) { showFeedback(swimFeedback, 'Please enter a time.', true); return; }

    // Negative because faster time = better score
    const statValue = -((minutes * 60) + seconds);

    swimSubmitBtn.disabled = true;
    swimSubmitBtn.textContent = 'Saving…';

    try {
        const result = await postLog(exerciseId, statValue);
        if (result.success) {
            showFeedback(swimFeedback, `Saved ${result.exercise}!`, false);
        } else {
            showFeedback(swimFeedback, result.error || 'Something went wrong.', true);
        }
    } catch {
        showFeedback(swimFeedback, 'Network error — could not save.', true);
    } finally {
        swimSubmitBtn.disabled = false;
        swimSubmitBtn.textContent = 'Save Session';
    }
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
