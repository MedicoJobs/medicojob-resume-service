from __future__ import annotations

import random
import uuid

from app.models.interview import (
    ClinicalCaseStudy,
    InterviewQuestion,
    InterviewQuestionRequest,
    InterviewQuestionResponse,
    PracticeExamQuestion,
    PracticeExamRequest,
    PracticeExamResponse,
    ScoringRubricItem,
)


def generate_interview_questions(payload: InterviewQuestionRequest) -> InterviewQuestionResponse:
    position = payload.position.strip()
    role_family = _role_family(position, payload.specialization)
    seniority = (payload.seniority or _seniority_from_position(position)).strip()

    return InterviewQuestionResponse(
        position=position,
        role_family=role_family,
        technical_questions=_technical_questions(position, role_family, seniority),
        scenario_questions=_scenario_questions(position, role_family),
        clinical_case_studies=_clinical_cases(position, role_family),
        behavioral_questions=_behavioral_questions(position, seniority),
        scoring_rubric=_scoring_rubric(role_family, seniority),
        interviewer_tips=[
            "Ask candidates to explain their clinical reasoning before revealing the next case detail.",
            "Score answers against patient safety, guideline awareness, communication, and escalation judgment.",
            "Verify credentials, registrations, and procedural claims after the interview.",
        ],
    )


def generate_practice_exam(payload: PracticeExamRequest) -> PracticeExamResponse:
    position = payload.position.strip()
    role_family = _role_family(position, payload.specialization)
    attempt_id = uuid.uuid4().hex[:12]
    rng = random.SystemRandom()

    bank = _practice_question_bank(position, role_family, payload.difficulty)
    rng.shuffle(bank)
    selected = bank[: payload.question_count]

    return PracticeExamResponse(
        attempt_id=attempt_id,
        position=position,
        role_family=role_family,
        difficulty=payload.difficulty,
        questions=[
            PracticeExamQuestion(id=index + 1, **question)
            for index, question in enumerate(selected)
        ],
    )


