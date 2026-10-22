# Job Agent POC — Prompt & Macro Architecture

## 1. Improved prompt (spec)

> Build a **local, single-user** service that discovers jobs on LinkedIn, scores them against my profile, applies to good matches via Easy Apply **after my approval (or under strict auto-rules)**, reports results, and learns from outcomes to improve matching.
>
> **Inputs**
> - `profile.yaml`: master CV facts, skills, years of experience, target titles, seniority, locations/remote, salary floor, visa/work-auth, deal-breakers (industries, companies, keywords), screening-question answers bank.
> - `search.yaml`: keywords, filters (date posted, Easy Apply only, remote, experience level), max results per run.
> - Base CV (PDF + structured JSON).
>
> **Pipeline** — `Auth → Discover → Extract → Dedupe → Score → Decide → Apply → Report → Learn`
>
> **Requirements**
> 1. **Auth**: I log in manually once in a headed browser (incl. 2FA/CAPTCHA); the service persists the browser session (cookies) and re-uses it. No credentials stored in code; secrets in `.env`.
> 2. **Discover**: run saved searches, paginate, collect job URLs + IDs. Human-like pacing, hard daily caps (e.g. ≤25 applications, ≤150 job views/day), randomized delays, run only in working hours.
> 3. **Extract**: title, company, location, posted date, description, Easy Apply flag, seniority, salary, applicant count → normalized JSON in SQLite.
> 4. **Dedupe/Filter**: skip already seen/applied, blacklisted companies, hard-filter deal-breakers *before* spending LLM tokens.
> 5. **Score** (0–100): LLM returns structured JSON `{score, must_have_met[], missing[], red_flags[], rationale}`, plus cheap embedding/keyword pre-score. Cache by job ID + profile version.
> 6. **Decide**: `score ≥ apply_threshold` → queue; `review_threshold ≤ score < apply_threshold` → needs my approval; else skip. Default mode is **dry-run / approve-each**.
> 7. **Apply** (Easy Apply only): fill form from profile + answers bank; for unknown questions → pause and ask me (never fabricate experience, never guess legal/visa/salary answers); optional tailored CV/cover letter per job (truthful reordering/emphasis only, no invented claims). Screenshot every submission.
> 8. **Report**: daily Markdown/HTML report — jobs scanned, scored, applied, skipped (with reason), failures, top missing skills, score distribution, application funnel (applied → viewed → reply → interview).
> 9. **Improve matching**: (a) feedback loop — I mark jobs 👍/👎 and record outcomes; (b) aggregate common `missing` skills → suggest CV/profile edits; (c) tune weights/thresholds and prompt versions; (d) offline eval set of labeled jobs to measure precision@k before changing the scorer.
> 10. **Safety/ops**: kill-switch file, stop on CAPTCHA/“unusual activity”/rate-limit signals, structured logs, idempotent re-runs, config-driven, tests with recorded HTML fixtures.
>
> **Non-goals (POC)**: multi-user, cloud hosting, non-Easy-Apply sites, bypassing CAPTCHA/anti-bot, scraping other people’s profiles.
>
> **Success criteria**: end-to-end dry run on 50 jobs; ≥80% agreement between score and my manual 👍/👎 on a 30-job labeled set; zero duplicate applications; report generated each run.

### Added basics (not in the original ask)
Dedupe store · dry-run/approval mode · rate limits & caps · answers bank · deal-breaker filters · application tracking & funnel · screenshots/audit log · kill-switch · config files · scheduler · labeled eval set · cost tracking (LLM tokens/run).

### ⚠️ Risk to accept knowingly
LinkedIn's User Agreement prohibits automated access/bots, even with Premium. Account restriction or ban is a real possibility. The design mitigates this (own session, low volume, human pacing, stop-on-challenge, human-in-the-loop) but cannot eliminate it. Use a non-critical account if possible, or keep the Apply step manual and automate only Discover→Score→Report (zero-risk-ish fallback: use job-alert emails/RSS instead of browsing).

---

## 2. Macro architecture

