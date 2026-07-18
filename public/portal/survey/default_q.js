/**
 * FOLDER/FILE PATH: public/survey/default_q.js
 * VERSION NO: 3.0.0
 * DATE: 2026-07-17
 * PURPOSE OF THE FILE: Defines the frozen master schema contract for all 23 bilingual 
 * SMS survey questions mapped to ICAO Annex 19 safety pillars and CAAN SSP mandates.
 */

export const MASTER_QUESTIONS = [
    // ── PILLAR 1: SAFETY POLICY & OBJECTIVES ──
    { 
        id: "q1_aware", 
        pillar: "Safety Policy & Objectives", 
        type: "binary", 
        text_en: "I am aware of my organisation's Safety Policy Statement.",
        text_ne: "म आफ्नो संस्थाको सुरक्षा नीति बयानबारे जानकार छु।" 
    },
    { 
        id: "q2", 
        pillar: "Safety Policy & Objectives", 
        type: "likert", 
        text_en: "Employees at all levels are regularly informed and reminded about the Safety Policy Statement.",
        text_ne: "सबै तहका कर्मचारीहरूलाई सुरक्षा नीति बयानबारे नियमित रूपमा सूचित र स्मरण गराइन्छ।" 
    },
    { 
        id: "q3", 
        pillar: "Safety Policy & Objectives", 
        type: "likert", 
        text_en: "The Safety Policy Statement clearly demonstrates the organisation's commitment to safety.",
        text_ne: "सुरक्षा नीति बयानले संस्थाको सुरक्षाप्रति प्रतिबद्धता स्पष्ट रूपमा देखाउँछ।" 
    },
    { 
        id: "q4", 
        pillar: "Safety Policy & Objectives", 
        type: "likert", 
        text_en: "The Safety Policy Statement is applicable and relevant to all employees, regardless of their role or level.",
        text_ne: "सुरक्षा नीति बयान सबै कर्मचारीहरूमा, तिनीहरूको भूमिका वा स्तर जुनसुकै भए पनि, लागू र सान्दर्भिक छ।" 
    },
    { 
        id: "q5_spi", 
        pillar: "Safety Policy & Objectives", 
        type: "likert", 
        text_en: "I am aware of our organisation's safety performance targets and how we are tracking against them.",
        text_ne: "म हाम्रो संस्थाका सुरक्षा प्रदर्शन लक्ष्यहरू र हामी ती विरुद्ध कसरी अघि बढिरहेका छौँ भन्नेबारे जानकार छु।" 
    },

    // ── PILLAR 2: SAFETY RISK MANAGEMENT ──
    { 
        id: "q6", 
        pillar: "Safety Risk Management", 
        type: "likert", 
        text_en: "I believe that our organisation has an effective hazard reporting process.",
        text_ne: "मलाई विश्वास छ कि हाम्रो संस्थामा एक प्रभावकारी खतरा रिपोर्टिङ प्रक्रिया छ।" 
    },
    { 
        id: "q7", 
        pillar: "Safety Risk Management", 
        type: "likert", 
        text_en: "I feel comfortable reporting safety concerns through our hazard reporting process.",
        text_ne: "म हाम्रो खतरा रिपोर्टिङ प्रक्रिया मार्फत सुरक्षा चिन्ताहरू रिपोर्ट गर्न सहज महसुस गर्छु।" 
    },
    { 
        id: "q8", 
        pillar: "Safety Risk Management", 
        type: "likert", 
        text_en: "Our hazard reporting process is easy to use.",
        text_ne: "हाम्रो खतरा रिपोर्टिङ प्रक्रिया प्रयोग गर्न सजिलो छ।" 
    },
    { 
        id: "q9", 
        pillar: "Safety Risk Management", 
        type: "likert", 
        text_en: "Reporting safety issues has clear value for my personal safety and the safety of my colleagues.",
        text_ne: "सुरक्षा समस्याहरू रिपोर्ट गर्नाले मेरो र मेरा सहकर्मीहरूको व्यक्तिगत सुरक्षाका लागि स्पष्ट मूल्य छ।" 
    },
    { 
        id: "q10", 
        pillar: "Safety Risk Management", 
        type: "likert", 
        text_en: "I feel safe to report any safety concern without fear of negative consequences.",
        text_ne: "म नकारात्मक परिणामको डर बिना कुनै पनि सुरक्षा चिन्ता रिपोर्ट गर्न सुरक्षित महसुस गर्छु।" 
    },
    { 
        id: "q11", 
        pillar: "Safety Risk Management", 
        type: "likert", 
        text_en: "When I observe an unsafe act or condition, I report it through the appropriate channel.",
        text_ne: "जब म कुनै असुरक्षित कार्य वा अवस्था देख्छु, म यसलाई उचित च्यानल मार्फत रिपोर्ट गर्छु।" 
    },
    { 
        id: "q12_risk_assess", 
        pillar: "Safety Risk Management", 
        type: "likert", 
        text_en: "I understand how risks are assessed and prioritised after a hazard report is submitted.",
        text_ne: "खतरा रिपोर्ट पेश गरेपछि जोखिमहरू कसरी मूल्याङ्कन र प्राथमिकता दिइन्छ भनी म बुझ्छु।" 
    },
    { 
        id: "q13_action_inform", 
        pillar: "Safety Risk Management", 
        type: "likert", 
        text_en: "I am informed of the actions taken to address hazards I have reported.",
        text_ne: "रिपोर्ट गरिएका खतराहरू सम्बोधन गर्न गरिएका कार्यहरूबारे मलाई सूचित गरिन्छ।" 
    },

    // ── PILLAR 3: SAFETY ASSURANCE ──
    { 
        id: "q14", 
        pillar: "Safety Assurance", 
        type: "likert", 
        text_en: "Management provides good feedback regarding the organisation's safety performance.",
        text_ne: "व्यवस्थापनले संस्थाको सुरक्षा प्रदर्शनबारे राम्रो प्रतिक्रिया दिन्छ।" 
    },
    { 
        id: "q15", 
        pillar: "Safety Assurance", 
        type: "likert", 
        text_en: "Management follows up regarding safety issues that have been reported.",
        text_ne: "व्यवस्थापनले रिपोर्ट गरिएका सुरक्षा समस्याहरूमा फलोअप गर्छ।" 
    },
    { 
        id: "q16", 
        pillar: "Safety Assurance", 
        type: "likert", 
        text_en: "Safety audits and inspections are carried out regularly in my work area.",
        text_ne: "मेरो कार्यक्षेत्रमा नियमित रूपमा सुरक्षा अडिट र निरीक्षणहरू गरिन्छ।" 
    },
    { 
        id: "q19_invest_outcome", 
        pillar: "Safety Assurance", 
        type: "likert", 
        text_en: "I am informed of the outcomes of safety investigations relevant to my work area.",
        text_ne: "मेरो कार्यक्षेत्रसँग सम्बन्धित सुरक्षा अनुसन्धानहरूका नतिजाहरूबारे मलाई सूचित गरिन्छ।" 
    },
    { 
        id: "q20_corrective", 
        pillar: "Safety Assurance", 
        type: "likert", 
        text_en: "Corrective actions arising from safety findings are actually implemented.",
        text_ne: "सुरक्षा निष्कर्षहरूबाट उत्पन्न सुधारात्मक कार्यहरू वास्तवमा कार्यान्वयन भएको मैले देख्छु।" 
    },

    // ── PILLAR 4: SAFETY PROMOTION ──
    { 
        id: "q17", 
        pillar: "Safety Promotion", 
        type: "likert", 
        text_en: "I am given sufficient training to competently and safely perform my duties.",
        text_ne: "मलाई मेरा कर्तव्यहरू सक्षमतापूर्वक र सुरक्षित रूपमा पूरा गर्न पर्याप्त तालिम दिइएको छ।" 
    },
    { 
        id: "q18", 
        pillar: "Safety Promotion", 
        type: "likert", 
        text_en: "I have access to the checklists and procedures needed to complete my duties safely.",
        text_ne: "मेरा कर्तव्यहरू सुरक्षित रूपमा पूरा गर्न आवश्यक चेकलिस्ट र प्रक्रियाहरूमा मेरो पहुँच छ।" 
    },
    { 
        id: "q21", 
        pillar: "Safety Promotion", 
        type: "likert", 
        text_en: "I am kept informed when changes are made that may affect safety in my role.",
        text_ne: "मेरो भूमिकामा सुरक्षालाई असर गर्न सक्ने परिवर्तनहरू गर्दा मलाई सूचित गरिन्छ।" 
    },
    { 
        id: "q22", 
        pillar: "Safety Promotion", 
        type: "likert", 
        text_en: "In the event of an emergency, I know which procedures to follow and who to contact.",
        text_ne: "आपतकालीन अवस्थामा, कुन प्रक्रिया पालना गर्ने र कसलाई सम्पर्क गर्ने भनेर म जान्दछु।" 
    },
    { 
        id: "q23_peer", 
        pillar: "Safety Promotion", 
        type: "likert", 
        text_en: "My colleagues take safety seriously in their day-to-day work.",
        text_ne: "मेरा सहकर्मीहरूले आफ्नो दैनिक कामलाई सुरक्षालाई गम्भीरतापूर्वक लिन्छन्।" 
    }
];

Object.freeze(MASTER_QUESTIONS);