def _practice_question_bank(position: str, role_family: str, difficulty: str) -> list[dict]:
    common = [
        {
            "type": "scenario",
            "question": f"You are working as a {position}. A patient suddenly becomes hypotensive and confused. What is your immediate approach?",
            "options": [],
            "correct_answer": None,
            "explanation": "A safe answer should start with ABCDE assessment, call for help, stabilize, check vitals/glucose, establish IV access, and escalate early.",
            "scoring_points": ["ABCDE assessment", "Early escalation", "Initial stabilization", "Focused differential diagnosis"],
        },
        {
            "type": "behavioral",
            "question": "Describe how you would handle a disagreement with a senior clinician when you believe patient safety is at risk.",
            "options": [],
            "correct_answer": None,
            "explanation": "Strong answers use respectful challenge, evidence, escalation pathways, and documentation without delaying care.",
            "scoring_points": ["Professional communication", "Patient safety priority", "Escalation judgment"],
        },
        {
            "type": "mcq",
            "question": "Which action is usually most appropriate first when a patient is clinically deteriorating?",
            "options": ["Wait for routine rounds", "Start a structured ABCDE assessment", "Document only", "Discharge with advice"],
            "correct_answer": "Start a structured ABCDE assessment",
            "explanation": "ABCDE assessment identifies and treats life-threatening issues in priority order.",
            "scoring_points": ["Recognizes acute deterioration", "Uses structured emergency assessment"],
        },
    ]

    specialty = {
        "Cardiology": [
            {
                "type": "mcq",
                "question": "A patient has crushing chest pain and ST elevation on ECG. What is the highest-priority decision?",
                "options": ["Schedule outpatient echo", "Assess reperfusion pathway immediately", "Start only oral antibiotics", "Reassure and observe"],
                "correct_answer": "Assess reperfusion pathway immediately",
                "explanation": "Suspected STEMI requires rapid reperfusion planning while stabilizing and checking contraindications.",
                "scoring_points": ["ECG interpretation", "Reperfusion urgency", "Contraindication review"],
            },
            {
                "type": "case",
                "question": "Build a management plan for acute decompensated heart failure with hypoxia and borderline blood pressure.",
                "options": [],
                "correct_answer": None,
                "explanation": "Good answers assess congestion/perfusion, oxygen or NIV needs, diuretics, BP tolerance, renal function, electrolytes, and ICU escalation.",
                "scoring_points": ["Volume assessment", "Oxygen strategy", "Diuretic plan", "Monitoring and escalation"],
            },
            {
                "type": "short_answer",
                "question": "What information do you need before starting anticoagulation in atrial fibrillation?",
                "options": [],
                "correct_answer": None,
                "explanation": "Assess stroke risk, bleeding risk, renal/liver function, contraindications, drug interactions, and patient adherence.",
                "scoring_points": ["Risk scoring", "Contraindications", "Renal function", "Shared decision-making"],
            },
        ],
        "Resident Doctor": [
            {
                "type": "short_answer",
                "question": "What should a safe admission note include?",
                "options": [],
                "correct_answer": None,
                "explanation": "It should include presenting complaint, relevant history, examination, differential diagnosis, plan, medications, allergies, and escalation triggers.",
                "scoring_points": ["Structured documentation", "Differential diagnosis", "Clear plan", "Escalation triggers"],
            },
            {
                "type": "case",
                "question": "A febrile patient is tachycardic, hypotensive, and drowsy. How do you assess and manage the first hour?",
                "options": [],
                "correct_answer": None,
                "explanation": "This tests sepsis recognition, cultures, antibiotics, fluids, lactate, urine output, source control, and escalation.",
                "scoring_points": ["Sepsis recognition", "Early antibiotics", "Fluid resuscitation", "Senior escalation"],
            },
        ],
        "Nursing": [
            {
                "type": "mcq",
                "question": "Before giving a high-alert medication, which safety practice is most important?",
                "options": ["Skip documentation", "Independent double-check", "Give it faster", "Ask the family to verify dose"],
                "correct_answer": "Independent double-check",
                "explanation": "High-alert medications require strict verification and monitoring.",
                "scoring_points": ["Medication safety", "Dose verification", "Monitoring"],
            }
        ],
    }
    role_questions = specialty.get(role_family, [
        {
            "type": "case",
            "question": f"A patient relevant to {position} has unclear symptoms and abnormal vitals. How do you avoid missing a serious diagnosis?",
            "options": [],
            "correct_answer": None,
            "explanation": "Use red flags, focused examination, targeted investigations, reassessment, and safety-netting.",
            "scoring_points": ["Red flags", "Focused assessment", "Reassessment", "Safety-netting"],
        }
    ])

    variations = [
        {
            "type": "short_answer",
            "question": f"What are three red flags a {position} must not miss in a {role_family.lower()} patient?",
            "options": [],
            "correct_answer": None,
            "explanation": f"The answer should name role-specific red flags and explain why each changes urgency.",
            "scoring_points": ["Red flag awareness", "Clinical urgency", "Reasoning"],
        },
        {
            "type": "scenario",
            "question": f"During a busy shift, two patients need you at the same time. How do you prioritize as a {position}?",
            "options": [],
            "correct_answer": None,
            "explanation": "Prioritize by acuity, airway/breathing/circulation risk, available team support, and clear delegation.",
            "scoring_points": ["Triage", "Delegation", "Safety-first prioritization"],
        },
    ]
    if difficulty.lower() == "hard":
        variations.append(
            {
                "type": "case",
                "question": f"A {role_family.lower()} patient deteriorates despite initial treatment. What data would make you change your plan?",
                "options": [],
                "correct_answer": None,
                "explanation": "Strong answers use reassessment, trends, response to treatment, complications, and senior/multidisciplinary review.",
                "scoring_points": ["Reassessment", "Trend interpretation", "Plan adjustment", "Escalation"],
            }
        )
    return [*common, *role_questions, *variations]


