# Codex TODO — Authenticated Supervised Browser Assist Improvements

This TODO is for the next development milestone of the `job-agent` project.

The current MVP can initialize the app, import CVs, add jobs, prepare application packages, generate answers, and run tests. The next goal is to make the app safer and more useful for real supervised browser-assisted applications.

The app must remain a **human-approved application assistant**, not an unattended mass-application bot.

---

## Global Rules

### Goal

Keep the job-agent app compliant, safe, and user-controlled while adding authentication/session support and better browser-assist behavior.

### Why this is being done

The user wants the agent to reuse their logged-in sessions for Indeed, LinkedIn, and ATS sites without storing passwords or submitting applications automatically.

### Non-negotiable rules

[x] Never store user passwords.

[x] Never ask the user to type passwords into the CLI.

[x] Never bypass CAPTCHA.

[x] Never bypass 2FA.

[x] Never bypass rate limits.

[x] Never scrape LinkedIn/Indeed at scale.

[x] Never auto-submit applications.

[x] Never click final submit buttons.

[x] Always keep browser-assist supervised.

[x] Always let the user log in manually.

[x] Always require manual confirmation before using sensitive data.

[x] Always save authentication/session files locally only.

[x] Never commit real profile, CV, auth session, database, or application files to GitHub.

---

# Part 1 — Protect Private Files in `.gitignore`

## Goal

Make sure authentication sessions, browser profiles, CV files, application data, and sensitive profile files are never committed to GitHub.

## Why this is being done

The app will store private browser sessions, cookies, CVs, generated applications, and possibly sensitive answers. These must remain local.

## Tasks

[x] Update `.gitignore`.

[x] Add private storage ignores:

```gitignore
# Local private storage
storage/auth/
storage/browser_profiles/
storage/logs/
storage/job_agent.db
storage/applications/

# Sensitive profile data
storage/profile/sensitive_answers.json
storage/profile/profile.json
storage/profile/facts.json
storage/profile/answer_bank.json
storage/profile/preferences.json
storage/profile/links.json
storage/profile/documents.json

# Real CV files
storage/master_cv/master_cv.tex
storage/master_cv/master_cv.pdf
storage/master_cv/assets/

# Keep examples only
!storage/profile/*.example.json
!storage/master_cv/.gitkeep
!storage/profile/.gitkeep
!storage/applications/.gitkeep
!storage/logs/.gitkeep
```

[x] Add safe example files if missing:

```text
storage/profile/profile.example.json
storage/profile/facts.example.json
storage/profile/answer_bank.example.json
storage/profile/preferences.example.json
storage/profile/links.example.json
storage/profile/documents.example.json
storage/profile/sensitive_answers.example.json
```

[x] Add tests or documentation confirming real auth/profile files are ignored.

---

# Part 2 — Add Auth and Browser Profile Settings

## Goal

Add configuration paths for local browser sessions and authentication storage.

## Why this is being done

The browser assistant needs a consistent place to save and load site sessions for Indeed, LinkedIn, and ATS platforms.

## Tasks

[x] Update `app/config.py`.

[x] Add settings:

```env
AUTH_DIR=storage/auth
BROWSER_PROFILES_DIR=storage/browser_profiles

LINKEDIN_AUTH_STATE=storage/auth/linkedin_storage_state.json
INDEED_AUTH_STATE=storage/auth/indeed_storage_state.json

LINKEDIN_BROWSER_PROFILE=storage/browser_profiles/linkedin
INDEED_BROWSER_PROFILE=storage/browser_profiles/indeed
DEFAULT_BROWSER_PROFILE=storage/browser_profiles/default
```

[x] Update `.env.example`.

[x] Ensure `jobagent init` creates:

```text
storage/auth/
storage/browser_profiles/
storage/browser_profiles/linkedin/
storage/browser_profiles/indeed/
storage/browser_profiles/default/
```

[x] Update `jobagent doctor` to check these folders.

[x] Add clear warnings if auth state files are missing.

---

# Part 3 — Create `AuthSessionService`

## Goal

