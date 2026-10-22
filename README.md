# Job Interview Company Analysis Tool

Research and prepare for job interviews with targeted company analysis and hard-hitting questions.

## Quick Start

Use the `/job-interview-company-research` skill to analyze any company:

```
/job-interview-company-research [company-name-or-description]
```

## Project Structure

```
job-analyze-tool/
├── README.md                          # This file
├── companies/                         # Company analysis documents
│   └── [company-name]/
│       ├── analysis.md               # Full research & questions
│       ├── red-flags.md              # Warning signs
│       └── notes.md                  # Personal observations
└── templates/
    └── company-analysis-template.md   # Use as a starting point
```

## Workflow

1. **Gather Intel** — Company name, funding, founders, product, market
2. **Research** — Web search, founder backgrounds, customer validation
3. **Analyze** — Compare claims vs. reality
4. **Generate Questions** — Targeted by topic (founders, PMF, moat, burn, culture, role)
5. **Prepare** — Know your red flags and success criteria
6. **Interview** — Ask naturally, listen for gaps

## Key Questions by Topic

### Founders & Leadership
- Tell me about a time you strongly disagreed. How did you resolve it?
- What's the biggest mistake you've made as a founder?

### Product-Market Fit
- Who are your top 3 customers? Can I speak with them?
- What's your net revenue retention?

### Competitive Moat
- How is your approach different from [competitor]?
- What would take to replace you?

### Burn & Runway
- What's your monthly burn and runway?
- Path to profitability?

### Culture & Team
- How has the team changed since Series A? Who left?
- What's the biggest frustration working here?

### Role-Specific
- What does success look like in 6 and 18 months?
- What's the biggest bottleneck this role solves?

## Red Flags

⚠️ Vague or rehearsed answers  
⚠️ No concrete customers to name  
⚠️ Founder conflict  
⚠️ Runway concerns relative to burn  
⚠️ High turnover  
⚠️ Claims seem exaggerated  

## Success Criteria

✅ 20-30 targeted questions (specific, not generic)  
✅ At least 3 key claims validated  
✅ Understand real competitive landscape  
✅ Know burn rate & runway  
✅ Have questions for each interview stage

## Files in This Project

- `companies/adaptive6/analysis.md` — Example: Adaptive6 analysis
- `templates/company-analysis-template.md` — Start here for new companies
- `docs/job-agent-poc.md` — LinkedIn job-agent POC: improved prompt + macro architecture

## Job agent (POC, milestone 1)

See `docs/job-agent-poc.md`. Milestone 1 ingests LinkedIn job-alert emails into SQLite.

```
pip install -e '.[dev]'          # add ,gmail / ,browser extras as needed
cp config/search.example.yaml config/search.yaml
jobagent ingest-file tests/fixtures/linkedin_alert.html   # offline demo
jobagent ingest-alerts           # Gmail (read-only OAuth, needs config/gmail_client.json)
jobagent login && jobagent fetch # manual login once; capped description fetch
jobagent status
pytest
```
Create `data/STOP` to halt all runs (kill-switch).
