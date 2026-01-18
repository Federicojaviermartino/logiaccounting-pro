# LogiAccounting Pro - Agent Skills Index

Auto-generated skill and agent documentation.

## Available Skills

| Skill | Description | Usage |
|-------|-------------|-------|
| `$backend` | FastAPI backend development patterns | Route creation, auth, stores |
| `$frontend` | React component patterns | Pages, state, API integration |
| `$deployment` | Render deployment guide | Configuration, env vars |
| `$testing` | Test patterns and commands | pytest, curl, Jest |
| `$data-analysis` | Report generation patterns | Queries, charts |

## Available Subagents

| Agent | Description | Model |
|-------|-------------|-------|
| `@code-reviewer` | Reviews code for quality and security | sonnet |
| `@api-designer` | Designs RESTful API endpoints | sonnet |
| `@test-writer` | Writes backend and frontend tests | sonnet |
| `@debugger` | Diagnoses and fixes bugs | opus |

## Usage Examples

### Invoking Skills
```
$backend    # Load backend development patterns
$frontend   # Load React component patterns
```

### Invoking Subagents
```
@code-reviewer review the auth module
@test-writer write tests for payments
@debugger why is the login failing?
```

### Combining Skills + Agents
```
@api-designer with $backend skill, design endpoints for invoices
```

## Directory Structure

```
logiaccounting-pro/
├── skills/
│   ├── backend/SKILL.md      # FastAPI patterns
│   ├── frontend/SKILL.md     # React patterns
│   ├── deployment/SKILL.md   # Render deployment
│   ├── testing/SKILL.md      # Test patterns
│   └── data-analysis/SKILL.md # Reports
└── .claude/
    └── agents/
        ├── code-reviewer.md  # Code review
        ├── api-designer.md   # API design
        ├── test-writer.md    # Test writing
        └── debugger.md       # Bug fixing
```
