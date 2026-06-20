# TODO — Agentic Job Application Manager

This file is intended to be given directly to Codex as the implementation checklist.

The goal is to build a local, supervised AI-powered job application manager that can prepare tailored applications from a LaTeX CV, generate job-specific CVs and cover letters, organize every application into folders, help with form filling, and provide an interface to track progress.

Important product rule: this should be a **human-approved application assistant**, not an unattended mass-application bot. It must not bypass CAPTCHA, rate limits, assessments, or platform restrictions. It must never submit applications without explicit user approval.

---

## Part 0 — Project Setup and Safety Rules

### Goal
Create the base project structure and define non-negotiable rules before building features.

### Why this is being done
The system will interact with job boards, CV files, personal information, and application forms. A clear project structure and safety rules prevent messy code, accidental platform abuse, and unsupported claims in applications.

### Tasks

[ ] Create a new repository named `agentic-application-manager`.

[ ] Create the base project structure:

```text
app/
  main.py
  config.py
  cli.py
  agents/
  services/
  models/
  prompts/
  templates/
  storage/
  tests/
README.md
TODO.md
.env.example
pyproject.toml
```

[ ] Set up Python 3.12+.

[ ] Add dependencies:

```text
fastapi
uvicorn
typer
rich
pydantic
sqlmodel
sqlalchemy
jinja2
python-dotenv
playwright
pytest
ruff
mypy
```

[ ] Add optional LaTeX compiler support for either `latexmk` or `tectonic`.

[ ] Create `.env.example` with placeholders for model provider settings, storage path, and database URL.

[ ] Create a central `config.py` file that loads environment variables.

[ ] Create a safety policy module that enforces these rules:

```text
- Never evade platform rate limits.
- Never scrape LinkedIn or Indeed at scale.
- Never fabricate skills, education, experience, dates, or work authorization.
- Always pause before final application submission.
- Always store the generated CV and cover letter used for each application.
- Always keep the original job description.
```

[ ] Add `README.md` with the project goal, setup instructions, and the supervised-use policy.

[ ] Add `TODO.md` to the repository using this checklist.

---

## Part 1 — Candidate Profile and Master CV Import

### Goal
Create a reliable source of truth for the candidate’s personal details, skills, experience, and master LaTeX CV.

### Why this is being done
The agent must tailor applications without inventing facts. A structured candidate profile allows the AI to reuse only approved information and prevents unsupported claims.

### Tasks

[ ] Create a `CandidateProfile` model.

[ ] Include fields for:

```text
name
email
phone
location
linkedin_url
github_url
portfolio_url
work_authorisation
notice_period
salary_expectation
summary
skills
education
experience
projects
master_cv_tex_path
```

[ ] Create a CLI command:

```bash
jobagent profile setup
```

[ ] Create a CLI command:

```bash
jobagent import-cv ./path/to/cv.tex
```

[ ] Store the imported master CV in:

```text
storage/master_cv/master_cv.tex
```

[ ] Create `storage/profile/profile.json`.

[ ] Create `storage/profile/answer_bank.json` for reusable application answers.

[ ] Add fields to the answer bank for:

```text
salary expectation
notice period
work authorization
why this role
why this company
tell us about yourself
remote work preference
relocation preference
```

[ ] Mark sensitive answers as requiring manual confirmation before use.

[ ] Add validation so the system cannot proceed without a master LaTeX CV.

[ ] Add tests for profile creation and CV import.

---

## Part 2 — Database and Application Tracker Core

### Goal
Create persistent tracking for jobs, applications, generated documents, and statuses.

### Why this is being done
The user needs to know which jobs were found, prepared, submitted, followed up, rejected, or moved to interview. A database also prevents duplicate applications.

### Tasks

[ ] Add SQLite database support for the MVP.

[ ] Create models:

```text
Job
Application
GeneratedDocument
ApplicationEvent
```

[ ] `Job` should include:

