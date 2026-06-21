# Codex TODO — Agentic Job Application Manager

This Markdown file is intended to be given to Codex as the implementation checklist for building the app.

The project is an **AI-assisted job application manager**, not an unattended mass-application bot. It should help prepare, tailor, organize, and supervise applications while keeping the user in control.

---

## Project Principle

### Goal

Build a local app/script that helps the user manage job applications end-to-end:

- Parse jobs.
- Score job fit.
- Tailor a LaTeX CV.
- Generate cover letters/SOPs.
- Generate answers to application questions.
- Follow LinkedIn/Indeed redirections to external ATS/company websites.
- Fill safe fields in supervised browser-assist mode.
- Stop before final submission.
- Save every application package in organized daily folders.
- Provide an interface/dashboard so the user can see progress.

### Why this is being done

The user wants a unique agentic application manager, not just a bot that sends the same CV everywhere. The value of the app is personalization, traceability, review, and follow-up management.

### Non-negotiable safety and compliance rules

[x] Do not build an unattended mass-application bot.

[x] Do not bypass CAPTCHA.

[x] Do not evade rate limits.

[x] Do not scrape LinkedIn/Indeed at scale.

[x] Do not auto-submit applications.

[x] Do not fabricate skills, work experience, education, dates, projects, salary, work authorization, or visa status.

[x] Do not answer sensitive questions without user-approved data.

[x] Always show a review screen before filling sensitive fields.

[x] Always stop before final submission.

[x] The user must manually confirm submission.

[x] Store the exact CV, cover letter, answers, screenshots, URLs, and metadata used for each application.

---

## Part 1 — Project Setup

### Goal

Create the basic Python project structure, dependencies, environment files, and development commands.

### Why this is being done

The app needs a clean foundation before adding AI, LaTeX generation, browser assist, storage, or interface features.

### Tasks

[x] Create a Python 3.12+ project.

[x] Use this structure:

```text
job-agent/
  app/
    __init__.py
    main.py
    config.py

    agents/
      __init__.py

    services/
      __init__.py

    models/
      __init__.py

    prompts/

    templates/

  storage/
    applications/
    master_cv/
    profile/
    logs/

  tests/

  scripts/

  .env.example
  pyproject.toml
  README.md
  TODO_CODEX_BUILD.md
```

[x] Add dependencies:

```text
fastapi
uvicorn
typer
rich
pydantic
pydantic-settings
sqlmodel
sqlalchemy
jinja2
playwright
python-dotenv
ollama
openai
httpx
beautifulsoup4
markdown
pytest
pytest-asyncio
```

[x] Add optional dependencies for document/PDF handling:

```text
weasyprint
pypdf
```

[x] Add `pyproject.toml`.

[x] Add `.env.example`.

[x] Add `README.md`.

[x] Add `jobagent` CLI entrypoint.

[x] Add a command:

```bash
jobagent init
```

[x] `jobagent init` should create the storage folders if missing.

[x] Add basic logging to:

```text
storage/logs/app.log
```

---

## Part 2 — Configuration System

### Goal

Create a central settings system for paths, model provider choice, database URL, and browser-assist behavior.

### Why this is being done

The app should be configurable without editing source code. The user should be able to switch between local Ollama models and OpenAI API by changing `.env`.

### Tasks

[x] Create `app/config.py`.

[x] Use `pydantic-settings`.

[x] Support these environment variables:

```env
APP_ENV=development
DATABASE_URL=sqlite:///storage/job_agent.db

MODEL_PROVIDER=ollama

OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b

LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=

STORAGE_DIR=storage
APPLICATIONS_DIR=storage/applications
PROFILE_DIR=storage/profile
MASTER_CV_DIR=storage/master_cv

BROWSER_HEADLESS=false
REQUIRE_MANUAL_SUBMIT=true
```

[x] Validate that required folders exist.

[x] Add helpful error messages if Ollama/OpenAI settings are missing.

[x] Add command:

```bash
jobagent doctor
```

[x] `jobagent doctor` should check:

[x] Python version.

[x] Storage folders.

[x] Database connection.

[x] LaTeX compiler availability.

[x] Ollama availability if selected.

[x] OpenAI API key if selected.

[x] Playwright browser availability.

---

## Part 3 — Data Models and Database

### Goal

Create the database schema for profile, jobs, applications, documents, generated answers, and status tracking.

### Why this is being done