Create a service that manages browser login sessions without storing passwords.

## Why this is being done

The app should reuse manually authenticated sessions for LinkedIn, Indeed, and ATS platforms while keeping login credentials private.

## Tasks

[x] Create:

```text
app/services/auth_session_service.py
```

[x] Implement supported sites:

```python
SUPPORTED_AUTH_SITES = {
    "indeed": "https://uk.indeed.com/",
    "linkedin": "https://www.linkedin.com/",
    "greenhouse": "https://boards.greenhouse.io/",
    "lever": "https://jobs.lever.co/",
    "workday": "https://www.myworkdayjobs.com/",
    "default": "about:blank",
}
```

[x] Add method:

```python
def get_auth_state_path(site: str) -> Path:
    ...
```

[x] Add method:

```python
def get_browser_profile_path(site: str) -> Path:
    ...
```

[x] Add method:

```python
async def login(site: str) -> Path:
    ...
```

Expected behavior:

```text
1. Open Chromium in non-headless mode.
2. Navigate to the selected site.
3. Let the user log in manually.
4. Let the user complete 2FA/CAPTCHA manually.
5. Wait until the user presses Enter in the CLI.
6. Save Playwright storage state to storage/auth/<site>_storage_state.json.
7. Close browser only after saving.
8. Never ask for or store the password.
```

[x] Add method:

```python
def auth_status(site: str) -> dict:
    ...
```

Return:

```json
{
  "site": "indeed",
  "auth_state_exists": true,
  "auth_state_path": "storage/auth/indeed_storage_state.json",
  "last_modified": "ISO timestamp or null"
}
```

[x] Add method:

```python
def logout(site: str) -> None:
    ...
```

Expected behavior:

```text
Delete storage/auth/<site>_storage_state.json.
Optionally delete storage/browser_profiles/<site>/ after confirmation.
```

[x] Add unit tests for path resolution and status.

[x] Add mocked Playwright tests for login save behavior.

---

# Part 4 — Add Auth CLI Commands

## Goal

Allow the user to create, check, and remove local login sessions.

## Why this is being done

The user needs simple commands to log in to Indeed/LinkedIn once and reuse the session during browser-assist.

## Tasks

[x] Add CLI group or commands:

```bash
pixi run jobagent auth login indeed
pixi run jobagent auth login linkedin
pixi run jobagent auth status
pixi run jobagent auth status indeed
pixi run jobagent auth logout indeed
pixi run jobagent auth logout linkedin
```

[x] `auth login <site>` should show:

```text
A browser will open.
Log in manually.
Complete any 2FA/CAPTCHA manually.
When the site shows you are logged in, return to the terminal and press Enter.
The app will save the browser session locally.
No password will be stored.
```

[x] `auth status` should show a Rich table:

```text
Site       State File Exists       Last Modified       Path
Indeed     yes                     2026-06-21          storage/auth/indeed_storage_state.json
LinkedIn   no                      -                   storage/auth/linkedin_storage_state.json
```

[x] `auth logout <site>` should ask for confirmation before deleting.

[x] Add tests for CLI auth status output.

---

# Part 5 — Detect Source Site and Select Auth Session

## Goal

Automatically determine which auth session should be used for a job URL.

## Why this is being done

Indeed, LinkedIn, Greenhouse, Lever, Workday, and custom ATS pages need different login/session handling.

## Tasks

[x] Create or update domain detection utility.

[x] Add function:

```python
def detect_source_site(url: str) -> str:
    ...
```

[x] Rules:

```text
indeed.*            -> indeed
linkedin.com        -> linkedin
greenhouse.io       -> greenhouse
lever.co            -> lever
myworkdayjobs.com   -> workday
ashbyhq.com         -> ashby
smartrecruiters.com -> smartrecruiters
teamtailor.com      -> teamtailor
workable.com        -> workable
recruitee.com       -> recruitee
bamboohr.com        -> bamboohr
unknown             -> default
```

[x] Add tests for source site detection.

---

# Part 6 — Update `BrowserService.apply_assist`

## Goal