```text
id
company
title
location
remote_type
salary_min
salary_max
source
source_url
description_text
description_html_path
date_found
deadline
status
created_at
updated_at
```

[ ] `Application` should include:

```text
id
job_id
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

[ ] Add valid application statuses:

```text
found
analyzed
prepared
needs_review
ready_to_apply
applied
submitted
follow_up_needed
interview
rejected
offer
archived
```

[ ] Create a database initialization command:

```bash
jobagent init
```

[ ] Create a command to list applications:

```bash
jobagent list
```

[ ] Create a command to filter applications by status:

```bash
jobagent list --status prepared
```

[ ] Create a command to view one application:

```bash
jobagent show APPLICATION_ID
```

[ ] Add duplicate detection using:

```text
company + title
source_url
job description hash
similarity score between job descriptions
```

[ ] Add tests for database creation, status updates, and duplicate detection.

---

## Part 3 — Job Input and Job Description Storage

### Goal
Allow the user to add jobs from pasted text, local files, saved HTML, or URLs.

### Why this is being done
The system needs job descriptions before it can score the job, tailor the CV, or write a cover letter. Supporting multiple input types keeps the workflow flexible.

### Tasks

[ ] Create a command to add a job from a text file:

```bash
jobagent add-job --file ./job.txt
```

[ ] Create a command to add a job from pasted text:

```bash
jobagent add-job --text "..."
```

[ ] Create a command to add a job from a URL:

```bash
jobagent add-job --url "https://example.com/job"
```

[ ] For URL input, save the URL and page title where possible.

[ ] Do not build large-scale scraping.

[ ] Do not automatically crawl job boards.

[ ] Save the original job description in each application folder.

[ ] Save original HTML if provided or accessible.

[ ] Create a `JobInputService`.

[ ] Normalize whitespace in job descriptions.

[ ] Generate a hash of the job description for duplicate detection.

[ ] Add tests for text, file, and URL job inputs.

---

## Part 4 — Application Folder Generator

### Goal
Create a clean, meaningful folder for every application.

### Why this is being done
Every job application should be easy to audit later. The user should be able to open one folder and see the job post, tailored CV, cover letter, answers, screenshots, metadata, and follow-up notes.

### Tasks

[ ] Create a `FolderService`.

[ ] Generate folder names using this format:

```text
YYYY-MM-DD_company-slug_role-slug_location-slug
```

[ ] Example folder name:

```text
2026-06-20_software-mind_python-developer_remote
```

[ ] Create this folder structure for every application:

```text
00_job-posting/
  job_description.md
  job_description.html
  source_url.txt
  screenshots/
01_analysis/
  extracted_requirements.json
  fit_score.json
  tailoring_strategy.md
02_cv/
  cv_tailored.tex
  cv_tailored.pdf
  cv_diff.md
03_cover-letter/
  cover_letter.md
  cover_letter.pdf
04_application/
  application_answers.json
  form_fields_detected.json
  submission_review.md
  submitted_copy.html
  submitted_copy.pdf
  confirmation_screenshot.png
05_follow-up/
  follow_up_email.md
  notes.md
metadata.json
```

[ ] Sanitize folder names so they work on all operating systems.

[ ] Prevent overwriting an existing application folder.

[ ] Add a numeric suffix if a folder already exists.

[ ] Save initial `metadata.json`.

[ ] Add tests for folder creation and metadata creation.

---

## Part 5 — Job Parser Agent

### Goal
Extract structured information from each job description.

### Why this is being done
Structured job data is required for fit scoring, CV tailoring, cover letter writing, and application preparation.

### Tasks

[ ] Create `agents/job_parser.py`.

[ ] Create `prompts/job_parser.md`.

[ ] Extract the following fields:

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
application_deadline
red_flags
questions_to_answer
```

[ ] Return strict JSON from the parser.

[ ] Use `null` for unknown values.