The app needs persistent tracking so the user can see what was prepared, submitted, rejected, followed up, or still pending.

### Tasks

[x] Use SQLModel or SQLAlchemy.

[x] Create `models/job.py`.

[x] Create `models/application.py`.

[x] Create `models/candidate_profile.py`.

[x] Create `models/generated_document.py`.

[x] Create `models/application_answer.py`.

[x] Create `models/model_usage.py`.

[x] Create `models/status.py`.

[x] Add `Job` model fields:

```text
id
company
title
location
remote_type
salary_min
salary_max
currency
source
source_url
final_application_url
ats_platform
description_text
description_html_path
date_found
deadline
status
created_at
updated_at
```

[x] Add `Application` model fields:

```text
id
job_id
application_date
folder_path
status
fit_score
cv_tex_path
cv_pdf_path
cover_letter_path
submitted_at
follow_up_date
notes
created_at
updated_at
```

[x] Add allowed statuses:

```text
found
analyzed
prepared
needs_review
ready_to_apply
browser_assist_started
submitted
follow_up_needed
interview
rejected
offer
archived
```

[x] Add database initialization command:

```bash
jobagent db init
```

[x] Add database migration or reset command for development:

```bash
jobagent db reset
```

[x] Add tests for model creation.

---

## Part 4 — Profile Storage and Required User Files

### Goal

Define exactly where the user should put CV, profile facts, answer bank, links, preferences, and optional documents.

### Why this is being done

The AI should only use approved user facts. Clear profile files prevent hallucinated claims and make the app ready to run.

### Required folder structure

[x] Create this structure:

```text
storage/
  master_cv/
    master_cv.tex
    master_cv.pdf
    assets/
      images/
      icons/
      fonts/

  profile/
    profile.json
    facts.json
    answer_bank.json
    preferences.json
    links.json
    documents.json
    sensitive_answers.json.example
```

### File: `storage/master_cv/master_cv.tex`

[x] Store the main LaTeX CV source here.

[x] This is the source file used for tailoring.

### File: `storage/master_cv/master_cv.pdf`

[x] Store the latest normal PDF version of the CV here.

[x] Use it as a reference and fallback.

### File: `storage/profile/profile.json`

[x] Create profile file:

```json
{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin_url": "",
  "github_url": "",
  "portfolio_url": "",
  "current_title": "Python / Backend Developer",
  "professional_summary": "",
  "education": [],
  "experience": [],
  "projects": [],
  "skills": []
}
```

### File: `storage/profile/facts.json`

[x] Create approved facts file:

```json
{
  "approved_facts": [],
  "blocked_claims": [
    "Do not claim skills that are not in the CV or approved profile.",
    "Do not claim work authorization unless confirmed by the user.",
    "Do not claim years of experience unless explicitly stated.",
    "Do not claim leadership experience unless explicitly confirmed."
  ]
}
```

### File: `storage/profile/answer_bank.json`

[x] Create reusable answer bank:

```json
{
  "why_this_role": {
    "base_answer": "",
    "can_be_tailored": true,
    "requires_manual_confirmation": false
  },
  "why_this_company": {
    "base_answer": "",
    "can_be_tailored": true,
    "requires_manual_confirmation": false
  },
  "tell_us_about_yourself": {
    "base_answer": "",
    "can_be_tailored": true,
    "requires_manual_confirmation": false
  },
  "salary_expectation": {
    "base_answer": "",
    "can_be_tailored": true,
    "requires_manual_confirmation": true
  },
  "notice_period": {
    "base_answer": "",
    "can_be_tailored": false,
    "requires_manual_confirmation": true
  },
  "work_authorisation": {
    "base_answer": "",
    "can_be_tailored": false,
    "requires_manual_confirmation": true
  },
  "visa_sponsorship": {
    "base_answer": "",
    "can_be_tailored": false,
    "requires_manual_confirmation": true
  }
}
```

### File: `storage/profile/preferences.json`

[x] Create preferences file:

```json
{
  "target_roles": [],
  "preferred_locations": [],
  "remote_preference": "",
  "preferred_industries": [],
  "minimum_salary": null,
  "avoid": []
}
```

### File: `storage/profile/links.json`

[x] Create links file:

```json
{
  "linkedin": "",
  "github": "",
  "portfolio": "",
  "personal_website": ""
}
```

### File: `storage/profile/documents.json`

[x] Create documents map:

```json
{
  "master_cv_tex": "storage/master_cv/master_cv.tex",
  "master_cv_pdf": "storage/master_cv/master_cv.pdf",
  "default_cover_letter_template": null,
  "transcript": null,
  "degree_certificate": null,
  "right_to_work_document": null,
  "references": null
}
```

[x] Do not require sensitive documents.

[x] If sensitive documents are configured, require manual approval before use.

[x] Add command:

```bash
jobagent profile validate
```

[x] Add command:

```bash
jobagent profile show
```

[x] Add command:

```bash
jobagent import-cv ./path/to/cv.tex
```

---

## Part 5 — Daily Application Folder System

### Goal

Store applications inside daily parent folders and create a clear package for each application.

### Why this is being done

The user wants done/prepared applications separated by date, making it easier to follow up and audit every application.

### Tasks

[x] Store applications using this structure:

```text
storage/applications/YYYY-MM-DD/company-slug_role-slug_location-slug/
```

[ ] Example:

```text
storage/applications/2026-06-21/software-mind_python-developer_remote/
```

[x] If the folder already exists, add suffixes:

```text
software-mind_python-developer_remote
software-mind_python-developer_remote_002
software-mind_python-developer_remote_003
```

[x] Inside each application folder, create:

```text
00_job-posting/
  job_description.md
  job_description.html
  source_url.txt
  final_application_url.txt
  screenshots/

01_analysis/
  extracted_requirements.json
  fit_score.json
  tailoring_strategy.md
  model_usage.json

02_cv/
  cv_tailored.tex
  cv_tailored.pdf
  cv_diff.md
  compile_log.txt

03_cover-letter/
  cover_letter.md
  cover_letter.pdf

04_application/
  application_answers.generated.json
  application_answers.approved.json
  form_fields_detected.json
  submission_review.md
  submitted_copy.html
  submitted_copy.pdf
  confirmation_screenshot.png

05_follow-up/
  follow_up_email.md
  interview_prep.md
  notes.md

metadata.json
```

[x] Add daily summary file:

```text
storage/applications/YYYY-MM-DD/daily_summary.md
```

[x] Daily summary should include:

[x] Number of jobs added.

[x] Number of applications prepared.

[x] Number of applications submitted.

[x] Company names.

[x] Role names.

[x] Statuses.

[x] Follow-up dates.

[x] Add command:

```bash
jobagent daily-summary
```

[x] Add command:

```bash
jobagent daily-summary 2026-06-21
```

[x] Add command:

```bash
jobagent list --date 2026-06-21
```

---

## Part 6 — Model Provider Layer

### Goal

Support multiple AI backends: Ollama local models, OpenAI API, and optionally LM Studio.

### Why this is being done

Codex is used to build the app. The app itself needs a runtime model backend for generating job analysis, CV edits, cover letters, and application answers.

For an RTX 3050 laptop, default to:

```text
qwen2.5-coder:3b
```

The user can optionally try:

```text
qwen2.5-coder:7b
```

### Tasks

[x] Create:

```text
app/services/model_provider.py
app/services/providers/openai_provider.py
app/services/providers/ollama_provider.py
app/services/providers/lmstudio_provider.py
```

[x] Define interface:

```python
class ModelProvider:
    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        ...

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        ...
```

[x] Add provider factory:

```python
def get_model_provider() -> ModelProvider:
    ...
```

[x] Add Ollama support.

[x] Add OpenAI support.

[x] Add LM Studio-compatible OpenAI API support.

[x] Add structured JSON output where supported.

[x] Add fallback behavior:

[x] If local model fails, show clear error.

[ ] If OpenAI fallback is configured, ask user before using it.

[x] Save model usage to:

```text
01_analysis/model_usage.json
```

[x] Track:

```text
provider
model
prompt_name
input_tokens_if_available
output_tokens_if_available
started_at
finished_at
success
error
```

[x] Add tests for:

[x] Provider factory.

[x] Ollama connection.

[x] OpenAI provider with mocked API.

[x] JSON generation.

[x] Failure handling.

---

## Part 7 — Prompt System

### Goal

Store prompts as versioned Markdown files instead of hardcoding them.

### Why this is being done

Prompts will change often. Keeping them as files makes the app easier to edit and test.

### Tasks

[x] Create:

```text
app/prompts/job_parser.md
app/prompts/fit_score.md
app/prompts/cv_tailor.md
app/prompts/cover_letter.md
app/prompts/application_answers.md
app/prompts/no_fabrication_reviewer.md
app/prompts/interview_prep.md
app/prompts/follow_up_email.md
```

[x] Add prompt loader service.

[x] Track prompt filename and version in generated outputs.

[x] Add tests for prompt loading.

---

## Part 8 — Job Import and Parsing

### Goal

Allow the user to add jobs from pasted text, local files, saved HTML, or URLs.

### Why this is being done

The app needs structured job data before it can tailor the CV or prepare answers.

### Tasks

[ ] Add CLI command:

```bash
jobagent add-job --file ./job.txt
```

[ ] Add CLI command:

```bash
jobagent add-job --url "https://example.com/job"
```

[ ] Add CLI command:

```bash
jobagent add-job --text "..."
```

[ ] Save original job posting into:

```text
00_job-posting/job_description.md
```

[ ] If HTML is available, save:

```text
00_job-posting/job_description.html
```

[ ] Create `JobParserAgent`.

[ ] Extract:

```text
company
title
location
remote_type
salary_range
required_skills
preferred_skills
responsibilities
experience_level
keywords
deadline
red_flags
questions_to_answer
```

[ ] Return strict JSON.

[ ] Save parsed output to:

```text
01_analysis/extracted_requirements.json
```

[ ] Add tests for parsing real job descriptions.

---

## Part 9 — Fit Scoring and Recommendation

### Goal

Score how well the job matches the candidate profile.

### Why this is being done

The user should not waste time applying to poor-fit jobs. The agent should explain why a job is strong, weak, or risky.

### Tasks

[ ] Create `ScoringService`.

[ ] Use a transparent score:

```text
must_have_skill_match: 45%
preferred_skill_match: 20%
experience_match: 15%
domain_match: 10%
location_remote_match: 5%
salary_match: 5%
```

[ ] Save result to:

```text
01_analysis/fit_score.json
```

[ ] Include:

```text
fit_score
must_have_matches
preferred_matches
missing_requirements
risk_flags
recommended_pitch
apply_recommendation
```

[ ] Add recommendation categories:

```text
strong_apply
apply_with_tailoring
maybe
low_priority
avoid
```

[ ] Add command:

```bash
jobagent analyze JOB_ID
```

---

## Part 10 — LaTeX CV Tailoring

### Goal

Tailor the user’s LaTeX CV for each job while preserving truthfulness and LaTeX validity.

### Why this is being done

A tailored CV has better relevance, but the app must not invent skills or break the LaTeX file.

### Tasks

[ ] Create `CVTailorAgent`.

[ ] Create `LatexService`.

[ ] Read from:

```text
storage/master_cv/master_cv.tex
```

[ ] Generate a tailoring strategy before editing.

[ ] Save strategy to:

```text
01_analysis/tailoring_strategy.md
```

[ ] Allowed edits:

[ ] Rewrite professional summary truthfully.

[ ] Reorder skills.

[ ] Reorder bullets.

[ ] Emphasize existing relevant experience.

[ ] Shorten irrelevant content.

[ ] Add keywords only if supported by approved facts.

[ ] Forbidden edits:

[ ] Invent companies.

[ ] Invent projects.

[ ] Invent years of experience.

[ ] Invent tools.

[ ] Invent education.

[ ] Invent work authorization.

[ ] Output tailored LaTeX to:

```text
02_cv/cv_tailored.tex
```

[ ] Compile PDF to:

```text
02_cv/cv_tailored.pdf
```

[ ] Save LaTeX compile log to:

```text
02_cv/compile_log.txt
```

[ ] If compilation fails, attempt safe syntax repair.

[ ] Save human-readable diff to:

```text
02_cv/cv_diff.md
```

[ ] Add command:

```bash
jobagent tailor JOB_ID
```

[ ] Add tests:

[ ] Valid LaTeX output.

[ ] No unsupported claims.

[ ] PDF created.

[ ] CV diff created.

---

## Part 11 — Cover Letter and SOP Generator

### Goal

Generate a tailored cover letter or statement of purpose when required.

### Why this is being done

Many applications ask for a cover letter/SOP. The agent should create one using the job post and approved profile facts.

### Tasks

[ ] Create `CoverLetterAgent`.

[ ] Inputs:

```text
job description
parsed requirements
candidate profile
approved facts
fit score
tailored CV summary
```

