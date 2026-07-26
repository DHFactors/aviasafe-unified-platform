/* ============================================================================
   FILE: app.js
   PATH: public/survey/app.js
   VERSION: 3.1.0
   DATE CREATED: 2026-07-26
   DATE REVISED: 2026-07-26
   PURPOSE: Two-step survey flow with proper option highlighting.
   ============================================================================ */

var currentQuestionIndex = 0;
var answers = [];
var questions = [];
var totalQuestions = 0;
var respondentInfo = {};

// ============================================================================
// STEP 1: INFO SCREEN
// ============================================================================

function skipInfo() {
    startSurvey();
}

function startSurvey() {
    respondentInfo = {
        name: document.getElementById('respondentName').value.trim(),
        designation: document.getElementById('respondentDesignation').value.trim(),
        department: document.getElementById('respondentDepartment').value.trim()
    };

    document.getElementById('infoScreen').style.display = 'none';
    document.getElementById('surveyScreen').classList.add('active');
    loadSurvey();
}

// ============================================================================
// STEP 2: SURVEY
// ============================================================================

function loadSurvey() {
    console.log("Loading survey...");

    if (typeof window.defaultQuestions !== 'undefined' && window.defaultQuestions.length > 0) {
        questions = window.defaultQuestions;
        console.log("Found", questions.length, "questions");
    } else {
        document.getElementById('surveyContainer').innerHTML = '<p style="text-align:center;color:#999;padding:40px;">No questions found.</p>';
        return;
    }

    totalQuestions = questions.length;
    answers = new Array(totalQuestions).fill(null);
    renderQuestion(0);
}

function renderQuestion(index) {
    var container = document.getElementById('surveyContainer');
    if (!container) return;

    if (!questions || index >= questions.length) {
        showComplete();
        return;
    }

    var q = questions[index];
    var progress = ((index + 1) / totalQuestions * 100).toFixed(0);
    var isLast = (index === totalQuestions - 1);
    var isOpenEnded = (q.isOpenEnded === true);
    var isChoice = (q.type === 'choice');
    var isLikert = (q.type === 'likert');

    var html = '';

    // Progress
    html += '<div class="survey-progress">';
    html += '<div class="progress-bar" style="width:' + progress + '%;"></div>';
    html += '<span class="progress-text">' + (index + 1) + ' of ' + totalQuestions + '</span>';
    html += '</div>';

    // Section header
    if (q.section && (index === 0 || questions[index-1]?.section !== q.section)) {
        html += '<div class="section-header">' + q.section + '</div>';
    }

    // Question
    html += '<div class="question-container">';
    html += '<div class="question-text">' + q.text + '</div>';
    html += '<div class="options-container">';

    if (isOpenEnded) {
        var val = answers[index] || '';
        html += '<textarea style="width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;font-size:16px;min-height:120px;resize:vertical;" placeholder="Share your thoughts..." onchange="selectOption(' + index + ', this.value)">' + val + '</textarea>';
    } else if (isChoice) {
        var choices = q.options || ['Aware', 'Unaware'];
        html += '<div class="choice-options">';
        choices.forEach(function(opt) {
            var sel = answers[index] === opt ? ' selected' : '';
            html += '<button class="option-btn' + sel + '" data-value="' + opt + '" onclick="selectOption(' + index + ', \'' + opt.replace(/'/g, "\\'") + '\')">' + opt + '</button>';
        });
        html += '</div>';
    } else if (isLikert) {
        var opts = q.options || ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];
        var row1 = opts.slice(0, 3);
        var row2 = opts.slice(3);

        html += '<div class="likert-row">';
        row1.forEach(function(opt) {
            var sel = answers[index] === opt ? ' selected' : '';
            var val = getLikertValue(opt);
            html += '<button class="option-btn' + sel + '" data-value="' + opt + '" onclick="selectOption(' + index + ', \'' + opt.replace(/'/g, "\\'") + '\')">';
            html += '<span class="value">' + val + '</span>';
            html += '<span class="label">' + opt + '</span>';
            html += '</button>';
        });
        html += '</div>';

        html += '<div class="likert-row">';
        row2.forEach(function(opt) {
            var sel = answers[index] === opt ? ' selected' : '';
            var val = getLikertValue(opt);
            html += '<button class="option-btn' + sel + '" data-value="' + opt + '" onclick="selectOption(' + index + ', \'' + opt.replace(/'/g, "\\'") + '\')">';
            html += '<span class="value">' + val + '</span>';
            html += '<span class="label">' + opt + '</span>';
            html += '</button>';
        });
        html += '</div>';
    }

    html += '</div></div>';

    // Navigation
    html += '<div class="navigation-buttons">';
    if (index > 0) {
        html += '<button class="btn btn-secondary" onclick="renderQuestion(' + (index-1) + ')">← Previous</button>';
    } else {
        html += '<div></div>';
    }
    var label = isLast ? 'Submit ✓' : 'Next →';
    html += '<button class="btn btn-primary" onclick="nextQuestion(' + index + ')">' + label + '</button>';
    html += '</div>';

    container.innerHTML = html;
    currentQuestionIndex = index;
}

function getLikertValue(option) {
    var map = {
        'Strongly Disagree': '1',
        'Disagree': '2',
        'Neutral': '3',
        'Agree': '4',
        'Strongly Agree': '5'
    };
    return map[option] || '';
}

function selectOption(index, value) {
    // Store the answer
    answers[index] = value;

    // Highlight the selected button
    var btns = document.querySelectorAll('.option-btn');
    btns.forEach(function(b) {
        // Check if this button's data-value matches the selected value
        var btnValue = b.getAttribute('data-value');
        if (btnValue === value) {
            b.classList.add('selected');
        } else {
            b.classList.remove('selected');
        }
    });
}

function nextQuestion(index) {
    if (answers[index] === null || answers[index] === '') {
        alert('Please select an answer before continuing.');
        return;
    }

    if (index === totalQuestions - 1) {
        showComplete();
    } else {
        renderQuestion(index + 1);
    }
}

// ============================================================================
// STEP 3: COMPLETE
// ============================================================================

function showComplete() {
    document.getElementById('surveyScreen').classList.remove('active');
    document.getElementById('completeScreen').classList.add('active');
}