[ ] Do not invent missing information.

[ ] Save output to:

```text
01_analysis/extracted_requirements.json
```

[ ] Update the database job record with parsed values.

[ ] Add schema validation with Pydantic.

[ ] Add tests using sample job descriptions.

---

## Part 6 — Fit Scoring Agent

### Goal
Score how well the candidate matches the job.

### Why this is being done
The user should prioritize strong opportunities instead of applying randomly. The score also explains what the CV and cover letter should emphasize.

### Tasks

[ ] Create `services/scoring_service.py`.

[ ] Calculate a score from 0 to 100.

[ ] Use this formula:

```text
must_have_skill_match: 45%
preferred_skill_match: 20%
experience_match: 15%
domain_match: 10%
location_remote_match: 5%
salary_match: 5%
```

[ ] Create a human-readable explanation of the score.

[ ] Identify missing requirements.

[ ] Identify strong matching points.

[ ] Identify risky requirements.

[ ] Save result to:

```text
01_analysis/fit_score.json
```

[ ] Update `Application.fit_score` in the database.

[ ] Add a recommendation field:

```text
apply
maybe
skip
```

[ ] Add tests for scoring logic.

---

## Part 7 — Application Strategy Planner

### Goal
Create a strategy for how the application should be positioned.

### Why this is being done
A good application is not just a generic CV and cover letter. The system should decide which skills, projects, and experiences should be emphasized for each job.

### Tasks

[ ] Create `agents/application_planner.py`.

[ ] Create `prompts/application_planner.md`.

[ ] Generate a tailoring strategy with:

```text
main selling points
skills to emphasize
projects to emphasize
experience bullets to prioritize
keywords to include
things to avoid
missing skills to handle carefully
cover letter angle
salary guidance notes
```

[ ] Do not recommend unsupported claims.

[ ] Save strategy to:

```text
01_analysis/tailoring_strategy.md
```

[ ] Add tests to ensure unsupported claims are flagged.

---

## Part 8 — LaTeX CV Tailoring Agent

### Goal
Generate a tailored LaTeX CV for each job.

### Why this is being done
Tailored CVs perform better than generic CVs, but the tailoring must remain truthful, ATS-friendly, and compilable.

### Tasks

[ ] Create `agents/cv_tailor.py`.

[ ] Create `prompts/cv_tailor.md`.

[ ] Load the master CV from:

```text
storage/master_cv/master_cv.tex
```

[ ] Parse or segment the CV into logical sections:

```text
header
summary
skills
experience
projects
education
```

[ ] Allow only safe tailoring operations:

```text
rewrite summary truthfully
reorder skills
reorder project bullets
shorten less relevant details
emphasize relevant existing experience
insert keywords only when supported by existing experience
```

[ ] Disallow unsafe operations:

```text
inventing employers
inventing degrees
inventing dates
adding unsupported technologies
claiming seniority not present in the profile
altering work authorization without confirmation
```

[ ] Save tailored LaTeX to:

```text
02_cv/cv_tailored.tex
```

[ ] Save a change explanation to:

```text
02_cv/cv_diff.md
```

[ ] Add a reviewer step to check for unsupported claims.

[ ] Add tests that verify the tailored CV does not include skills absent from the profile or master CV.

---

## Part 9 — LaTeX Compilation Service

### Goal
Compile the tailored LaTeX CV into a PDF.

### Why this is being done
Most applications require PDF CV uploads. The system should produce a ready-to-upload file for every job.

### Tasks

[ ] Create `services/latex_service.py`.

[ ] Support compilation with `latexmk`.

[ ] Optionally support compilation with `tectonic`.

[ ] Compile:

```text
02_cv/cv_tailored.tex
```

[ ] Output:

```text
02_cv/cv_tailored.pdf
```

[ ] Capture compilation logs.

[ ] If compilation fails, save logs to:

```text
02_cv/latex_compile_error.log
```

