from app.models.application import Application, ApplicationAnswer, GeneratedDocument, Job, ModelUsage


def test_model_creation() -> None:
    job = Job(description_text="Python role", description_hash="abc")
    application = Application(job_id=1, folder_path="storage/applications/example")
    document = GeneratedDocument(application_id=1, document_type="cv_tex", path="cv.tex")
    answer = ApplicationAnswer(
        application_id=1,
        question="Why this role?",
        question_type="why_this_role",
        generated_answer="Because it matches approved skills.",
    )
    usage = ModelUsage(provider="local", model="local-rules", prompt_name="test")
    assert job.status == "found"
    assert application.status == "found"
    assert document.path == "cv.tex"
    assert answer.requires_manual_review is True
    assert usage.success is False
