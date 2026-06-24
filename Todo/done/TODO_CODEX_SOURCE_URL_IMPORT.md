# Codex TODO — Add Source URL Support for File-Based Jobs and Prepare for App Testing

This milestone fixes the current blocker before testing the full job-agent flow.

Right now, jobs added with:

```bash
pixi run jobagent add-job --file ./job.txt
```

store the job text but do not reliably store the original job URL as `job.source_url`. Because `apply-assist` depends on `source_url`, file-based jobs cannot open the original Indeed/LinkedIn/ATS page unless the database is edited manually.

The goal of this change is to make file-based job imports preserve the original source URL cleanly.

---

## Global Goal

Allow the user to add a job from a text file while also storing the original job posting URL, source platform, and source metadata.

Example desired usage:

```bash
pixi run jobagent add-job --file ./job_indeed_cgi_software_engineers.txt --source-url "https://uk.indeed.com/viewjob?jk=51baa25edf955295&from=shareddesktop_copy"
```

Then:

```bash
pixi run jobagent jobs
pixi run jobagent prepare JOB_ID
pixi run jobagent apply-assist APPLICATION_ID
```

should work without manual database editing.

---

## Part 1 — Update `add-job` CLI Options

### Goal

Add CLI flags so file-based and text-based job imports can store the original source URL and source platform.

### Why this is being done

The browser assistant needs `job.source_url` to open the real application page. Without it, `apply-assist` cannot start from the original Indeed/LinkedIn job post.

### Tasks

[x] Update `jobagent add-job`.

[x] Add optional argument:

```bash
--source-url "https://..."
```

[x] Add optional argument:

```bash
--source indeed
```

[x] Supported source values should include:

```text
indeed
linkedin
company_site
greenhouse
lever
workday
ashby
smartrecruiters
teamtailor
workable
recruitee
bamboohr
unknown
```

[x] Example:

```bash
pixi run jobagent add-job --file ./job.txt --source-url "https://uk.indeed.com/viewjob?jk=..." --source indeed
```

[x] Example:

```bash
pixi run jobagent add-job --text "..." --source-url "https://www.linkedin.com/jobs/view/..." --source linkedin
```

[x] If `--source` is not provided, infer it from `--source-url`.

[x] If neither `--source-url` nor a URL inside the file is found, keep current behavior but show a warning:

```text
Job added without source_url. Browser assist will not work until a source URL is added.
```

---

## Part 2 — Extract `Source URL:` From Job Text Files

### Goal

Automatically read the source URL from the job text file if it contains a `Source URL:` line.

### Why this is being done

The user often stores job descriptions in text files. If the file already includes the original URL, the app should use it automatically.

### Tasks

[x] Add helper function:

```python
def extract_source_url_from_text(text: str) -> str | None:
    ...
```

[x] It should detect lines like:

```text
Source URL:
https://uk.indeed.com/viewjob?jk=51baa25edf955295&from=shareddesktop_copy
```

[x] It should also detect same-line format:

```text
Source URL: https://uk.indeed.com/viewjob?jk=51baa25edf955295&from=shareddesktop_copy
```

[x] It should also detect:

```text
URL:
https://...
```

[x] It should also detect:

```text
Original URL:
https://...
```

[x] If both a CLI `--source-url` and file URL are present, prefer the CLI value.

[x] Add helper function:

```python
def infer_source_from_url(url: str | None) -> str:
    ...
```

[x] Inference rules:

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
otherwise           -> unknown
```

---

## Part 3 — Update Job Input Service

### Goal

Make the job input service store `source_url` and `source` properly.

### Why this is being done

The database should preserve the exact source URL from the beginning of the workflow so future preparation, audit logs, and browser assist all work correctly.

### Tasks

[x] Update job input service method signatures.

[x] Suggested method signatures:

```python
def add_from_file(
    file_path: Path,
    source_url: str | None = None,
    source: str | None = None,
) -> Job:
    ...
```

```python
def add_from_text(
    text: str,
    source_url: str | None = None,
    source: str | None = None,
) -> Job:
    ...