[ ] Add an automatic repair attempt for common LaTeX issues.

[ ] Limit automatic repair attempts to avoid loops.

[ ] Add tests using a minimal sample CV.

---

## Part 10 — Cover Letter and SOP Generator

### Goal
Generate a tailored cover letter or SOP for jobs that require one.

### Why this is being done
Many applications ask for a cover letter, motivation statement, or SOP. The agent should generate a natural, concise, job-specific draft instead of a generic one.

### Tasks

[ ] Create `agents/cover_letter_writer.py`.

[ ] Create `prompts/cover_letter.md`.

[ ] Generate a cover letter using:

```text
candidate profile
job description
fit score
application strategy
tailored CV summary
```

[ ] Keep the cover letter concise.

[ ] Avoid robotic phrasing.

[ ] Avoid repeating the CV line by line.

[ ] Mention company and role details when available.

[ ] Do not invent company facts.

[ ] Save Markdown version to:

```text
03_cover-letter/cover_letter.md
```

[ ] Optionally render PDF version to:

```text
03_cover-letter/cover_letter.pdf
```

[ ] Add a command:

```bash
jobagent cover-letter APPLICATION_ID
```

[ ] Add tests for cover letter generation.

---

## Part 11 — Dynamic Application Answer Generator

### Goal
Build an agent that automatically prepares high-quality answers for common application questions such as “Why this role?”, “Why this company?”, and “Tell us about yourself?”.

### Why this is being done
Many job applications ask open-text questions. These answers should not be generic copy-paste text. The agent should generate job-specific, company-aware, truthful answers using the candidate profile, master CV, job description, and approved answer bank. This makes the application more personal while keeping the user in control before submission.

### Tasks

[ ] Create `agents/form_answer_writer.py`.

[ ] Create `prompts/application_form_answer.md`.

[ ] Create a structured answer bank at:

```text
storage/profile/answer_bank.json
```

[ ] The answer bank should include reusable base answers for:

```text
why_this_role
why_this_company
tell_us_about_yourself
salary_expectation
notice_period
work_authorisation
visa_sponsorship
remote_work_preference
relocation_preference
availability_start_date
preferred_work_style
```

[ ] Use this JSON structure for every answer bank item:

```json
{
  "key": "why_this_role",
  "base_answer": "I am interested in roles where I can build reliable backend systems, work with Python/Django, and contribute to products used by real users.",
  "tone": "professional_friendly",
  "requires_manual_confirmation": false,
  "can_be_tailored": true,
  "approved_facts_only": true
}
```

[ ] Create an answer-generation service that receives:

```text
application_id
job description
parsed job requirements
company name
role title
candidate profile
master CV facts
answer bank
field label from application form
maximum character or word limit, if detected
```

[ ] The agent should detect and normalize similar form questions into known answer types. Examples:

```text
"Why do you want this role?" -> why_this_role
"Why are you interested in joining us?" -> why_this_company
"Tell us about yourself" -> tell_us_about_yourself
"Briefly introduce yourself" -> tell_us_about_yourself
"What are your salary expectations?" -> salary_expectation
"When can you start?" -> availability_start_date
```

[ ] Create a function:

```python
def classify_application_question(label: str, helper_text: str | None = None) -> ApplicationQuestionType:
    ...
```

[ ] Create a function:

```python
def generate_application_answer(application_id: int, question_label: str, max_chars: int | None = None) -> GeneratedAnswer:
    ...
```

[ ] Generated answers must include:

```text
question_label
normalized_question_type
answer
source_facts_used
confidence_score
requires_user_review
risk_notes
character_count
word_count
created_at
```

[ ] Save all generated answers to:

```text
04_application/application_answers.json
```

[ ] Also save a readable Markdown version to:

```text
04_application/application_answers.md
```

[ ] For “Why this role?”, the answer should use:

```text
role title
key responsibilities
matching candidate skills
matching projects or experience
growth motivation
remote/flexible setup, only if relevant
```

