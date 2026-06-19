from __future__ import annotations

import random
import uuid

from app.models.interview import PracticeExamQuestion, PracticeExamRequest, PracticeExamResponse
from app.services.interview_question_agent import _role_family


def generate_applicant_mcq_exam(payload: PracticeExamRequest) -> PracticeExamResponse:
    rng = random.SystemRandom()
    position = payload.position.strip()
    role_family = _role_family(position, payload.specialization)
    question_count = payload.question_count
    bank = _build_mcq_bank(position, role_family, payload.difficulty, rng)
    rng.shuffle(bank)

    while len(bank) < question_count:
        bank.extend(_build_mcq_bank(position, role_family, payload.difficulty, rng))
        rng.shuffle(bank)

    return PracticeExamResponse(
        attempt_id=uuid.uuid4().hex[:12],
        position=position,
        role_family=role_family,
        difficulty=payload.difficulty,
        questions=[
            PracticeExamQuestion(id=index + 1, **question)
            for index, question in enumerate(bank[:question_count])
        ],
    )


def _build_mcq_bank(position: str, role_family: str, difficulty: str, rng: random.SystemRandom) -> list[dict]:
    common = _common_mcqs(position, rng)
    specialty = {
        "Cardiology": _cardiology_mcqs(rng),
        "Resident Doctor": _resident_mcqs(rng),
        "Nursing": _nursing_mcqs(rng),
        "Emergency and Critical Care": _emergency_mcqs(rng),
        "Pediatrics": _pediatric_mcqs(rng),
    }.get(role_family, _general_medicine_mcqs(position, rng))

    if difficulty.lower() == "hard":
        specialty.extend(_hard_mcqs(role_family, rng))
    return [*common, *specialty]


def _mcq(question: str, correct: str, distractors: list[str], explanation: str, scoring_points: list[str]) -> dict:
    options = [correct, *distractors]
    random.SystemRandom().shuffle(options)
    return {
        "type": "mcq",
        "question": question,
        "options": options,
        "correct_answer": correct,
        "explanation": explanation,
        "scoring_points": scoring_points,
    }


def _common_mcqs(position: str, rng: random.SystemRandom) -> list[dict]:
    patient_age = rng.choice([28, 42, 56, 67, 74])
    setting = rng.choice(["ward", "OPD", "emergency bay", "post-operative unit"])
    return [
        _mcq(
            f"As a {position}, a {patient_age}-year-old patient in the {setting} becomes drowsy with low blood pressure. What is the safest first action?",
            "Start an ABCDE assessment and call for help",
            ["Wait for the next routine round", "Discharge the patient with advice", "Document only and reassess tomorrow"],
            "Acute deterioration needs structured assessment, immediate stabilization, and escalation.",
            ["ABCDE", "Escalation", "Patient safety"],
        ),
        _mcq(
            "Which handover format best reduces missed clinical information?",
            "SBAR with active problems and pending actions",
            ["Only verbal summary from memory", "A list of medications only", "Asking the patient to explain the plan"],
            "SBAR creates a structured handover with situation, background, assessment, and recommendation.",
            ["Structured communication", "Handover safety"],
        ),
        _mcq(
            "A medication dose looks unusually high. What should you do before administration?",
            "Pause and verify the order with prescription, patient factors, and a senior/pharmacist if needed",
            ["Give it because it is already prescribed", "Ask the family if the dose seems correct", "Skip all documentation"],
            "Medication safety requires verification before giving a potentially harmful dose.",
            ["Medication safety", "Verification", "Documentation"],
        ),
    ]


def _cardiology_mcqs(rng: random.SystemRandom) -> list[dict]:
    lead_group = rng.choice(["inferior leads", "anterior leads", "lateral leads"])
    chest_pain_duration = rng.choice([30, 45, 90, 120])
    return [
        _mcq(
            f"A patient has crushing chest pain for {chest_pain_duration} minutes with ST elevation in {lead_group}. What is the priority?",
            "Activate reperfusion pathway while stabilizing the patient",
            ["Schedule routine outpatient echo", "Observe without repeat ECG", "Treat as gastritis first"],
            "ST elevation with ischemic symptoms is time-critical and needs reperfusion planning.",
            ["STEMI recognition", "Reperfusion", "Emergency stabilization"],
        ),
        _mcq(
            "Which finding most strongly suggests acute decompensated heart failure?",
            "Raised JVP with pulmonary crackles and hypoxia",
            ["Isolated mild headache", "Normal oxygen saturation with clear lungs", "Localized ankle sprain"],
            "Congestion signs with hypoxia support decompensated heart failure.",
            ["Heart failure recognition", "Clinical examination"],
        ),
        _mcq(
            "Before starting anticoagulation for atrial fibrillation, which factor is essential to check?",
            "Stroke risk, bleeding risk, renal function, and contraindications",
            ["Only the patient's preferred meal time", "Hair color and height", "Whether the patient owns a smartwatch"],
            "Anticoagulation choice depends on risk-benefit and renal/bleeding considerations.",
            ["Atrial fibrillation", "Risk assessment", "Contraindications"],
        ),
    ]


