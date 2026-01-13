---
name: feedback-to-linear
description: Transform user feedback into structured Linear issues with AI-enhanced parsing for labels, priority, acceptance criteria, and estimates
license: MIT
---

# Feedback to Linear

Transform raw user feedback text into structured Linear issues with intelligent AI parsing.

## Triggers

Activate this skill with any of these phrases:
- "Convert this feedback to Linear issues"
- "Create issues from user feedback"
- "feedback-to-linear"
- "Parse feedback for Linear"
- "Transform feedback into Linear"

## Quick Reference

| Aspect | Details |
|--------|---------|
| **Input** | Raw feedback text (batch) + team/project selection + optional media URLs |
| **Output** | Linear issues with AI-parsed metadata (title, labels, priority, acceptance criteria, estimates, links) |
| **Workspace** | Uses workspace from configured Linear API key |
| **Mode** | Batch processing with preview table before creation |
| **Duration** | ~2-3 minutes for 5-10 feedback items |

## Agent Behavior Contract

When this skill is invoked, you MUST:

1. **Never assume context** - Always fetch teams, projects, and labels dynamically from Linear
2. **Single workspace** - Issues are created in the workspace associated with the Linear MCP plugin's API key
3. **Preview before creating** - Show a formatted table of all parsed issues for user confirmation
4. **Use existing labels only** - Never create new labels; only match to fetched labels
5. **Default to Backlog** - New issues start in "Backlog" or "Todo" state unless specified
6. **Batch process** - Parse all feedback items together, then create all at once
7. **Preserve user voice** - Keep original feedback wording in descriptions

## Process

### Phase 1: Input Collection

**Objective:** Gather feedback, platform context, and determine target location in Linear.

**Steps:**
1. Prompt user for feedback text (support multi-line, multiple items)
2. Check if current directory is a git repo (`git rev-parse --git-dir`)
3. If in a git repo, use `AskUserQuestion` to ask:
   - **Question**: "Use context from current repository?"
   - **Options**:
     - "Yes" (description: "Add project name, platform, and repo info to issues")
     - "No" (description: "Create issues without repo context")
4. If user selects "Yes":
   - Detect project name from `package.json`, `Cargo.toml`, `pyproject.toml`, or git remote
   - Detect platform from project structure (ios/, android/, package.json dependencies, etc.)
   - Store repo context for later enrichment
5. **CRITICAL**: Use `MCPSearch` tool to load each MCP tool BEFORE calling it. For example:
   - Call `MCPSearch` with query `"select:mcp__plugin_linear_linear__list_teams"`
   - Wait for it to return successfully
   - Then call `mcp__plugin_linear_linear__list_teams`
   - Repeat this pattern for ALL MCP tools: search first, then call
6. Use `mcp__plugin_linear_linear__list_teams` to fetch available teams (after loading via MCPSearch)
7. Use `AskUserQuestion` with 2 questions:
   - **Team**: "Which team should these issues go to?"
     - Present team names and descriptions
     - If repo context detected, highlight matching team/project name
     - Single selection required
   - **Platform**: "What platform(s) does this feedback relate to?"
     - Options: iOS, Android, Web, Backend/API, Multiple/All platforms
     - If repo context detected platform, set as default selection
     - Single selection
8. Load and use `mcp__plugin_linear_linear__list_projects` (MCPSearch first, then call) filtered by selected team
9. Load and use `mcp__plugin_linear_linear__list_issue_labels` (MCPSearch first, then call) for selected team
10. Use `AskUserQuestion` with 2 questions:
   - **Project**: "Which project should these issues go to? (optional)"
     - Present project names
     - If repo context detected, highlight matching project name
     - Include "None/Backlog" option
     - Single selection
   - **Media**: "Any images, videos, or links to add?"
     - Options:
       - "No media" (description: Continue without attachments)
       - "Add URLs" (description: Provide image/video/reference URLs)
     - Single selection