[ ] Generate concise cover letter.

[ ] Default length: 250–400 words.

[ ] Make the tone professional, clear, and human.

[ ] Do not copy the CV line by line.

[ ] Do not invent company-specific facts unless present in job description or approved source.

[ ] Save Markdown to:

```text
03_cover-letter/cover_letter.md
```

[ ] Optionally render PDF to:

```text
03_cover-letter/cover_letter.pdf
```

[ ] Add command:

```bash
jobagent cover-letter JOB_ID
```

---

## Part 12 — Dynamic Application Answer Generator

### Goal

Automatically generate answers for application questions such as:

- Why this role?
- Why this company?
- Tell us about yourself.
- Salary expectations.
- Notice period.
- Work authorization.
- Visa sponsorship.
- Are you willing to relocate?
- Why should we hire you?
- Describe your experience with Python/Django/PostgreSQL/Redis.
- Portfolio/GitHub/LinkedIn links.

### Why this is being done

Job applications often include repeated questions. The agent should answer them consistently, truthfully, and tailored to the role.

### Tasks

[ ] Create `ApplicationAnswerAgent`.

[ ] Create `QuestionClassifier`.

[ ] Classify questions into types:

```text
why_this_role
why_this_company
tell_us_about_yourself
salary_expectation
notice_period
work_authorisation
visa_sponsorship
relocation
experience_question
technical_stack_question
availability
portfolio_link
unknown
```

[ ] Read reusable base answers from:

```text
storage/profile/answer_bank.json
```

[ ] Read approved facts from:

```text
storage/profile/facts.json
```

[ ] Generate tailored answer using:

```text
question text
job description
company
role
candidate profile
approved facts
answer bank
```

[ ] Return structured JSON:

```json
{
  "question": "",
  "question_type": "",
  "generated_answer": "",
  "source_facts_used": [],
  "requires_manual_review": true,
  "sensitive": false,
  "unsupported_claims": [],
  "confidence": 0.0
}
```

[ ] Mark these as sensitive:

```text
work_authorisation
visa_sponsorship
salary_expectation
notice_period
relocation
criminal_history
disability
gender
ethnicity
references
```

[ ] Save generated answers to:

```text
04_application/application_answers.generated.json
```

[ ] Create approval workflow.

[ ] Approved answers should be saved to:

```text
04_application/application_answers.approved.json
```

[ ] The browser-assist service may only fill answers from the approved file.

[ ] Add command:

```bash
jobagent answers JOB_ID
```

[ ] Add command:

```bash
jobagent approve-answers JOB_ID
```

[ ] Add tests:

[ ] "Why this role" answer uses role requirements.

[ ] "Why this company" answer uses company/job context only.

[ ] "Tell us about yourself" answer uses profile facts.

[ ] Sensitive answers require manual approval.

[ ] Unsupported claims are detected.

---

## Part 13 — No-Fabrication Reviewer

### Goal

Review generated CVs, cover letters, and answers for unsupported claims.

### Why this is being done

The agent must never lie on behalf of the user.

### Tasks

[ ] Create `NoFabricationReviewer`.

[ ] Inputs:

```text
generated text
master CV
profile.json
facts.json
blocked_claims
job description
```

[ ] Output:

```json
{
  "approved": false,
  "unsupported_claims": [],
  "risky_phrases": [],
  "required_fixes": [],
  "safe_to_use": false
}
```

[ ] Run reviewer after:

[ ] CV tailoring.

[ ] Cover letter generation.

[ ] Application answer generation.

[ ] Submission review.

[ ] If unsupported claims are found, block approval.

[ ] Save reviewer output to relevant folders.

[ ] Add tests for hallucinated skills and work authorization claims.

---

## Part 14 — Prepare Full Application Package

### Goal

Run the full preparation pipeline for one job.

### Why this is being done

The user should be able to run one command and get a complete reviewed application package.

### Tasks

[ ] Add command:

```bash
jobagent prepare JOB_ID
```

[ ] `prepare` should run:

[ ] Job parsing.

[ ] Fit scoring.

[ ] Application folder creation.

[ ] CV tailoring.

[ ] LaTeX PDF compilation.

[ ] Cover letter generation.

[ ] Dynamic application answer generation.

[ ] No-fabrication review.

[ ] Metadata save.

[ ] Final package summary.

[ ] Final output should show:

```text
Company
Role
Fit score
Recommendation
Folder path
Tailored CV path
Cover letter path
Answers path
Risks
Next command
```

---

## Part 15 — LinkedIn/Indeed Redirection and ATS Detection

### Goal

When a job starts on LinkedIn or Indeed but redirects to an external company/ATS website, follow the redirect in supervised mode and continue filling the destination application.

### Why this is being done

Many jobs on LinkedIn and Indeed send the user to external platforms such as Greenhouse, Lever, Workday, Ashby, SmartRecruiters, Teamtailor, Workable, Recruitee, BambooHR, or custom company career pages.

### Tasks

[ ] Create `BrowserService`.

[ ] Create `ATSDetectorService`.

[ ] Use Playwright in non-headless mode by default.

[ ] Add command:

```bash
jobagent apply-assist JOB_ID
```

[ ] Start from `source_url`.

[ ] Detect Apply button when possible.

[ ] Handle user login manually.

[ ] If redirected, save final URL to:

```text
00_job-posting/final_application_url.txt
```

[ ] Store both URLs in metadata:

```json
{
  "source_url": "",
  "final_application_url": "",
  "ats_platform": ""
}
```

[ ] Save screenshots:

```text
00_job-posting/screenshots/source_page.png
00_job-posting/screenshots/destination_page.png
```

[ ] Detect ATS platform by URL and page patterns:

```text
greenhouse
lever
workday
ashby
smartrecruiters
teamtailor
workable
recruitee
bamboohr
unknown_custom
```

[ ] Show redirection review:

```text
Original source:
Destination:
Detected platform:
Continue with supervised browser assist? yes/no
```

[ ] Never bypass login.

[ ] Never bypass CAPTCHA.

[ ] Never bypass rate limits.

[ ] Never submit automatically.

[ ] Add tests for redirect handling.

---

## Part 16 — Form Field Detection and Safe Filling

### Goal

Detect application form fields and fill safe fields only after the user approves.

### Why this is being done

The app should reduce repetitive typing while keeping the user in control of sensitive information.

### Tasks

[ ] Create `FormFieldDetector`.

[ ] Detect:

```text
input
textarea
select
radio
checkbox
file upload
```

[ ] Extract labels.

[ ] Infer field purpose.

[ ] Save detected fields to:

```text
04_application/form_fields_detected.json
```

[ ] Safe fields:

```text
name
email
phone
location
linkedin
github
portfolio
resume upload
cover letter upload
non-sensitive text answer from approved answers
```

[ ] Sensitive fields requiring review:

```text
salary
notice period
work authorization
visa sponsorship
relocation
gender
ethnicity
disability
criminal history
references
```

[ ] Never auto-fill:

```text
captcha
technical assessments
coding tests
personality assessments
multi-choice tests where answer depends on judgement
```

[ ] Fill only from:

```text
04_application/application_answers.approved.json
```

[ ] Upload tailored CV from:

```text
02_cv/cv_tailored.pdf
```

[ ] Upload cover letter from:

```text
03_cover-letter/cover_letter.pdf
```

[ ] Stop before final submit.

[ ] Display:

```text
Review the application in the browser.
Submit manually when ready.
After submitting, return here and confirm.
```

[ ] After user confirms submission, save:

```text
04_application/confirmation_screenshot.png
04_application/submitted_copy.html
04_application/submitted_copy.pdf
```

[ ] Mark status as:

```text
submitted
```

---

## Part 17 — Application Tracker and Follow-Up System

### Goal

Track every application status and generate follow-up material.

### Why this is being done

The user needs to know what was sent, when, and when to follow up.

### Tasks

[ ] Add command:

```bash
jobagent list
```

[ ] Add filters:

```bash
jobagent list --status prepared
jobagent list --status submitted
jobagent list --date 2026-06-21
jobagent list --company "Company Name"
```

[ ] Add command:

```bash
jobagent status JOB_ID submitted
```

[ ] Add command:

```bash
jobagent notes JOB_ID
```

[ ] Add follow-up date calculation:

```text
submitted_at + 5 business days
```

[ ] Generate follow-up email to:

```text
05_follow-up/follow_up_email.md
```

[ ] Add command:

```bash
jobagent followups
```

[ ] Add command:

```bash
jobagent follow-up-email JOB_ID
```

---

## Part 18 — Interview Prep Pack

### Goal

Generate interview preparation notes for each submitted or interview-stage application.