```

[x] Store final resolved source URL in:

```python
job.source_url
```

[x] Store inferred or provided source in:

```python
job.source
```

[x] Keep `description_text` as the full job description text.

[x] Preserve existing behavior for duplicates.

[x] Make duplicate detection consider:

```text
description_hash
source_url
company + title after parsing
```

[x] If a duplicate source URL is added, show the existing job ID instead of creating a duplicate.

---

## Part 4 — Update `jobagent jobs` and `jobagent job JOB_ID`

### Goal

Make source URLs visible before preparation.

### Why this is being done

The user needs to confirm that the job was imported correctly before running `prepare` or `apply-assist`.

### Tasks

[x] Update:

```bash
pixi run jobagent jobs
```

[x] Show columns:

```text
Job ID
Company
Title
Source
Source URL
Status
Created At
Prepared?
```

[x] Truncate long URLs in the table but keep enough to identify the source.

[x] Update:

```bash
pixi run jobagent job JOB_ID
```

[x] Show full source URL.

[x] Show a warning if source URL is missing:

```text
Warning: this job has no source_url. apply-assist cannot open the job page.
```

[x] Show next recommended command:

```text
Next: pixi run jobagent prepare JOB_ID
```

---

## Part 5 — Add Optional Command to Set or Update Source URL

### Goal

Allow users to fix an imported job that has no source URL.

### Why this is being done

Some jobs may already exist in the database from older imports. The user should not need to edit SQLite manually.

### Tasks

[x] Add command:

```bash
pixi run jobagent set-source-url JOB_ID "https://..."
```

[x] It should update:

```text
job.source_url
job.source
```

[x] Infer source from URL if `--source` is not provided.

[x] Optional:

```bash
pixi run jobagent set-source-url JOB_ID "https://..." --source indeed
```

[x] After update, print:

```text
Updated Job JOB_ID source_url.
Next: pixi run jobagent prepare JOB_ID
```

---

## Part 6 — Update Application Folder Metadata

### Goal

Make sure the source URL is copied into generated application folders.

### Why this is being done

Each application package should be traceable back to the original job post.

### Tasks

[x] During `prepare`, save source URL to:

```text
00_job-posting/source_url.txt
```

[x] Save source URL in:

```text
metadata.json
```

[x] Save source platform in:

```text
metadata.json
```

[x] If `source_url` is missing, write an empty file and add a warning to:

```text
audit_log.md
```

[x] Make sure `apply-assist` reads from database first, then metadata fallback if needed.

---

## Part 7 — Tests

### Goal

Prevent regressions and confirm file-based jobs work with browser assist.

### Why this is being done

This is the blocking change before real app testing.

### Required tests

[x] Test `add-job --file --source-url`.

[x] Test `add-job --file` extracts `Source URL:` from file content.

[x] Test CLI `--source-url` overrides file `Source URL:`.

[x] Test source inference from Indeed URL.

[x] Test source inference from LinkedIn URL.

[x] Test source inference from Greenhouse/Lever/Workday URLs.

[x] Test job without source URL shows warning.

[x] Test `jobagent jobs` displays source/source URL.

[x] Test `jobagent job JOB_ID` displays full source URL.

[x] Test `set-source-url` updates existing job.

[x] Test `prepare` writes `00_job-posting/source_url.txt`.

[x] Test `metadata.json` includes source URL.

[x] Test `apply-assist` no longer fails when a file-based job has `--source-url`.

---

## Part 8 — README Update

### Goal

Document the correct workflow for testing the app.

### Why this is being done

The user needs a simple path from job text file to prepared application to browser assist.

### Tasks

[x] Update README with this workflow:

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

[x] Explain that `--source-url` is required for browser assist when importing from a local file.

[x] Explain that `Source URL:` inside the text file can be used instead of `--source-url`.

[x] Add example job text header:

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

---

## Part 9 — Manual Acceptance Checklist

### Goal

Define when this small change is complete and the app can move to testing.

### Checklist

[x] `pixi run test` passes.

[x] `pixi run jobagent doctor` passes or shows only acceptable warnings.

[x] `pixi run jobagent add-job --file ./job.txt --source-url "https://..." --source indeed` creates a job.

[x] `pixi run jobagent jobs` shows the job and source URL.

[x] `pixi run jobagent job JOB_ID` shows the full source URL.

[x] `pixi run jobagent prepare JOB_ID` creates the application package.

[x] `00_job-posting/source_url.txt` contains the original URL.

[x] `metadata.json` contains the original URL.

[x] `pixi run jobagent approve-answers APPLICATION_ID` works.

[x] `pixi run jobagent auth login indeed` works.

[x] `pixi run jobagent auth status` shows Indeed session exists.

[x] `pixi run jobagent apply-assist APPLICATION_ID` opens the original Indeed URL.

[x] Browser assist does not click final submit.

[x] First test run should end with `CANCEL`, not `SUBMITTED`.

---

## Suggested Codex Prompt

Paste this into Codex:

```text
Continue from the current job-agent GitHub state.

Implement source URL support for file-based and text-based job imports.

The blocking issue is that jobs added with `add-job --file ./job.txt` do not reliably store the original job URL in `job.source_url`, so `apply-assist` cannot open the job page later.

Add:
1. `--source-url` and `--source` options to `jobagent add-job`.
2. Automatic extraction of `Source URL:` from job text files.
3. Source inference from URL domains.
4. A command to update source URL for existing jobs.
5. Better display of source/source URL in `jobagent jobs` and `jobagent job JOB_ID`.
6. Ensure `prepare` writes source URL to `00_job-posting/source_url.txt` and `metadata.json`.
7. Tests for all of the above.
8. README instructions for testing with an Indeed job text file.

Keep the app supervised. Do not change browser assist to auto-submit anything.
```