11. If "Add URLs" selected in step 10:
   - Prompt for multiple URLs (one per line or comma-separated)
   - For each URL, ask for optional title/description
   - Support: screenshot URLs, video recordings, reference links
12. Store available labels, platform context, and repo context for parsing

**Inputs:** User feedback text, team selection, optional project, platform context, optional repo context
**Outputs:** Validated team/project, platform context, available labels list, repo context (if enabled)
**Verification:** Confirm team and project IDs are valid

---

### Phase 2: AI Parsing (Batch)

**Objective:** Extract structured issue data from raw feedback using AI.

**Steps:**
1. Split feedback into individual items (by line breaks, blank lines, or numbered lists)
2. For each feedback item, extract:
   - **Title**: Imperative, actionable, <80 chars
   - **Description**: Original feedback + context + estimate note (markdown formatted)
   - **Labels**: Semantically match to fetched labels (see guidelines below)
   - **Priority**: 0-4 based on urgency signals (default: 0)
   - **Acceptance Criteria**: 3-5 testable items in markdown checklist format
   - **Estimate**: XS/S/M/L/XL complexity (appended to description, not passed to API)
   - **Confidence**: HIGH/MEDIUM/LOW for each field (see guidelines)
   - **Links**: Extract and structure URLs (embedded in description markdown)
     - Auto-detect http/https URLs in feedback text using regex patterns
     - Identify URL type: image (.png, .jpg, .jpeg, .gif, .webp), video (.mp4, .mov, .avi, .loom.com, .vimeo.com, .youtube.com), screenshot service (d.pr, cloudapp, droplr, cl.ly), or reference
     - Extract context around URLs for title generation (e.g., "screenshot showing crash", "video reproduction of bug")
     - Merge with user-provided URLs from Phase 1 step 9
     - For user-provided URLs: accept one URL per line or comma-separated, with optional title in parentheses or after a colon
     - Remove duplicate URLs (case-insensitive URL comparison)
     - Preserve user-provided titles over auto-generated ones
     - Format as: `[{url: "https://...", title: "Description"}]`

**Label Matching Guidelines:**
- Present AI with the list of available labels fetched in Phase 1
- Match based on semantic similarity to label names
- Common patterns:
  - Bug-like: "crash", "error", "broken", "doesn't work" → match "Bug", "Defect", etc.
  - Feature-like: "add", "new", "would love", "wish" → match "Feature", "Enhancement", etc.
  - Improvement-like: "better", "improve", "slow", "optimize" → match "Improvement", "Performance", etc.
  - Platform: "iOS", "Android", "mobile", "backend", "web" → match platform labels
- If no confident match (>70% similarity), leave labels empty

**Title Convention:**
- When platform is selected (not "Multiple/All platforms"), prefix title with `[Platform]`
- Format: `[iOS] Fix crash when uploading images`
- Multi-platform issues: No prefix, add platform labels instead
- Examples:
  - iOS selected → "[iOS] Add dark mode support"
  - Android selected → "[Android] Fix navigation bug"
  - Multiple/All → "Fix authentication issue" (no prefix)

**Priority Detection:**
- Priority 1 (Urgent): "crash", "broken", "urgent", "ASAP", "critical", "down"
- Priority 2 (High): "important", "soon", "blocking", "serious"
- Priority 3 (Medium): "should", "would be nice"
- Priority 4 (Low): "minor", "eventually", "nice to have"
- Default: 0 (No priority)

**Confidence Scoring:**
Assign confidence level (HIGH/MEDIUM/LOW) for each parsed field:

| Field | HIGH | MEDIUM | LOW |
|-------|------|--------|-----|
| Title | Clear action verb, specific issue | Transformed from vague description | Very vague, needs clarification |
| Labels | Exact keyword match | Semantic match | Inferred/guessed |
| Priority | Explicit keyword present | Contextual signals | Defaulted to 0 |
| Estimate | - | All estimates (heuristic-based) | - |