### Why this is being done

Each application package should become an interview prep asset.

### Tasks

[ ] Create `InterviewPrepAgent`.

[ ] Generate:

```text
company summary from job description
role requirements
candidate matching strengths
weak spots to prepare
likely technical questions
likely behavioral questions
projects to discuss
questions to ask recruiter
salary discussion notes
```

[ ] Save to:

```text
05_follow-up/interview_prep.md
```

[ ] Add command:

```bash
jobagent interview-prep JOB_ID
```

---

## Part 19 — Audit Log and Metadata

### Goal

Make every generated artifact traceable.

### Why this is being done

The user should be able to audit what was generated, what was approved, and what was submitted.

### Tasks

[ ] Create `metadata.json` in each application folder.

[ ] Include:

```json
{
  "application_id": null,
  "job_id": null,
  "company": "",
  "title": "",
  "location": "",
  "source": "",
  "source_url": "",
  "final_application_url": "",
  "ats_platform": "",
  "application_date": "",
  "status": "",
  "fit_score": null,
  "documents": {
    "cv_tex": "",
    "cv_pdf": "",
    "cover_letter_md": "",
    "cover_letter_pdf": "",
    "answers_generated": "",
    "answers_approved": ""
  },
  "manual_review_required": true,
  "submitted": false,
  "submitted_at": null,
  "follow_up_date": null
}
```

[ ] Add an audit log file:

```text
audit_log.md
```

[ ] Log:

[ ] Job added.

[ ] CV generated.

[ ] Cover letter generated.

[ ] Answers generated.

[ ] Answers approved.

[ ] Browser-assist started.

[ ] Redirect detected.

[ ] Files uploaded.

[ ] User confirmed submission.

[ ] Status changed.

---

## Part 20 — CLI User Experience

### Goal

Create a useful command-line interface before building the web dashboard.

### Why this is being done

CLI is faster to build and easier to test. The web interface can reuse the same services.

### Tasks

[ ] Implement commands:

```bash
jobagent init
jobagent doctor
jobagent profile validate
jobagent profile show
jobagent import-cv ./cv.tex
jobagent add-job --file ./job.txt
jobagent add-job --url "https://..."
jobagent add-job --text "..."
jobagent analyze JOB_ID
jobagent tailor JOB_ID
jobagent cover-letter JOB_ID
jobagent answers JOB_ID
jobagent approve-answers JOB_ID
jobagent prepare JOB_ID
jobagent apply-assist JOB_ID
jobagent mark-submitted JOB_ID
jobagent list
jobagent list --date YYYY-MM-DD
jobagent list --status submitted
jobagent daily-summary
jobagent followups
jobagent interview-prep JOB_ID
```

[ ] Use Rich tables for output.

[ ] Use clear errors.

[ ] Show next recommended command after each step.

---

## Part 21 — Web Interface / Dashboard

### Goal

Create an interface so the user can see what is going on visually.

### Why this is being done

The user wants to monitor applications, review generated documents, approve answers, and track progress without only using the terminal.

### Recommended MVP interface

Use FastAPI with simple Jinja2 templates first. A React/Next.js frontend can come later.

### Tasks

[ ] Create FastAPI app.

[ ] Add route:

```text
GET /
```

[ ] Dashboard should show:

[ ] Total jobs.

[ ] Applications prepared today.

[ ] Applications submitted today.

[ ] Applications needing review.

[ ] Follow-ups due.

[ ] Recent applications.

[ ] Add route:

```text
GET /applications
```

[ ] Show application table with:

```text
date
company
role
location
fit score
status
source
folder path
```

[ ] Add route:

```text
GET /applications/{id}
```

[ ] Application detail page should show:

[ ] Job description.

[ ] Fit score.

[ ] Extracted requirements.

[ ] Tailoring strategy.

[ ] CV PDF link.

[ ] Cover letter link.

[ ] Generated answers.

[ ] Approved answers.

[ ] Browser-assist status.

[ ] Screenshots.

[ ] Metadata.

[ ] Audit log.

[ ] Add route:

```text
POST /applications/{id}/approve-answers
```

[ ] Add route:

```text
POST /applications/{id}/prepare
```

[ ] Add route:

```text
POST /applications/{id}/mark-submitted
```

[ ] Add route:

```text
POST /applications/{id}/status
```

[ ] Add route:

```text
GET /daily/{date}
```

