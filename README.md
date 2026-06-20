# Agentic Application Manager

Local, supervised job application assistant for preparing tailored application packages from an approved LaTeX CV.

This project is intentionally a human-approved assistant, not an unattended mass-application bot. It must not bypass CAPTCHA, rate limits, assessments, or platform restrictions, and it must never submit applications without explicit user approval.

## Setup

Use Pixi for all package and task management:

```bash
pixi install
pixi run jobagent init
```

Optional: put your draft/current CV and supporting material in `drafts/`. Import the approved LaTeX CV when ready:

```bash
pixi run jobagent import-cv drafts/cv.tex
```

## MVP Workflow

```bash
pixi run jobagent add-job --file ./job.txt
pixi run jobagent prepare JOB_ID
pixi run jobagent list
pixi run jobagent show APPLICATION_ID
```

Generated application packages are stored under `storage/applications/`.

## Development Commands

```bash
pixi run test
pixi run lint
pixi run typecheck
pixi run serve
```

The FastAPI app runs with:

```bash
pixi run uvicorn app.main:app --reload
```

## Safety Rules

- Never evade platform rate limits.
- Never scrape LinkedIn or Indeed at scale.
- Never fabricate skills, education, experience, dates, or work authorization.
- Always pause before final application submission.
- Always store the generated CV and cover letter used for each application.
- Always keep the original job description.

## Current Scope

The first version implements local project setup, profile/CV import, job input, application folder generation, structured parsing, fit scoring, CV draft tailoring, optional LaTeX compilation, cover letter drafting, answer draft creation, review output, CLI commands, a small API surface, and focused tests.