[ ] For “Why this company?”, the answer should use:

```text
company name
company mission or product, if present in the job post
engineering culture, if present in the job post
industry/domain interest
why the candidate’s background fits that company
```

[ ] If the company details are not available in the job description, the answer must avoid fake specifics and use a careful generic version.

[ ] For “Tell us about yourself”, the answer should summarize:

```text
current professional identity
education background
backend/full-stack experience
main technical skills
1-2 relevant projects or achievements
working style
what the candidate is looking for next
```

[ ] Add support for different answer lengths:

```text
short: 50-80 words
medium: 100-150 words
long: 200-300 words
character_limited: obey detected form limit
```

[ ] Add tone options:

```text
professional
professional_friendly
confident
concise
warm
```

[ ] Ensure the default tone is:

```text
professional_friendly
```

[ ] Add a no-fabrication validator that checks every generated answer against the candidate profile and CV facts.

[ ] The validator must reject answers containing unsupported claims such as:

```text
experience years not present in the CV
company-specific claims not present in the job post or approved research
technologies not present in the candidate profile
leadership claims not supported by the CV
work authorization claims not manually approved
salary expectations not approved by the user
```

[ ] Require manual confirmation for sensitive questions:

```text
work authorization
visa sponsorship
salary expectation
notice period
availability date
relocation
disability
gender
ethnicity
criminal history
references
```

[ ] For sensitive fields, generate a suggested answer but mark it as:

```text
requires_user_review: true
auto_fill_allowed: false
```

[ ] For safe fields, allow browser-assist to fill the answer only after the user confirms the preview.

[ ] Add a CLI command:

```bash
jobagent answers APPLICATION_ID
```

[ ] Add CLI options:

```bash
jobagent answers APPLICATION_ID --question "Why this role?"
jobagent answers APPLICATION_ID --all-common
jobagent answers APPLICATION_ID --tone professional_friendly
jobagent answers APPLICATION_ID --length medium
```

[ ] Add an interactive review screen showing:

```text
Question
Generated answer
Facts used
Risk notes
Character count
Manual review required: yes/no
Approve / Edit / Regenerate / Skip
```

[ ] Allow the user to edit and save the final approved answer.

[ ] Store approved answers separately from draft answers:

```text
04_application/application_answers.approved.json
```

[ ] Browser-assist mode must use only approved answers when filling text areas.

[ ] Add unit tests for question classification.

[ ] Add unit tests for answer generation.

[ ] Add tests ensuring unsupported claims are rejected.

[ ] Add tests ensuring sensitive answers are never auto-approved.

[ ] Add tests ensuring character limits are respected.

### Example generated answer behavior

For a Python/Django backend role, the agent should generate something like this:

```text
Question: Why this role?

Answer:
I am interested in this role because it closely matches my backend development experience with Python, Django, relational databases, Redis, and scheduled jobs. I enjoy building reliable, maintainable systems and working on practical products where backend quality directly affects users. The role also looks like a strong opportunity to contribute to an international engineering team while continuing to grow in a fast-paced technical environment.
```

For a company-focused question, the agent should generate something like this:

```text
Question: Why this company?

Answer:
I am interested in this company because the role appears to combine technical ownership, collaborative engineering, and real product impact. I am especially drawn to environments where developers are trusted to solve problems, improve systems, and keep learning. Based on my background in Python, Django, data-driven projects, and full-stack development, I believe I could contribute quickly while growing with the team.
```

For an introduction question, the agent should generate something like this:

```text
Question: Tell us about yourself.

Answer:
I am a software developer with experience in backend and full-stack development, especially with Python, Django, relational databases, JavaScript, Go, and Flutter. I also have an academic background in Cognitive Neuroimaging and Data Science, which strengthened my analytical and problem-solving skills. I enjoy building practical, user-focused systems, learning quickly, and working with teams that value clean engineering and continuous improvement.
```

