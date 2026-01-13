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
| **Mode** | Batch processing with preview table before creation |
| **Duration** | ~2-3 minutes for 5-10 feedback items |

## Agent Behavior Contract

When this skill is invoked, you MUST:

1. **Never assume context** - Always fetch teams, projects, and labels dynamically from Linear
2. **Preview before creating** - Show a formatted table of all parsed issues for user confirmation
3. **Use existing labels only** - Never create new labels; only match to fetched labels
4. **Default to Backlog** - New issues start in "Backlog" or "Todo" state unless specified
5. **Batch process** - Parse all feedback items together, then create all at once
6. **Preserve user voice** - Keep original feedback wording in descriptions

## Process

### Phase 1: Input Collection

**Objective:** Gather feedback, platform context, and determine target location in Linear.

**Steps:**
1. Prompt user for feedback text (support multi-line, multiple items)
2. Use `mcp__plugin_linear_linear__list_teams` to fetch available teams
3. Use `AskUserQuestion` to ask user to select target team
   - Present team names and descriptions
   - Single selection required
4. Use `mcp__plugin_linear_linear__list_projects` filtered by team
5. Use `AskUserQuestion` to ask user to select target project
   - Present project names
   - Include "None/Backlog" option
   - Single selection
6. Use `AskUserQuestion` to ask: "What platform(s) does this feedback relate to?"
   - Options: iOS, Android, Web, Backend/API, Multiple/All platforms
   - Single selection
7. Use `mcp__plugin_linear_linear__list_issue_labels` for the selected team
8. Store available labels and platform context for parsing
9. Use `AskUserQuestion` to ask: "Do you have any images, videos, or links to include?"
   - Options:
     - "No media" (description: Continue without attachments)
     - "Add URLs" (description: Provide image/video/reference URLs)
   - If "Add URLs" selected:
     - Prompt for multiple URLs (one per line or comma-separated)
     - For each URL, ask for optional title/description
     - Support: screenshot URLs, video recordings, reference links

**Inputs:** User feedback text, team selection, optional project, platform context
**Outputs:** Validated team/project, platform context, available labels list
**Verification:** Confirm team and project IDs are valid

---

### Phase 2: AI Parsing (Batch)

**Objective:** Extract structured issue data from raw feedback using AI.

**Steps:**
1. Split feedback into individual items (by line breaks, blank lines, or numbered lists)
2. For each feedback item, extract:
   - **Title**: Imperative, actionable, <80 chars
   - **Description**: Original feedback + context (markdown formatted)
   - **Labels**: Semantically match to fetched labels (see guidelines below)
   - **Priority**: 0-4 based on urgency signals (default: 0)
   - **Acceptance Criteria**: 3-5 testable items in markdown checklist format
   - **Estimate**: XS/S/M/L/XL complexity
   - **Links**: Extract and structure URLs
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
- Priority 3 (Normal): "should", "would be nice"
- Priority 4 (Low): "minor", "eventually", "nice to have"
- Default: 0 (No priority)

**Acceptance Criteria Format:**
```markdown
## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

**Inputs:** Feedback items, available labels
**Outputs:** Structured issue data for each feedback item
**Verification:** All items have title, description, valid labels

---

### Phase 3: Creation & Confirmation

**Objective:** Preview parsed issues and create them in Linear.

**Steps:**
1. Display preview table with columns: Title, Labels, Priority, Estimate, Links
2. Show first 100 chars of description for each
3. For Links column: show count (e.g., "3 links") or first URL with title if single
4. Use `AskUserQuestion` to ask: "Create these N issues?"
   - Options:
     - "Yes, create all" (description: Creates all issues as shown)
     - "Edit first" (description: Modify fields before creating)
     - "Cancel" (description: Discard and start over)
5. If "Yes, create all":
   - For each parsed issue, call `mcp__plugin_linear_linear__create_issue`
   - Include: title, team, project (if set), labels, priority, description (with AC), links (if any)
     - links format: `[{url: string, title: string}]`
6. If "Edit first":
   - Use `AskUserQuestion` to ask which field(s) to modify (Title, Labels, Priority, Description, Estimate, Links)
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
- [ ] Links formatted as [{url, title}] if present
- [ ] Auto-detected URLs extracted from feedback text
- [ ] User-provided URLs merged with auto-detected (no duplicates)
- [ ] Links count shown in preview table

## Extension Points

This skill can be extended to:
1. **Custom parsing rules** - Add domain-specific keyword matching in references
2. **Template support** - Pre-fill description templates based on issue type
3. **Assignee inference** - Auto-assign based on feedback source or label
4. **Duplicate detection** - Check for similar existing issues before creating
5. **Export preview** - Save parsed issues to CSV before Linear creation

## References

See `references/ai-parsing-guidelines.md` for detailed semantic matching rules and examples.
