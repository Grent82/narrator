# Beads Workflow Guide for Agents

## Overview

This project uses **Beads** - an AI-native issue tracking system that lives directly in the codebase. Issues are stored in a Dolt database at `.beads/` and integrate seamlessly with git commits.

## Configuration

| Setting | Value |
|---------|-------|
| **Database Type** | Dolt (embedded) |
| **Issue Prefix** | `narrator` |
| **Issue Format** | `narrator-<hash>` (e.g., `narrator-a3f2dd`) |
| **Location** | `.beads/` directory |

## Basic Workflow

### 1. Create an Issue

Before starting work on anything non-trivial, create an issue:

```bash
bd create "Clear description of what needs to be done"
```

For complex tasks, add more detail:

```bash
bd create "Add user authentication" --body "Implement JWT auth with refresh tokens. Include:
- Login endpoint
- Token validation middleware
- User session management"
```

### 2. Claim and Work on an Issue

```bash
# Claim the issue (marks as in-progress)
bd update <issue-id> --claim

# Work on the issue...
# Make commits (issues auto-sync with commits)
```

### 3. Complete the Issue

```bash
# Mark as done
bd update <issue-id> --status done

# Or close with a note
bd update <issue-id> --close "Implemented and tested"
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `bd create "title"` | Create new issue |
| `bd list` | List all issues |
| `bd show <id>` | View issue details |
| `bd update <id> --claim` | Claim issue (in-progress) |
| `bd update <id> --status done` | Mark complete |
| `bd close <id>` | Close issue |
| `bd stats` | Show project statistics |
| `bd dolt push` | Sync with remote |

## Agent Guidelines

### When to Create Issues

Create a beads issue when:
- Starting a new feature implementation
- Investigating a bug
- Refactoring significant code
- Any task that spans multiple steps or files

### When to Skip Issues

Skip creating issues for:
- Single-line fixes (typos, obvious bugs)
- Quick exploratory questions
- Tasks that are part of another issue

### Best Practices

1. **One Issue Per Task**: Keep issues focused and atomic
2. **Clear Descriptions**: Include context, acceptance criteria, and any constraints
3. **Claim Before Working**: Use `--claim` to mark in-progress
4. **Close When Done**: Always mark issues complete after finishing
5. **Link Related Issues**: Use `bd dep` to add dependencies between issues

## Integration with This Project

Beads is integrated into:
- `.claude/settings.json` - Enabled via hooks
- `CLAUDE.md` - Referenced in agent workflow
- Git hooks - Auto-syncs with commits

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `bd` command not found | Run `brew install beads` or check installation |
| Database errors | Run `bd init` to reinitialize |
| Can't see issues | Run `bd list` to verify database is accessible |

## Learn More

- **Beads GitHub**: https://github.com/steveyegge/beads
- **Quick Start**: Run `bd quickstart`
- **Full Docs**: https://github.com/steveyegge/beads/docs

---

*This guide is available to all agents via the beads-workflow skill.*