---

## Part 12 — Application Package Reviewer

### Goal
Review the full application package before applying.

### Why this is being done
The system should catch mistakes before the user submits an application. This reduces risk from unsupported claims, weak tailoring, missing documents, or formatting problems.

### Tasks

[ ] Create `agents/reviewer.py`.

[ ] Create `prompts/reviewer.md`.

[ ] Review:

```text
parsed job requirements
fit score
tailoring strategy
tailored CV
cover letter
application answers
sensitive fields
missing documents
LaTeX compilation status
```

[ ] Return:

```text
approved: true/false
required_fixes
suggested_improvements
risk_notes
final_recommendation
```

[ ] Save review to:

```text
04_application/submission_review.md
```

[ ] If review fails, set application status to:

```text
needs_review
```

[ ] If review passes, set application status to:

```text
ready_to_apply
```

[ ] Add tests for reviewer output.

---

## Part 13 — One-Command Preparation Flow

### Goal
Create a single command that prepares the full application package.

### Why this is being done
The user should not need to run many commands manually for every job. A one-command workflow makes the tool practical.

### Tasks

[ ] Create this command:

```bash
jobagent prepare JOB_ID
```

[ ] The command should run:

```text
create application folder
parse job
score fit
create application strategy
tailor CV
compile CV PDF
generate cover letter
generate application answers
review package
save metadata
update database status
```

[ ] Display a summary in the terminal:

```text
Company
Role
Location
Fit score
Recommendation
CV path
Cover letter path
Application folder path
Status
Warnings
```

[ ] Add a `--no-cover-letter` option.

[ ] Add a `--force` option for regenerating documents.

[ ] Add a `--dry-run` option that previews actions without writing files.

[ ] Add integration tests for the full preparation flow.

---

## Part 14 — Supervised Browser-Assist Mode

### Goal
Help the user complete application forms in a browser while keeping the user in control.

### Why this is being done
Job applications often require web forms. The system should reduce manual copying and uploading, but it must not behave like an unattended bot.

### Tasks

[ ] Create `services/browser_service.py`.

[ ] Use Playwright with `headless=False`.

[ ] Create this command:

```bash
jobagent apply-assist APPLICATION_ID
```

[ ] Open the job application URL in a visible browser.

[ ] Wait for the user to log in manually if required.

[ ] Detect visible form fields.

[ ] Save detected fields to:

```text
04_application/form_fields_detected.json
```

[ ] Match fields with generated application answers.

[ ] Show the user a review table before filling anything.

[ ] Fill only safe fields after explicit approval:

```text
name
email
phone
location
LinkedIn URL
GitHub URL
portfolio URL
notice period
cover letter text
resume upload field
```

[ ] Require manual confirmation for sensitive fields.

[ ] Never fill CAPTCHA.

[ ] Never answer technical assessments.

[ ] Never submit the final application automatically.

[ ] Pause before the submit button.

[ ] Show this message:

```text
Review the application in the browser. Submit manually only if everything is correct.
```

[ ] After the user confirms they submitted, save:

```text
submitted_copy.html
confirmation_screenshot.png
```

[ ] Set application status to:

```text
submitted
```

[ ] Add tests/mocks ensuring submit buttons are never clicked automatically.

---

## Part 15 — Follow-Up and Interview Prep Tools

### Goal
Help the user follow up and prepare after applying.

### Why this is being done
The application process continues after submission. The system should help the user stay organized and ready for interviews.

### Tasks

[ ] Add a follow-up date to every submitted application.

[ ] Default follow-up date should be 5 to 7 business days after submission.

[ ] Create this command:

```bash
jobagent followups
```

[ ] Generate follow-up email drafts.

[ ] Save follow-up drafts to:

```text
05_follow-up/follow_up_email.md
```

[ ] Create this command:

```bash
jobagent interview-prep APPLICATION_ID
```

