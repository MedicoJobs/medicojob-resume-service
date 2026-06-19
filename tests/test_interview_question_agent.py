from app.models.interview import InterviewQuestionRequest, PracticeExamRequest
from app.services.applicant_exam_agent import generate_applicant_mcq_exam
from app.services.interview_question_agent import generate_interview_questions, generate_practice_exam


def test_generate_consultant_cardiologist_interview_kit():
    result = generate_interview_questions(InterviewQuestionRequest(position="Consultant Cardiologist"))

    assert result.role_family == "Cardiology"
    assert result.position == "Consultant Cardiologist"
    assert len(result.technical_questions) >= 3
    assert len(result.scenario_questions) >= 3
    assert len(result.clinical_case_studies) >= 2
    assert len(result.behavioral_questions) >= 3
    assert sum(item.weight for item in result.scoring_rubric) == 100
    assert any("chest pain" in item.question.lower() for item in result.technical_questions)


def test_generate_applicant_practice_exam_creates_new_attempts():
    payload = PracticeExamRequest(position="Resident Doctor", question_count=5)

    first = generate_practice_exam(payload)
    second = generate_practice_exam(payload)

    assert first.attempt_id != second.attempt_id
    assert first.role_family == "Resident Doctor"
    assert len(first.questions) == 5
    assert all(question.explanation for question in first.questions)


def test_generate_applicant_mcq_exam_returns_new_mcq_attempts():
    payload = PracticeExamRequest(position="Resident Doctor", question_count=10)

    first = generate_applicant_mcq_exam(payload)
    second = generate_applicant_mcq_exam(payload)

    assert first.attempt_id != second.attempt_id
    assert len(first.questions) == 10
    assert all(question.type == "mcq" for question in first.questions)
    assert all(len(question.options) == 4 for question in first.questions)
    assert all(question.correct_answer in question.options for question in first.questions)