Make `apply-assist` use saved auth sessions, keep the browser open, follow redirections, detect forms, and support supervised safe filling.

## Why this is being done

The current browser assist is still basic. The user needs it to work with logged-in sessions and external redirections while keeping manual review and manual submission.

## Tasks

[x] Update `app/services/browser_service.py`.

[x] `apply_assist` should:

[x] Load application and job data.

[x] Detect source site from `job.source_url`.

[x] Check if saved auth state exists for the source site.

[x] If auth state is missing for LinkedIn/Indeed, show:

```text
No saved auth session found for <site>.
Run:
pixi run jobagent auth login <site>
Then retry apply-assist.
```

[x] Launch Chromium in non-headless mode.

[x] Use saved auth state or persistent browser profile.

[x] Navigate to `job.source_url`.

[x] Wait for user login/manual interaction if needed.

[x] Save source screenshot:

```text
00_job-posting/screenshots/source_page.png
```

[x] Detect and click safe Apply button only after user confirmation.

[x] If redirected, save final URL:

```text
00_job-posting/final_application_url.txt
```

[x] Save destination screenshot:

```text
00_job-posting/screenshots/destination_page.png
```

[x] Detect ATS platform.

[x] Save ATS platform to database and metadata.

[x] Detect form fields.

[x] Save detected fields:

```text
04_application/form_fields_detected.json
```

[x] Load approved answers from:

```text
04_application/application_answers.approved.json
```

[x] Show a review table:

```text
Detected field
Inferred type
Safe/sensitive/blocked
Proposed value
Source file
Will fill? yes/no
```

[x] Ask user:

```text
Fill safe fields now? yes/no
```

[x] Fill only safe fields.

[x] Do not fill sensitive fields unless explicitly approved in this session.

[x] Upload tailored CV only after confirmation.

[x] Upload cover letter only after confirmation.

[x] Never click final submit.

[x] Display:

```text
Review the application in the browser.
Submit manually if everything is correct.
After submitting, return here and type SUBMITTED.
Type CANCEL if you did not submit.
```

[x] If user types `SUBMITTED`, save:

```text
04_application/confirmation_screenshot.png
04_application/submitted_copy.html
```

[x] Mark application status as `submitted`.

[x] If user types `CANCEL`, leave status unchanged or set `needs_review`.

[x] Keep browser open until user confirms.

[x] Add tests proving browser does not close before user confirmation.

[x] Add tests proving final submit is never clicked.

---

# Part 7 — Real Safe Field Filling

## Goal

Replace preview-only filling with supervised safe filling.

## Why this is being done

The current preview is useful for safety, but the app should eventually reduce manual typing by filling approved safe fields.

## Tasks

[x] Implement safe input filling for:

```text
first name
last name
full name
email
phone
location
city
country
LinkedIn URL
GitHub URL
portfolio URL
resume upload
CV upload
cover letter text
cover letter upload
```

[x] Use only data from:

```text
storage/profile/profile.json
storage/profile/links.json
04_application/application_answers.approved.json
02_cv/cv_tailored.pdf
03_cover-letter/cover_letter.pdf
```

[x] Implement textarea filling for approved non-sensitive questions.

[x] Implement select dropdown filling only when confidence is high.

[x] Implement checkboxes/radio buttons only if safe and explicitly approved.

[x] Never fill:

```text
CAPTCHA
technical test answers
coding assessment answers
personality assessment answers
demographic answers
criminal history answers
disability answers
gender answers
ethnicity answers
references
right-to-work
visa sponsorship
salary
notice period
```

unless the user explicitly approves during that browser-assist session.

[x] Add field safety classifier:

```python
class FieldSafety:
    SAFE = "safe"
    SENSITIVE = "sensitive"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"
```

[x] Add tests for safe/sensitive/blocked classification.

---

# Part 8 — Improve Interactive Answer Approval

## Goal

Make answer approval manual, visible, and editable.

## Why this is being done

Generated application answers can affect real job outcomes. The user should approve, edit, reject, or skip each answer.

## Tasks

[x] Update `approve-answers` command.