[ ] Generate:

```text
company summary
role summary
important requirements
likely technical questions
likely behavioral questions
candidate projects to discuss
questions to ask recruiter
salary discussion notes
```

[ ] Save interview prep to:

```text
05_follow-up/interview_prep.md
```

[ ] Add tests for follow-up date calculation.

---

## Part 16 — Logging, Audit Trail, and Metadata

### Goal
Make every application traceable.

### Why this is being done
The user needs to know exactly what was generated, when it was generated, what was submitted, and what changed from the master CV.

### Tasks

[ ] Create `ApplicationEvent` records for important actions:

```text
job_added
folder_created
job_parsed
fit_scored
cv_tailored
cv_compiled
cover_letter_generated
package_reviewed
browser_assist_started
submitted
follow_up_created
status_changed
```

[ ] Save all important timestamps.

[ ] Save model names used for AI-generated outputs.

[ ] Save prompt version names.

[ ] Save metadata in:

```text
metadata.json
```

[ ] Update metadata after every major step.

[ ] Add an export command:

```bash
jobagent export APPLICATION_ID
```

[ ] Export a zip file containing the full application folder.

[ ] Add tests for metadata updates.

---

## Part 17 — Quality Checks and Test Suite

### Goal
Make the tool reliable before using it on real applications.

### Why this is being done
The system handles important career documents. Bugs could cause embarrassing or harmful applications, so testing is required.

### Tasks

[ ] Add unit tests for all models.

[ ] Add unit tests for folder generation.

[ ] Add unit tests for job parsing schema validation.

[ ] Add unit tests for fit scoring.

[ ] Add unit tests for duplicate detection.

[ ] Add unit tests for application status transitions.

[ ] Add tests for LaTeX compilation using a sample CV.

[ ] Add tests ensuring unsupported skills are not added to the CV.

[ ] Add tests ensuring sensitive fields require manual confirmation.

[ ] Add tests ensuring browser-assist never clicks final submit.

[ ] Add a lint command:

```bash
ruff check .
```

[ ] Add a type-check command:

```bash
mypy app
```

[ ] Add a test command:

```bash
pytest
```

[ ] Add these commands to the README.

---

## Part 18 — Web Interface / Dashboard

### Goal
Create an interface so the user can see what is going on, manage applications, inspect generated files, and track statuses.

### Why this is being done
A CLI is useful for development, but the user needs a visual dashboard to monitor applications, review packages, open generated CVs and cover letters, and understand the current state of the job search.

### Tasks

[ ] Create a FastAPI backend if not already active.

[ ] Add API endpoints:

```text
GET /applications
GET /applications/{id}
GET /applications/{id}/files
GET /applications/{id}/events
POST /jobs
POST /applications/{id}/prepare
POST /applications/{id}/status
POST /applications/{id}/apply-assist
POST /applications/{id}/follow-up
```

[ ] Create a frontend app using React, Next.js, or simple FastAPI templates.

[ ] Create a dashboard homepage showing:

```text
total jobs
prepared applications
ready-to-apply applications
submitted applications
interviews
rejections
offers
follow-ups due
```

[ ] Create a Kanban board with columns:

```text
Found
Analyzed
Prepared
Ready to Apply
Submitted
Follow-Up Needed
Interview
Rejected
Offer
Archived
```

[ ] Create an application detail page showing:

```text
company
role
location
source URL
fit score
recommendation
status
folder path
generated CV link
cover letter link
application answers
review warnings
event timeline
follow-up date
notes
```

[ ] Add buttons for:

```text
Prepare application
Regenerate CV
Regenerate cover letter
Open application folder
Start browser assist
Mark as submitted
Create follow-up email
Generate interview prep
Archive application
```

[ ] Add a document preview area for:

```text
CV PDF
cover letter
job description
submission review
interview prep
follow-up email
```

[ ] Add a progress timeline for each application:

```text
Job added → Parsed → Scored → CV tailored → Cover letter generated → Reviewed → Ready → Submitted → Follow-up
```

[ ] Add warnings for applications that need review.

[ ] Add visual labels for:

```text
high fit
medium fit
low fit
missing required skills
sensitive fields need confirmation
follow-up due
```

[ ] Add a settings page for:

```text
candidate profile
answer bank
storage location
model provider
LaTeX compiler path
browser-assist settings
```

[ ] Add a local-only mode warning so the user understands where data is stored.

[ ] Add authentication if the interface is exposed beyond localhost.

[ ] Add tests for API endpoints.

[ ] Add README instructions for running the interface:

```bash
uvicorn app.main:app --reload
```

[ ] Add README instructions for running the frontend if a separate frontend is used.

---

## Part 19 — Final Acceptance Criteria

### Goal
Define when the project is considered usable.

### Why this is being done
Clear acceptance criteria prevent an unfinished prototype from being mistaken for a working application manager.

### Tasks

[ ] The user can import a LaTeX CV.

[ ] The user can add a job from a text file.

[ ] The user can add a job from pasted text.

[ ] The system creates a meaningful application folder.

[ ] The system stores the original job description.

[ ] The system parses the job into structured JSON.

[ ] The system scores the job fit.

[ ] The system creates a truthful tailoring strategy.

[ ] The system generates a tailored LaTeX CV.

[ ] The system compiles the tailored CV to PDF.

[ ] The system creates a CV diff explanation.

[ ] The system generates a tailored cover letter.

[ ] The system generates application form answers.

[ ] Sensitive answers require manual confirmation.

[ ] The reviewer catches unsupported claims.

[ ] The browser-assist mode opens a visible browser.

[ ] The browser-assist mode does not click final submit.

[ ] The user can mark an application as submitted.

[ ] The system saves a confirmation screenshot or copy when available.

[ ] The system creates follow-up drafts.

[ ] The system creates interview prep notes.

[ ] The dashboard shows all applications and statuses.

[ ] The dashboard lets the user open generated files.

[ ] The dashboard shows a clear timeline of each application.

[ ] All tests pass.

[ ] README contains setup, usage, safety rules, and troubleshooting instructions.

---

## Suggested Build Order for Codex

Use this implementation order:

[ ] Part 0 — Project Setup and Safety Rules

[ ] Part 1 — Candidate Profile and Master CV Import

[ ] Part 2 — Database and Application Tracker Core

[ ] Part 3 — Job Input and Job Description Storage

[ ] Part 4 — Application Folder Generator

[ ] Part 5 — Job Parser Agent

[ ] Part 6 — Fit Scoring Agent

[ ] Part 7 — Application Strategy Planner

[ ] Part 8 — LaTeX CV Tailoring Agent

[ ] Part 9 — LaTeX Compilation Service

[ ] Part 10 — Cover Letter and SOP Generator

[ ] Part 11 — Application Answer Generator

[ ] Part 12 — Application Package Reviewer

[ ] Part 13 — One-Command Preparation Flow

[ ] Part 14 — Supervised Browser-Assist Mode

[ ] Part 15 — Follow-Up and Interview Prep Tools

[ ] Part 16 — Logging, Audit Trail, and Metadata

[ ] Part 17 — Quality Checks and Test Suite

[ ] Part 18 — Web Interface / Dashboard

[ ] Part 19 — Final Acceptance Criteria

---

## MVP Definition

The first working version should only include these items:

[ ] Import master LaTeX CV.

[ ] Add a job from a text file.

[ ] Parse the job description.

[ ] Create the application folder.

[ ] Score the job.

[ ] Tailor the CV.

[ ] Compile the tailored CV to PDF.

[ ] Generate a cover letter.

[ ] Save metadata.

[ ] Show the application in the CLI.

After the MVP works reliably, continue with browser-assist and the web dashboard.