[ ] Daily page should show all applications under that date folder.

[ ] Add route:

```text
GET /followups
```

[ ] Add document preview support:

[ ] Open tailored CV PDF.

[ ] Open cover letter.

[ ] Open generated answers.

[ ] Open interview prep.

[ ] Add a visual pipeline:

```text
Found → Analyzed → Prepared → Needs Review → Ready → Browser Assist → Submitted → Follow-up → Interview/Rejected/Offer
```

[ ] Add status badges.

[ ] Add warning badges for:

```text
sensitive answers pending
unsupported claim detected
LaTeX compile failed
missing CV
missing profile facts
missing approved answers
```

[ ] Add command:

```bash
jobagent serve
```

[ ] `jobagent serve` should start local web UI:

```text
http://localhost:8000
```

---

## Part 22 — Tests

### Goal

Make the app reliable before using it for real applications.

### Why this is being done

The app handles important documents and should not silently generate wrong or unsupported content.

### Tasks

[ ] Add unit tests for folder creation.

[ ] Add unit tests for profile validation.

[ ] Add unit tests for job parsing.

[ ] Add unit tests for fit scoring.

[ ] Add unit tests for model provider.

[ ] Add unit tests for CV tailoring safety checks.

[ ] Add unit tests for LaTeX compilation.

[ ] Add unit tests for answer generation.

[ ] Add unit tests for sensitive field detection.

[ ] Add unit tests for no-fabrication reviewer.

[ ] Add integration tests for `prepare`.

[ ] Add mocked browser tests for redirection.

[ ] Add tests proving final submit is never clicked automatically.

---

## Part 23 — README Documentation

### Goal

Document how to install, configure, and use the app.

### Why this is being done

The user should be able to set up the app without remembering implementation details.

### Tasks

[ ] Add installation steps.

[ ] Add Ollama setup:

```bash
ollama pull qwen2.5-coder:3b
```

[ ] Add optional larger model:

```bash
ollama pull qwen2.5-coder:7b
```

[ ] Add `.env` example.

[ ] Add profile file examples.

[ ] Add how to import LaTeX CV.

[ ] Add how to add a job.

[ ] Add how to prepare an application.

[ ] Add how to use browser-assist.

[ ] Add how daily folders work.

[ ] Add how to open dashboard.

[ ] Add limitations and compliance notes.

---

## Part 24 — Final Acceptance Criteria

### Goal

Define when the app is considered ready for first real use.

### Why this is being done

Codex needs a clear definition of done.

### Checklist

[ ] `jobagent init` works.

[ ] `jobagent doctor` works.

[ ] Profile files are validated.

[ ] Master LaTeX CV can be imported.

[ ] A job can be added from a local text file.

[ ] A job can be parsed into structured JSON.

[ ] A fit score is generated.

[ ] A daily application folder is created.

[ ] A tailored CV `.tex` is generated.

[ ] A tailored CV `.pdf` is compiled.

[ ] A cover letter is generated.

[ ] Application answers are generated for common questions.

[ ] Sensitive answers require manual review.

[ ] Unsupported claims are detected.

[ ] Approved answers are saved separately.

[ ] Browser-assist opens the application URL.

[ ] LinkedIn/Indeed external redirects are saved.

[ ] ATS platform detection works for common platforms.

[ ] Safe fields can be filled after approval.

[ ] Final submit is never clicked automatically.

[ ] Confirmation screenshot can be saved.

[ ] Application status can be changed.

[ ] Daily summaries are generated.

[ ] Follow-up emails are generated.

[ ] Interview prep pack is generated.

[ ] Dashboard shows application progress.

[ ] Tests pass.

---

## Suggested first Codex instruction

Use this as the first message to Codex:

```text
Build the Agentic Job Application Manager described in TODO_CODEX_BUILD.md.

Start with Parts 1–6 only:
1. Project setup
2. Configuration
3. Database models
4. Profile storage and validation
5. Daily application folder system
6. Model provider layer with Ollama as default

Use Python 3.12+, Typer, Rich, SQLModel, Pydantic Settings, and Ollama.

Default local model should be qwen2.5-coder:3b.

Do not implement browser automation yet. Create clean services, tests, README updates, and CLI commands:
jobagent init
jobagent doctor
jobagent profile validate
jobagent import-cv
jobagent list
```

After Parts 1–6 are working, continue with job parsing, CV tailoring, and application package generation.
