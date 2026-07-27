var currentQuestionIndex = 0;
var answers = [];
var questions = [];
var totalQuestions = 0;
var respondentInfo = {};
var surveyConfig = null;
var tenantName = '';

// ============================================================================
// TENANT DETECTION
// ============================================================================

function getTenantFromSubdomain() {
    var hostname = window.location.hostname;
    var parts = hostname.split('.');
    if (parts.length >= 2 && parts[1] === 'aviasafesystems') {
        return parts[0];
    }
    return null;
}

function getTenantFromUrl() {
    var params = new URLSearchParams(window.location.search);
    return params.get('tenant') || null;
}

function getCurrentTenant() {
    return getTenantFromSubdomain() || getTenantFromUrl();
}

// ============================================================================
// SURVEY PERIOD
// ============================================================================

function getDaysRemaining(closeDate) {
    var now = new Date();
    var close = new Date(closeDate);
    var diff = close - now;
    if (diff <= 0) return 0;
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function isSurveyOpen(config) {
    if (!config) return true;
    var now = new Date();
    if (config.openDate) {
        var open = new Date(config.openDate);
        if (now < open) return false;
    }
    if (config.closeDate) {
        var close = new Date(config.closeDate);
        if (now > close) return false;
    }
    return true;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    var d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ============================================================================
// INIT
// ============================================================================

document.addEventListener('DOMContentLoaded', async function() {
    await loadSurveyContext();
});

async function loadSurveyContext() {
    var tenantId = getCurrentTenant();
    if (!tenantId) {
        document.getElementById('surveyTitle').textContent = 'Safety Survey';
        return;
    }

    try {
        var tenantDoc = await firebase.firestore().collection('tenants').doc(tenantId).get();
        if (!tenantDoc.exists) return;

        var data = tenantDoc.data();
        tenantName = data.name || tenantId.replace(/-/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); });
        surveyConfig = data.surveyConfig || data.survey || null;

        // Show tenant badge
        var badge = document.getElementById('tenantBadge');
        badge.textContent = tenantName;
        badge.style.display = 'inline-block';

        // Update survey title
        document.getElementById('surveyTitle').textContent = tenantName + ' — Safety Survey';

        // Show survey period
        if (surveyConfig && (surveyConfig.openDate || surveyConfig.closeDate)) {
            var periodInfo = document.getElementById('surveyPeriodInfo');
            var parts = [];
            if (surveyConfig.openDate) parts.push('Opens: ' + formatDate(surveyConfig.openDate));
            if (surveyConfig.closeDate) parts.push('Closes: ' + formatDate(surveyConfig.closeDate));
            periodInfo.textContent = parts.join('  ·  ');
            periodInfo.style.display = 'block';

            var daysEl = document.getElementById('daysRemaining');
            if (surveyConfig.closeDate) {
                var days = getDaysRemaining(surveyConfig.closeDate);
                if (days > 0) {
                    daysEl.textContent = days + ' day' + (days !== 1 ? 's' : '') + ' remaining to complete the survey';
                    daysEl.style.display = 'block';
                } else {
                    daysEl.textContent = 'Survey is closed';
                    daysEl.style.color = '#ea4335';
                    daysEl.style.display = 'block';
                }
            }

            // Status bar for closed survey
            if (!isSurveyOpen(surveyConfig)) {
                var statusBar = document.getElementById('surveyStatusBar');
                var statusMsg = document.getElementById('statusMessage');
                statusBar.style.display = 'block';
                statusBar.style.background = '#fce8e6';
                statusBar.style.color = '#ea4335';
                statusMsg.innerHTML = '<i class="fas fa-clock"></i> This survey is currently closed. It will reopen on ' + formatDate(surveyConfig.openDate) + '.';
            }
        }
    } catch (e) {
        console.warn('Could not load tenant context:', e);
    }
}

// ============================================================================
// STEP 1: INFO SCREEN
// ============================================================================

function skipInfo() {
    startSurvey();
}

function startSurvey() {
    if (surveyConfig && !isSurveyOpen(surveyConfig)) {
        alert('This survey is currently closed. Please check back during the open period.');
        return;
    }

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
    answers[index] = value;

    var btns = document.querySelectorAll('.option-btn');
    btns.forEach(function(b) {
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
        submitSurvey();
    } else {
        renderQuestion(index + 1);
    }
}

// ============================================================================
// STEP 3: SUBMIT
// ============================================================================

async function submitSurvey() {
    if (surveyConfig && !isSurveyOpen(surveyConfig)) {
        alert('This survey is closed. Responses cannot be submitted at this time.');
        return;
    }

    var tenantId = getCurrentTenant();

    var responseData = {
        answers: answers,
        respondentInfo: respondentInfo,
        tenantId: tenantId || null,
        submittedAt: new Date().toISOString(),
        surveyVersion: '3.0.0'
    };

    try {
        if (tenantId) {
            await firebase.firestore().collection('tenants').doc(tenantId).collection('responses').add(responseData);
        } else {
            await firebase.firestore().collection('surveyResponses').add(responseData);
        }
        showComplete();
    } catch (e) {
        console.error('Submit error:', e);
        alert('Could not save your response. Please try again.');
    }
}

// ============================================================================
// STEP 4: COMPLETE
// ============================================================================

function showComplete() {
    document.getElementById('surveyScreen').classList.remove('active');
    document.getElementById('completeScreen').classList.add('active');
}
