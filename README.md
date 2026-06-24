# Agentic Application Manager

Local, supervised job application assistant for preparing tailored job applications from an approved LaTeX CV.

The app is a human-approved assistant, not an unattended application bot. It does not store passwords, bypass CAPTCHA/2FA/rate limits, or submit applications automatically.

## Setup

Use Pixi for all package and task management:

```bash
pixi install
pixi run jobagent init
pixi run jobagent doctor
```

If Playwright Chromium is missing:

```bash
pixi run python -m playwright install chromium
```

If you want real LLM output through Ollama:

```bash
ollama serve
ollama pull qwen2.5-coder:3b
```

The app can run without Ollama, but generation falls back to rule-based output.

## Add Your Details

Put draft/current CVs and supporting material in `drafts/`. When your LaTeX CV is ready:

```bash
pixi run jobagent import-cv drafts/cv.tex
```

Then edit these local files:

- `storage/profile/profile.json`: name, email, phone, location, links, skills, education, experience, projects.
- `storage/profile/facts.json`: approved facts the assistant may use; blocked claims it must avoid.
- `storage/profile/answer_bank.json`: reusable answers for common questions.
- `storage/profile/preferences.json`: target roles, locations, salary floor, industries, avoid list.
- `storage/profile/links.json`: LinkedIn, GitHub, portfolio, personal site.
- `storage/profile/documents.json`: optional document paths.

Real profile/CV/application/session files are ignored by Git. Safe examples live as `storage/profile/*.example.json`.

## Authentication and Browser Sessions

The app does not store passwords. You log in manually in the opened browser, complete any 2FA/CAPTCHA yourself, and the app saves local Playwright session state.

```bash
pixi run jobagent auth login indeed
pixi run jobagent auth login linkedin
pixi run jobagent auth status
pixi run jobagent auth logout indeed
```

Session files are stored under `storage/auth/` and browser profiles under `storage/browser_profiles/`. Both are ignored by Git.

## Application Workflow

```bash
pixi run jobagent add-job --file ./job_indeed_cgi_software_engineers.txt --source-url "https://uk.indeed.com/viewjob?jk=51baa25edf955295&from=shareddesktop_copy" --source indeed
pixi run jobagent jobs
pixi run jobagent prepare JOB_ID
pixi run jobagent list
pixi run jobagent approve-answers APPLICATION_ID
pixi run jobagent auth login indeed
pixi run jobagent auth status
pixi run jobagent apply-assist APPLICATION_ID
```

Browser assist opens a supervised browser, reuses saved auth state where available, follows Apply redirects when possible, detects ATS/form fields, and stops before final submission. You must review and submit manually.

When importing from a local text file, `--source-url` is required for browser assist unless the file contains a source URL header. The app can read these headers automatically:

```text
Source: Indeed

Source URL:
https://uk.indeed.com/viewjob?jk=51baa25edf955295&from=shareddesktop_copy

Company:
CGI

Role:
Software Engineers / Software Developer

Location:
United Kingdom
```

You can fix older jobs without editing SQLite:

```bash
pixi run jobagent set-source-url JOB_ID "https://uk.indeed.com/viewjob?jk=..." --source indeed
```

Useful tracking commands:

```bash
pixi run jobagent list
pixi run jobagent status APPLICATION_ID needs_review
pixi run jobagent mark-submitted APPLICATION_ID
pixi run jobagent follow-up-email APPLICATION_ID
pixi run jobagent interview-prep APPLICATION_ID
pixi run jobagent daily-summary
```

## Dashboard

```bash
pixi run serve
```

Open `http://localhost:8000`.

## Development Commands

```bash
pixi run test
pixi run lint
pixi run typecheck
```

## Safety Rules

- Never store user passwords.
- Never bypass CAPTCHA, 2FA, or rate limits.
- Never scrape LinkedIn or Indeed at scale.
- Never fabricate skills, education, experience, dates, salary, visa status, or work authorization.
- Never auto-submit applications or click final submit buttons.
- Always keep browser assist supervised.
- Always require manual confirmation before sensitive data is used.