**Low Confidence Handling:**
- Add `[?]` suffix to titles with LOW confidence
- Flag items in preview for user review
- Store confidence score for each field (used in preview table)

**Description Format with Estimate:**
```markdown
[Original user feedback, quoted or paraphrased]

## Context
[Any inferred or explicit context]
[If repo context enabled: Source repo: {project_name} ({repo_url})]

**Complexity Estimate:** M (Medium)

## Links
- [Screenshot showing crash](https://d.pr/abc123)
- [Video reproduction](https://loom.com/share/xyz)
[If file paths detected and repo context enabled:
- [src/Header.tsx](https://github.com/user/repo/blob/main/src/Header.tsx)]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

**Inputs:** Feedback items, available labels, repo context (if enabled)
**Outputs:** Structured issue data for each feedback item with confidence scores
**Verification:** All items have title, description, valid labels, confidence scores

---

### Phase 3: Creation & Confirmation

**Objective:** Preview parsed issues and create them in Linear.

**Steps:**
1. Display preview table with columns: Title, Labels, Priority, Estimate, Confidence
2. Show first 100 chars of description for each
3. Highlight rows with LOW confidence (e.g., with a warning icon or note)
4. Use `AskUserQuestion` to ask: "Create these N issues?"
   - Options:
     - "Yes, create all" (description: Creates all issues as shown)
     - "Edit first" (description: Modify fields before creating)
     - "Cancel" (description: Discard and start over)
5. If "Yes, create all":
   - Load `mcp__plugin_linear_linear__create_issue` via MCPSearch first
   - For each parsed issue, call `mcp__plugin_linear_linear__create_issue`
   - Include: title, team, project (if set), labels, priority, description
     - Description contains: context (including repo context if enabled), estimate note, links (markdown formatted), and acceptance criteria
6. If "Edit first":
   - Use `AskUserQuestion` to ask which field(s) to modify (Title, Labels, Priority, Description, Estimate)
   - Re-parse with user adjustments
   - Return to step 1 (preview)
7. Collect created issue URLs
8. Display summary table with issue identifiers and URLs

**Inputs:** Parsed issue data, user confirmation
**Outputs:** Created Linear issues with URLs
**Verification:** All issues created successfully, URLs returned

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Creating labels | May not match team conventions | Use existing labels only via semantic matching |
| Hardcoding labels | Different workspaces have different labels | Fetch dynamically per team |
| Assuming workspace | API key determines workspace | Document which workspace is active |
| Skipping preview | User loses control over what's created | Always show table before creating |
| Guessing project | Wrong categorization | Ask explicitly or make optional |
| Single-item processing | Inefficient for bulk feedback | Batch parse and create |

## Verification Checklist

Before completing this skill, verify:
- [ ] All issues created with valid team assignment
- [ ] Labels match existing workspace labels (no new labels created)
- [ ] User confirmed before creation
- [ ] Summary with issue URLs provided
- [ ] Acceptance criteria formatted as markdown checklist
- [ ] Priority values are 0-4 (or omitted)
- [ ] Estimate included in description as note (not passed to API)
- [ ] Confidence scores assigned to each field (HIGH/MEDIUM/LOW)
- [ ] LOW confidence items flagged with [?] in title
- [ ] Preview table includes Confidence column
- [ ] Repo context added to descriptions (if user opted in)
- [ ] Links embedded in description markdown
- [ ] Auto-detected URLs extracted from feedback text
- [ ] User-provided URLs merged with auto-detected (no duplicates)
- [ ] File paths validated and linked (if repo context enabled)

## Extension Points

This skill can be extended to:
1. **Custom parsing rules** - Add domain-specific keyword matching in references
2. **Template support** - Pre-fill description templates based on issue type
3. **Assignee inference** - Auto-assign based on feedback source or label
4. **Duplicate detection** - Check for similar existing issues before creating
5. **Export preview** - Save parsed issues to CSV before Linear creation

## References

See `references/ai-parsing-guidelines.md` for detailed semantic matching rules and examples.