[x] Load:

```text
04_application/application_answers.generated.json
```

[x] For each answer, display:

```text
Question
Question type
Generated answer
Source facts used
Sensitive: yes/no
Unsupported claims
Confidence
```

[x] Ask:

```text
[A] approve
[E] edit
[R] reject
[S] skip
[Q] quit
```

[x] If user chooses edit, open multiline editor or prompt for edited answer.

[x] Save approved/edited answers to:

```text
04_application/application_answers.approved.json
```

[x] Rejected answers should not be saved as approved.

[x] Skipped answers should remain pending.

[x] Sensitive answers must never be approved automatically.

[x] If unsupported claims exist, block approval unless the answer is edited to remove them.

[x] Update `submission_review.md` with approval status.

[x] Add tests:

[x] Non-sensitive answers can be approved.

[x] Sensitive answers require explicit approval.

[x] Unsupported claims block approval.

[x] Edited answers are saved correctly.

---

# Part 9 — Improve `jobagent doctor`

## Goal

Make health checks clearer and less likely to show false warnings.

## Why this is being done

The current Ollama check can time out too quickly, and Playwright errors should tell the user exactly how to fix them.

## Tasks

[x] Increase Ollama timeout from 2 seconds to 10 seconds.

[x] If Ollama is unavailable, show:

```text
Ollama is not responding.
Start it with:
ollama serve
```

[x] If Ollama model is missing, show:

```text
Install the default model:
ollama pull qwen2.5-coder:3b
```

[x] If Playwright Chromium is missing, show:

```text
Install Chromium:
pixi run python -m playwright install chromium
```

[x] Check auth folders:

```text
storage/auth
storage/browser_profiles
```

[x] Check auth state files if present.

[x] Do not fail the whole doctor command if auth files are missing; show warning only.

[x] Add tests for doctor messages.

---

# Part 10 — Add Raw Jobs Listing

## Goal

Add a command to list jobs that were added but not yet prepared.

## Why this is being done

Currently `jobagent list` shows applications only. After `add-job`, the user cannot easily see raw jobs before running `prepare`.

## Tasks

[x] Add command:

```bash
pixi run jobagent jobs
```

[x] Show Rich table:

```text
Job ID
Company
Title
Source
Source URL
Status
Created At
Prepared? yes/no
```

[x] Add filters:

```bash
pixi run jobagent jobs --status found
pixi run jobagent jobs --source indeed
pixi run jobagent jobs --unprepared
```

[x] Add command:

```bash
pixi run jobagent job JOB_ID
```

[x] `job JOB_ID` should show:

```text
company
title
location
source
source_url
final_application_url
status
short description preview
related application ID if prepared
```

[x] Optional: parse company/title during `add-job` if the parser is cheap and available.

[x] Add tests for raw job listing.

---

# Part 11 — Fix Dashboard Today Stats

## Goal

Correct dashboard counts for applications prepared/submitted today.

## Why this is being done

The current dashboard can count all dated applications as today if it only checks whether a date string exists.

## Tasks

[x] Update dashboard stats logic.

[x] Use:

```python
from datetime import date

today = date.today()

prepared_today = sum(
    1 for app, _ in rows
    if app.application_date and app.application_date.date() == today
)

submitted_today = sum(
    1 for app, _ in rows
    if app.submitted_at and app.submitted_at.date() == today
)
```

[x] Add dashboard cards:

```text
Prepared Today
Submitted Today
Needs Review
Follow-ups Due
```

[x] Add tests:

[x] Application from today is counted.

[x] Application from yesterday is not counted.

[x] Submitted today is counted.

[x] Submitted yesterday is not counted.

---

# Part 12 — Improve Metadata and Audit Logs for Auth/Browser Assist

## Goal

Record what happened during browser assist without storing secrets.

## Why this is being done

The user needs traceability for every application, but auth/session details must remain private.

## Tasks

[x] Update `metadata.json` with:

```json
{
  "auth_site": "indeed",
  "auth_state_used": true,
  "auth_state_path": "storage/auth/indeed_storage_state.json",
  "source_url": "",
  "final_application_url": "",
  "ats_platform": "",
  "browser_assist_started_at": "",
  "browser_assist_completed_at": "",
  "manual_submit_confirmed": false
}
```

[x] Do not store cookies in metadata.

[x] Do not store passwords.

[x] Do not store full auth state content.

[x] Add audit log entries:

```text
Auth session checked.
Auth session loaded.
Browser assist started.
Source page opened.
Apply redirection detected.
ATS platform detected.
Fields detected.
Safe fields filled.
CV upload confirmed.
Cover letter upload confirmed.
User confirmed manual submission.
Confirmation screenshot saved.
```

[x] Add tests for audit log entries.

---

# Part 13 — Documentation Updates

## Goal

Explain how authentication/session storage and supervised browser assist work.

## Why this is being done

The user needs to know how to log in safely and what the app will/will not do.

## Tasks

[x] Update `README.md`.

[x] Add section:

```markdown
## Authentication and Browser Sessions
```

[x] Explain:

```text
The app does not store passwords.
You log in manually in the opened browser.
The app saves local browser session state.
You can delete sessions with auth logout.
Session files are ignored by Git.
```

[x] Add usage:

```bash
pixi run jobagent auth login indeed
pixi run jobagent auth login linkedin
pixi run jobagent auth status
pixi run jobagent auth logout indeed
```

[x] Add browser-assist usage:

```bash
pixi run jobagent apply-assist APPLICATION_ID
```

[x] Add warning:

```text
The app never clicks final submit. You must review and submit manually.
```

[x] Add troubleshooting:

```bash
pixi run python -m playwright install chromium
ollama serve
ollama pull qwen2.5-coder:3b
```

---

# Part 14 — Tests and Acceptance Criteria

## Goal

Define when this milestone is complete.

## Why this is being done

Codex needs a clear definition of done.

## Required tests

[x] Existing tests still pass.

[x] New auth session tests pass.

[x] New raw jobs listing tests pass.

[x] New dashboard stats tests pass.

[x] New doctor message tests pass.

[x] New answer approval tests pass.

[x] New browser-assist safety tests pass.

[x] Test proves final submit is never clicked.

[x] Test proves sensitive answers are never auto-approved.

[x] Test proves missing auth state gives useful message.

[x] Test proves auth state files are not committed.

## Manual acceptance checklist

[x] `pixi run jobagent doctor` shows clear fix instructions for missing Ollama/Playwright.

[x] `pixi run jobagent auth login indeed` opens browser and saves local session.

[x] `pixi run jobagent auth status` shows Indeed session exists.

[x] `pixi run jobagent jobs` shows jobs added with `add-job`.

[x] `pixi run jobagent prepare JOB_ID` still works.

[x] `pixi run jobagent approve-answers APPLICATION_ID` lets user approve/edit/reject answers.

[x] `pixi run jobagent apply-assist APPLICATION_ID` opens browser using saved session.

[x] Browser assist follows Indeed/LinkedIn redirection when present.

[x] Browser assist detects fields and shows review.

[x] Browser assist fills only safe approved fields.

[x] Browser assist uploads CV only after confirmation.

[x] Browser assist never submits automatically.

[x] After manual submission, confirmation screenshot and HTML are saved.

[x] Dashboard counts today’s applications correctly.

---

# Suggested Codex Prompt

Paste this into Codex:

```text
Continue from the current job-agent GitHub state.

Implement the milestone described in this TODO file.

Focus on:
1. Auth/session storage using Playwright without storing passwords.
2. `jobagent auth login/status/logout`.
3. Updating `apply-assist` to use saved sessions, follow redirects, detect fields, fill only safe approved fields, and never submit.
4. Interactive `approve-answers`.
5. Better `doctor` messages.
6. Raw `jobagent jobs` listing.
7. Dashboard today stats fix.
8. Strong `.gitignore` protections for local/private files.
9. Tests for all safety requirements.

Keep the app supervised and human-approved. Do not build an unattended mass-application bot.
```

