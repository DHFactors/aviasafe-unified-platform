/* ============================================================================
   FILE: default_q.js
   PATH: public/survey/default_q.js
   VERSION: 2.1.0
   DATE CREATED: 2026-07-26
   DATE REVISED: 2026-07-26
   PURPOSE: Safety survey questionnaire - 19 questions.
   AUTHOR: AviaSAFE Systems
   ============================================================================ */

// ============================================================================
// STANDARD LIKERT SCALE (5-point)
// ============================================================================

var LIKERT_5 = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];

// ============================================================================
// SURVEY QUESTIONS
// ============================================================================

window.defaultQuestions = [
    // ============================================================
    // SECTION A: Safety Policy (4 questions)
    // ============================================================
    {
        section: "A. Safety Policy",
        text: "I am aware of my organization's safety policy statement.",
        type: "choice",
        options: ["Aware", "Unaware"]
    },
    {
        section: "A. Safety Policy",
        text: "Employees at all levels are regularly informed and reminded about the Safety Policy Statement.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "A. Safety Policy",
        text: "The safety policy statement clearly demonstrates the company's commitment to safety.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "A. Safety Policy",
        text: "The safety policy statement is applicable and relevant to all employees, regardless of their roles or level.",
        type: "likert",
        options: LIKERT_5
    },

    // ============================================================
    // SECTION B: Hazard Reporting Culture (6 questions)
    // ============================================================
    {
        section: "B. Hazard Reporting Culture",
        text: "I believe that my company has an effective hazard reporting process.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "B. Hazard Reporting Culture",
        text: "I feel comfortable reporting issues with the hazard reporting process.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "B. Hazard Reporting Culture",
        text: "I think our hazard reporting process is very easy to use.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "B. Hazard Reporting Culture",
        text: "I think that reporting issues has obvious value for my safety.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "B. Hazard Reporting Culture",
        text: "I never feel pressure to NOT report some types of issues.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "B. Hazard Reporting Culture",
        text: "I always report any dangerous work practice I see.",
        type: "likert",
        options: LIKERT_5
    },

    // ============================================================
    // SECTION C: Safety Guidance from SMS (6 questions)
    // ============================================================
    {
        section: "C. Safety Guidance from SMS",
        text: "I feel that I am given enough training to easily complete my tasks.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "C. Safety Guidance from SMS",
        text: "I have checklists that I use to complete routine tasks.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "C. Safety Guidance from SMS",
        text: "I have procedures that I can consult if I don't know how to complete a duty.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "C. Safety Guidance from SMS",
        text: "I think that I am kept informed when changes are made which may affect safety.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "C. Safety Guidance from SMS",
        text: "In case of an emergency, I can use an emergency response document to follow for what to do and who to contact.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "C. Safety Guidance from SMS",
        text: "I feel management does a good job following up with me regarding issues I have reported.",
        type: "likert",
        options: LIKERT_5
    },

    // ============================================================
    // SECTION D: How Employees Feel About the SMS (3 questions)
    // ============================================================
    {
        section: "D. Employee Feelings About SMS",
        text: "I feel that I was adequately trained on the purpose and goals of our SMS.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "D. Employee Feelings About SMS",
        text: "Safety audits/inspections are carried out regularly.",
        type: "likert",
        options: LIKERT_5
    },
    {
        section: "D. Employee Feelings About SMS",
        text: "Is there anything further you would like to add?",
        type: "textarea",
        isOpenEnded: true
    }
];

console.log("Survey questions loaded:", window.defaultQuestions.length, "questions");