def _role_family(position: str, specialization: str | None) -> str:
    text = f"{position} {specialization or ''}".lower()
    if "cardio" in text:
        return "Cardiology"
    if "neuro" in text:
        return "Neurology"
    if "nurs" in text:
        return "Nursing"
    if "emergency" in text or "icu" in text or "critical" in text:
        return "Emergency and Critical Care"
    if "pediatric" in text or "paediatric" in text:
        return "Pediatrics"
    if "radiolog" in text:
        return "Radiology"
    if "resident" in text:
        return "Resident Doctor"
    return "General Medicine"


def _seniority_from_position(position: str) -> str:
    text = position.lower()
    if any(term in text for term in ("consultant", "head", "lead", "senior")):
        return "Senior"
    if "resident" in text or "junior" in text:
        return "Junior"
    return "Mid-Level"


def _technical_questions(position: str, role_family: str, seniority: str) -> list[InterviewQuestion]:
    specialty_bank = {
        "Cardiology": [
            ("How do you evaluate and risk-stratify a patient presenting with acute chest pain?", "ACS assessment", "Uses ECG timing, troponins, risk scores, hemodynamic status, and reperfusion pathways."),
            ("When would you choose thrombolysis, PCI referral, or conservative management in suspected STEMI/NSTEMI?", "Treatment selection", "Balances guideline indications, contraindications, time windows, and facility capability."),
            ("Explain your approach to long-term management of heart failure with reduced ejection fraction.", "Heart failure care", "Mentions GDMT, titration, device indications, follow-up, renal/electrolyte monitoring, and patient education."),
        ],
        "Nursing": [
            ("How do you prioritize care for multiple unstable patients during a busy shift?", "Clinical prioritization", "Uses ABCs, acuity, escalation, delegation, and documentation."),
            ("What checks do you perform before administering high-alert medication?", "Medication safety", "Mentions five rights, allergies, dilution, double-checks, monitoring, and incident reporting."),
            ("How do you identify early deterioration in a ward patient?", "Patient monitoring", "Uses vitals trends, early warning scores, mental status, urine output, and escalation."),
        ],
        "Resident Doctor": [
            ("How do you structure a new patient clerking from history to management plan?", "Clinical workflow", "Covers history, examination, differential diagnosis, investigations, initial treatment, and escalation."),
            ("Which red flags make you escalate immediately to a senior doctor?", "Escalation judgment", "Identifies airway, shock, sepsis, altered sensorium, acute coronary signs, stroke signs, and severe pain."),
            ("How do you document clinical findings and hand over patients safely?", "Documentation", "Uses concise notes, active problems, pending tests, treatment changes, and clear next actions."),
        ],
    }
    questions = specialty_bank.get(role_family, [
        (f"What are the most important clinical protocols for a {position} in your daily practice?", "Protocol knowledge", "Names relevant protocols and explains how they protect patient safety."),
        ("How do you build a differential diagnosis when the initial presentation is unclear?", "Diagnostic reasoning", "Uses structured differentials, red flags, targeted investigations, and reassessment."),
        ("How do you decide when to refer, admit, observe, or discharge a patient?", "Disposition planning", "Balances risk, diagnosis certainty, patient stability, resources, and follow-up safety."),
    ])
    return [
        InterviewQuestion(question=q, focus=f"{focus} ({seniority})", expected_signal=signal)
        for q, focus, signal in questions
    ]


def _scenario_questions(position: str, role_family: str) -> list[InterviewQuestion]:
    return [
        InterviewQuestion(
            question=f"A patient family is anxious and asking for guarantees before a high-risk decision. How would you communicate as a {position}?",
            focus="Communication under pressure",
            expected_signal="Explains uncertainty clearly, checks understanding, documents consent, and remains empathetic.",
        ),
        InterviewQuestion(
            question="You disagree with a colleague's management plan and believe patient safety may be affected. What do you do?",
            focus="Team escalation",
            expected_signal="Uses respectful challenge, evidence, senior escalation, and patient-safety-first decision making.",
        ),
        InterviewQuestion(
            question=f"The department is overloaded and two urgent {role_family.lower()} patients arrive together. How do you triage?",
            focus="Prioritization",
            expected_signal="Uses acuity, ABCs, available staff, delegation, rapid stabilization, and escalation.",
        ),
    ]


