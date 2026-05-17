// log.js — Log Exercise page interactivity

// ── Sport selector ──────────────────────────────────────────────────────────

const sportButtons = document.querySelectorAll('.lb-filter-btn[data-sport]');
const sportForms   = document.querySelectorAll('.log-sport-form');

sportButtons.forEach(button => {
    button.addEventListener('click', () => {
        sportButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        const selectedSport = button.dataset.sport;
        sportForms.forEach(form => {
            form.hidden = form.dataset.sport !== selectedSport;
        });
    });
});


// ── Shared helpers ───────────────────────────────────────────────────────────

function showFeedback(feedbackEl, message, isError) {
    feedbackEl.textContent    = message;
    feedbackEl.style.display  = 'block';
    feedbackEl.style.color    = isError ? '#f87171' : '#00c896';
}

async function postLog(exerciseId, statValue) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const response = await fetch('/log', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ exercise_id: exerciseId, stat_value: statValue })
    });
    return response.json();
}

async function handleSubmit(btn, feedbackEl, exerciseId, statValue) {
    btn.disabled     = true;
    btn.textContent  = 'Saving…';
    try {
        const result = await postLog(exerciseId, statValue);
        if (result.success) {
            showFeedback(feedbackEl, `Saved ${result.exercise}!`, false);
        } else {
            showFeedback(feedbackEl, result.error || 'Something went wrong.', true);
        }
    } catch {
        showFeedback(feedbackEl, 'Network error — could not save.', true);
    } finally {
        btn.disabled    = false;
        btn.textContent = 'Save Session';
    }
}


// ── Lifting ──────────────────────────────────────────────────────────────────

const liftSubmitBtn = document.getElementById('lift-submit-btn');
const liftFeedback  = document.getElementById('lift-feedback');

liftSubmitBtn.addEventListener('click', async () => {
    const exerciseId = parseInt(document.querySelector('[data-sport="lifting"] .log-select').value);
    const weight     = parseFloat(document.getElementById('lift-weight').value);
    const userweight = parseFloat(document.getElementById('current-weight').value);

    if (!exerciseId) { showFeedback(liftFeedback, 'Please select an exercise.', true); return; }
    if (!weight)     { showFeedback(liftFeedback, 'Please enter a weight.', true); return; }
    if (!userweight) { showFeedback(liftFeedback, 'Please enter your current weight.', true); return; }

    const statValue = parseFloat((weight / userweight).toFixed(3));
    await handleSubmit(liftSubmitBtn, liftFeedback, exerciseId, statValue);
});


// ── Running ──────────────────────────────────────────────────────────────────

const runSubmitBtn = document.getElementById('run-submit-btn');
const runFeedback  = document.getElementById('run-feedback');

runSubmitBtn.addEventListener('click', async () => {
    const exerciseId = parseInt(document.getElementById('run-exercise').value);
    const minutes    = parseFloat(document.getElementById('run-minutes').value) || 0;
    const seconds    = parseFloat(document.getElementById('run-seconds').value) || 0;

    if (!exerciseId)                    { showFeedback(runFeedback, 'Please select a distance.', true); return; }
    if (minutes === 0 && seconds === 0) { showFeedback(runFeedback, 'Please enter a time.', true); return; }

    const statValue = -((minutes * 60) + seconds);
    await handleSubmit(runSubmitBtn, runFeedback, exerciseId, statValue);
});


// ── Swimming stroke → distance filter ───────────────────────────────────────

const swimStrokeSelect   = document.getElementById('swim-stroke');
const swimDistanceSelect = document.getElementById('swim-exercise');
const allSwimOptions     = Array.from(swimDistanceSelect.querySelectorAll('option[data-stroke]'));