def _resident_mcqs(rng: random.SystemRandom) -> list[dict]:
    symptom = rng.choice(["fever and hypotension", "acute breathlessness", "new confusion", "severe abdominal pain"])
    return [
        _mcq(
            f"A new admission has {symptom}. What should your first note and plan emphasize?",
            "Focused assessment, differentials, initial treatment, investigations, and escalation triggers",
            ["Only the final diagnosis", "Only demographic details", "A delayed plan after discharge"],
            "A safe admission plan must show reasoning, immediate actions, and when to escalate.",
            ["Admission workflow", "Clinical reasoning", "Escalation"],
        ),
        _mcq(
            "Which patient should be escalated most urgently to a senior doctor?",
            "A patient with hypotension, altered sensorium, and rising respiratory rate",
            ["A stable patient requesting a routine certificate", "A patient asking about diet advice", "A patient waiting for elective follow-up"],
            "Shock or altered sensorium can indicate life-threatening deterioration.",
            ["Red flags", "Escalation judgment"],
        ),
        _mcq(
            "What is the best way to document a pending critical test result during handover?",
            "Mention the test, why it matters, expected time, and action needed for abnormal results",
            ["Leave it out if the result is not ready", "Tell only the patient", "Write 'follow up' without details"],
            "Pending investigations need clear ownership and action thresholds.",
            ["Documentation", "Handover", "Accountability"],
        ),
    ]


def _nursing_mcqs(rng: random.SystemRandom) -> list[dict]:
    medication = rng.choice(["insulin", "heparin", "potassium chloride", "opioid analgesia"])
    return [
        _mcq(
            f"Before administering {medication}, what is the safest practice?",
            "Verify rights of medication and use required independent double-checks",
            ["Administer quickly without checking", "Ask another patient", "Skip monitoring"],
            "High-risk medication administration requires verification and monitoring.",
            ["Medication safety", "Double-check", "Monitoring"],
        ),
        _mcq(
            "Which change is an early warning sign of deterioration?",
            "Increasing respiratory rate with falling oxygen saturation",
            ["Improved appetite", "Stable vitals", "Resolved pain"],
            "Respiratory rate and oxygenation changes often precede major deterioration.",
            ["Early warning signs", "Patient monitoring"],
        ),
    ]


def _emergency_mcqs(rng: random.SystemRandom) -> list[dict]:
    return [
        _mcq(
            "In suspected sepsis with hypotension, which action should not be delayed?",
            "Early antibiotics, cultures, fluids, lactate, and escalation",
            ["Waiting for fever to resolve naturally", "Only giving oral vitamins", "Routine appointment after a week"],
            "Sepsis is time-sensitive and needs bundled early care.",
            ["Sepsis", "Shock", "Emergency care"],
        ),
        _mcq(
            "What is the priority in an unconscious patient?",
            "Airway protection and immediate ABC assessment",
            ["Detailed family history first", "Routine discharge", "Outpatient physiotherapy"],
            "Airway and breathing are immediate priorities in unconscious patients.",
            ["Airway", "Emergency assessment"],
        ),
    ]


def _pediatric_mcqs(rng: random.SystemRandom) -> list[dict]:
    return [
        _mcq(
            "A child is lethargic with poor perfusion and persistent vomiting. What is the safest first approach?",
            "Assess ABC, hydration/shock status, glucose, and escalate urgently",
            ["Send home without observation", "Wait for routine vaccination visit", "Ignore perfusion signs"],
            "Children can deteriorate quickly; perfusion, glucose, and hydration must be assessed early.",
            ["Pediatric red flags", "Shock recognition"],
        )
    ]


def _general_medicine_mcqs(position: str, rng: random.SystemRandom) -> list[dict]:
    diagnosis = rng.choice(["pneumonia", "DKA", "stroke", "upper GI bleed"])
    return [
        _mcq(
            f"A patient may have {diagnosis}, but the presentation is incomplete. What is the safest diagnostic approach?",
            "Identify red flags, stabilize, order targeted tests, reassess, and escalate if unstable",
            ["Wait until all symptoms become classic", "Avoid examination", "Discharge without safety-netting"],
            "Unclear presentations require structured risk assessment and reassessment.",
            ["Differential diagnosis", "Red flags", "Reassessment"],
        )
    ]


def _hard_mcqs(role_family: str, rng: random.SystemRandom) -> list[dict]:
    return [
        _mcq(
            f"In a complex {role_family.lower()} case, initial treatment is not working. What is the best next step?",
            "Reassess diagnosis, review response trends, check complications, and escalate",
            ["Repeat the same plan indefinitely", "Stop monitoring", "Ignore new abnormal findings"],
            "Failure to improve should trigger reassessment and senior/multidisciplinary input.",
            ["Reassessment", "Trend interpretation", "Escalation"],
        )
    ]