def _clinical_cases(position: str, role_family: str) -> list[ClinicalCaseStudy]:
    if role_family == "Cardiology":
        return [
            ClinicalCaseStudy(
                title="Acute Chest Pain With ST Changes",
                prompt="A 58-year-old diabetic patient arrives with crushing chest pain, diaphoresis, hypotension, and ST elevation in inferior leads. Walk through your first 30 minutes.",
                evaluation_points=["Immediate stabilization and monitoring", "ECG/troponin interpretation", "Reperfusion decision and contraindication checks", "Complication anticipation"],
            ),
            ClinicalCaseStudy(
                title="Decompensated Heart Failure",
                prompt="A patient with known HFrEF presents with severe breathlessness, raised JVP, basal crepitations, and borderline blood pressure. Build the assessment and treatment plan.",
                evaluation_points=["Volume and perfusion assessment", "Oxygen/ventilation strategy", "Diuretic and vasodilator judgment", "Renal/electrolyte monitoring"],
            ),
        ]
    return [
        ClinicalCaseStudy(
            title=f"Unstable Patient For {position}",
            prompt="A patient deteriorates suddenly with tachycardia, low blood pressure, and confusion. Explain your immediate assessment and management.",
            evaluation_points=["ABCDE assessment", "Sepsis/shock recognition", "Initial investigations and treatment", "Timely escalation"],
        ),
        ClinicalCaseStudy(
            title="Diagnostic Uncertainty",
            prompt="A patient has non-specific symptoms, abnormal vitals, and incomplete history. How do you avoid missing a serious diagnosis?",
            evaluation_points=["Red flag screening", "Focused examination", "Safe initial treatment", "Reassessment and safety-netting"],
        ),
    ]


def _behavioral_questions(position: str, seniority: str) -> list[InterviewQuestion]:
    return [
        InterviewQuestion(
            question=f"Tell us about a time you changed your management plan after new clinical evidence appeared.",
            focus="Adaptability",
            expected_signal="Shows humility, reassessment, evidence use, and clear communication.",
        ),
        InterviewQuestion(
            question=f"As a {seniority.lower()} {position}, how do you mentor juniors while maintaining patient flow?",
            focus="Leadership",
            expected_signal="Balances supervision, delegation, teaching moments, and patient safety.",
        ),
        InterviewQuestion(
            question="Describe a difficult patient or family interaction and how you handled it.",
            focus="Empathy and professionalism",
            expected_signal="Uses listening, de-escalation, shared decisions, and documentation.",
        ),
    ]


def _scoring_rubric(role_family: str, seniority: str) -> list[ScoringRubricItem]:
    leadership_weight = 20 if seniority == "Senior" else 15
    return [
        ScoringRubricItem(
            criterion=f"{role_family} clinical knowledge",
            weight=30,
            strong_signal="Accurate, guideline-aware answers with clear clinical reasoning.",
            concern_signal="Vague answers, unsafe omissions, or outdated practice.",
        ),
        ScoringRubricItem(
            criterion="Patient safety and escalation",
            weight=25,
            strong_signal="Recognizes deterioration early and escalates with appropriate urgency.",
            concern_signal="Delays escalation or misses red flags.",
        ),
        ScoringRubricItem(
            criterion="Communication and teamwork",
            weight=20,
            strong_signal="Clear handovers, empathetic patient communication, and respectful team collaboration.",
            concern_signal="Poor documentation, defensive communication, or weak handover structure.",
        ),
        ScoringRubricItem(
            criterion="Leadership and ownership",
            weight=leadership_weight,
            strong_signal="Takes ownership, supervises appropriately, and improves department workflow.",
            concern_signal="Avoids accountability or cannot prioritize under pressure.",
        ),
        ScoringRubricItem(
            criterion="Culture and compliance fit",
            weight=100 - (30 + 25 + 20 + leadership_weight),
            strong_signal="Understands ethics, consent, confidentiality, and hospital protocols.",
            concern_signal="Weak awareness of compliance, consent, or professional boundaries.",
        ),
    ]