swimStrokeSelect.addEventListener('change', () => {
    const selectedStroke = swimStrokeSelect.value;
    allSwimOptions.forEach(opt => opt.remove());
    const matching = allSwimOptions.filter(opt => opt.dataset.stroke === selectedStroke);
    matching.forEach(opt => swimDistanceSelect.appendChild(opt));
    swimDistanceSelect.value    = '';
    swimDistanceSelect.disabled = matching.length === 0;
    swimDistanceSelect.querySelector('option[disabled]').textContent =
        matching.length === 0 ? 'No distances available' : 'Choose a distance';
});


// ── Swimming ─────────────────────────────────────────────────────────────────

const swimSubmitBtn = document.getElementById('swim-submit-btn');
const swimFeedback  = document.getElementById('swim-feedback');

swimSubmitBtn.addEventListener('click', async () => {
    const exerciseId = parseInt(swimDistanceSelect.value);
    const minutes    = parseFloat(document.getElementById('swim-minutes').value) || 0;
    const seconds    = parseFloat(document.getElementById('swim-seconds').value) || 0;

    if (!exerciseId)                    { showFeedback(swimFeedback, 'Please select a stroke and distance.', true); return; }
    if (minutes === 0 && seconds === 0) { showFeedback(swimFeedback, 'Please enter a time.', true); return; }

    const statValue = -((minutes * 60) + seconds);
    await handleSubmit(swimSubmitBtn, swimFeedback, exerciseId, statValue);
});


// ── Cycling ──────────────────────────────────────────────────────────────────

const cycleSubmitBtn = document.getElementById('cycle-submit-btn');
const cycleFeedback  = document.getElementById('cycle-feedback');

cycleSubmitBtn.addEventListener('click', async () => {
    const exerciseId = parseInt(document.getElementById('cycle-exercise').value);
    const minutes    = parseFloat(document.getElementById('cycle-minutes').value) || 0;
    const seconds    = parseFloat(document.getElementById('cycle-seconds').value) || 0;

    if (!exerciseId)                    { showFeedback(cycleFeedback, 'Please select a distance.', true); return; }
    if (minutes === 0 && seconds === 0) { showFeedback(cycleFeedback, 'Please enter a time.', true); return; }

    const statValue = -((minutes * 60) + seconds);
    await handleSubmit(cycleSubmitBtn, cycleFeedback, exerciseId, statValue);
});


// ── Plyometrics exercise → input type toggle ─────────────────────────────────

const plyoSelect = document.getElementById('plyo-exercise');

plyoSelect.addEventListener('change', function () {
    const units  = this.options[this.selectedIndex].dataset.units;
    const isTime = units === 'seconds';
    document.getElementById('plyo-time-input').hidden  = !isTime;
    document.getElementById('plyo-value-input').hidden =  isTime;
    document.getElementById('plyo-value-label').textContent =
        units === 'cm' ? 'Distance (cm)' : 'Reps';
});


// ── Plyometrics ───────────────────────────────────────────────────────────────

const plyoSubmitBtn = document.getElementById('plyo-submit-btn');
const plyoFeedback  = document.getElementById('plyo-feedback');

plyoSubmitBtn.addEventListener('click', async () => {
    const exerciseId = parseInt(plyoSelect.value);
    const units      = plyoSelect.options[plyoSelect.selectedIndex]?.dataset.units;

    if (!exerciseId) { showFeedback(plyoFeedback, 'Please select an exercise.', true); return; }

    let statValue;
    if (units === 'seconds') {
        const minutes = parseFloat(document.getElementById('plyo-minutes').value) || 0;
        const seconds = parseFloat(document.getElementById('plyo-seconds').value) || 0;
        if (minutes === 0 && seconds === 0) { showFeedback(plyoFeedback, 'Please enter a time.', true); return; }
        statValue = -((minutes * 60) + seconds);
    } else {
        statValue = parseFloat(document.getElementById('plyo-value').value);
        if (!statValue) { showFeedback(plyoFeedback, 'Please enter a value.', true); return; }
    }

    await handleSubmit(plyoSubmitBtn, plyoFeedback, exerciseId, statValue);
});