```
                        ┌──────────────────────────────┐
  profile.yaml ───────► │          Config / Profile     │ ◄── search.yaml
  base CV, answers      └──────────────┬───────────────┘
                                       │
┌───────────┐   ┌─────────────┐   ┌────▼──────┐   ┌───────────┐   ┌──────────┐
│ Scheduler │──►│ Orchestrator│──►│ Discovery │──►│ Extractor │──►│  Store   │
│ (cron/CLI)│   │ (pipeline)  │   │ (browser) │   │ (parse)   │   │ (SQLite) │
└───────────┘   └──────┬──────┘   └─────▲─────┘   └───────────┘   └────┬─────┘
                       │                │ session                      │
                       │         ┌──────┴──────┐                       │
                       │         │ Auth/Session│ manual login, cookies │
                       │         └─────────────┘                       │
                       │                                               │
                ┌──────▼──────┐   ┌───────────┐   ┌────────────┐       │
                │   Matcher   │──►│  Decider  │──►│   Applier  │◄──────┤
                │ (filters +  │   │ thresholds│   │ Easy Apply │       │
                │  LLM score) │   │ + approval│   │ + Q&A bank │       │
                └──────▲──────┘   └─────┬─────┘   └─────┬──────┘       │
                       │                │ ask me        │ results      │
                       │          ┌─────▼─────┐         ▼              │
                       │          │ Review UI │   ┌───────────┐        │
                       │          │ (CLI/web) │   │  Reporter │◄───────┘
                       │          └─────┬─────┘   └─────┬─────┘
                       │   labels/outcomes│              │ report.md/html
                ┌──────┴──────────────────▼──┐           ▼
                │  Learning / Tuning loop    │◄──── funnel + gaps analysis
                │  (prompt & weight versions,│
                │   eval set, CV suggestions)│
                └────────────────────────────┘
```

### Components

| # | Component | Responsibility | POC tech |
|---|-----------|----------------|----------|
| 1 | Config/Profile | Typed, versioned profile + search config | YAML + pydantic |
| 2 | Auth/Session | Persistent logged-in browser context; detect logout/challenge | Playwright persistent context |
| 3 | Discovery | Run searches, paginate, throttle, enforce caps | Playwright |
| 4 | Extractor | Page → normalized job JSON | Playwright + selectors, fixtures for tests |
| 5 | Store | Jobs, scores, applications, events, labels, prompt versions | SQLite |
| 6 | Matcher | Hard filters → keyword/embedding pre-score → LLM structured score | Claude API w/ JSON schema, cached |
| 7 | Decider | Threshold policy, approve/auto/skip, daily caps | Pure Python |
| 8 | Review UI | Approve/reject, answer unknown questions, 👍/👎 | CLI first, tiny web later |
| 9 | Applier | Fill Easy Apply, answers bank, attach CV, screenshot, record | Playwright |
| 10 | Reporter | Run + trend reports, funnel, top missing skills | Jinja → MD/HTML |
| 11 | Learning loop | Use labels/outcomes to tune weights/prompts, propose CV edits, eval precision@k | Scripts + eval set |
| 12 | Orchestrator/Scheduler | Idempotent stages, retries, kill-switch, logging | CLI (`typer`) + cron |

### Data model (core tables)
`jobs(id, url, title, company, desc, easy_apply, posted_at, raw_hash)` ·
`scores(job_id, profile_ver, prompt_ver, score, json)` ·
`applications(job_id, status, applied_at, cv_version, screenshot, error)` ·
`labels(job_id, thumb, source)` · `outcomes(job_id, stage, at)` ·
`runs(id, started, stats_json)`

### Job state machine
`discovered → extracted → filtered_out | scored → skipped | needs_review | queued → applied | failed | needs_input → (viewed | replied | interview | rejected)`

### Matching-score improvement loop
1. Baseline scorer + labeled set (≈30–50 jobs I rate).
2. Measure agreement/precision@k per prompt/weights version.
3. Mine `missing[]` across jobs → rank skill gaps → CV wording or learning suggestions.
4. Adjust search queries from high-score job titles/keywords.
5. Track outcome rates per score bucket; recalibrate thresholds.
6. Only promote a new prompt version if eval metrics improve.

### Suggested repo layout
```
src/jobagent/{config,auth,discovery,extract,store,match,decide,apply,report,learn,cli}.py
config/{profile.yaml,search.yaml,answers.yaml}
data/{jobs.db,screenshots/,reports/}
tests/{fixtures/,eval/labeled_jobs.jsonl}
```

### POC milestones
1. **M1** Auth + Discovery + Extract → SQLite (no apply).
2. **M2** Matcher + Reporter (read-only, fully safe) + labeling CLI.
3. **M3** Learning loop / eval harness.
4. **M4** Applier in dry-run, then approve-each, then capped auto mode.
