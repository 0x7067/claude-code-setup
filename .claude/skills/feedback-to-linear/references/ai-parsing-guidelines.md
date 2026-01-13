# AI Parsing Guidelines for Feedback to Linear

This document provides detailed guidelines for parsing raw user feedback into structured Linear issue data.

## Overview

The parsing process extracts six key components from each feedback item:
1. Title
2. Description
3. Labels
4. Priority
5. Acceptance Criteria
6. Estimate

## 1. Title Extraction

### Rules
- **Format**: Imperative mood (e.g., "Fix crash on upload", not "The app crashes")
- **Length**: Maximum 80 characters
- **Clarity**: Should stand alone without context
- **Actionable**: Start with verb when possible

### Examples

| Raw Feedback | Extracted Title |
|--------------|----------------|
| "The app crashes when I try to upload large images" | Fix crash when uploading large images |
| "Would love to see dark mode support" | Add dark mode support |
| "Loading times are really slow on mobile" | Improve loading times on mobile |
| "Can't find the settings button anywhere" | Make settings button more discoverable |

### Platform Prefix Convention

When a specific platform is selected during input collection:
- Prefix the title with `[Platform]`
- Examples:

| Platform | Raw Title | Final Title |
|----------|-----------|-------------|
| iOS | Fix crash on upload | [iOS] Fix crash on upload |
| Android | Add dark mode | [Android] Add dark mode |
| Web | Improve loading | [Web] Improve loading |
| Backend/API | Optimize query | [Backend] Optimize query |
| Multiple/All | Fix auth bug | Fix auth bug (no prefix) |

### Edge Cases
- **Vague feedback**: "This is broken" → "Fix reported issue [needs details]"
- **Multiple issues in one**: Split into separate feedback items first
- **Feature requests without verbs**: Add appropriate verb (Add, Support, Enable, etc.)

---

## 2. Description Generation

### Structure
```markdown
[Original user feedback, quoted or paraphrased]

## Context
[Any inferred or explicit context]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

### Rules
- Preserve user's original wording when quoting feedback
- Add "Reported by: [source]" if source is known
- Include any environmental details mentioned (device, OS, version)
- Format code snippets with proper markdown
- Add links if URLs were mentioned

### Example
**Input:** "App crashes when uploading images over 10MB on iPhone 14"

**Output:**
```markdown
User reported: "App crashes when uploading images over 10MB on iPhone 14"

## Context
- Device: iPhone 14
- Issue occurs specifically with large images (>10MB)
- Crash happens during upload process

## Acceptance Criteria
- [ ] Large images (>10MB) upload without crashing
- [ ] User receives clear feedback during upload
- [ ] Error handling prevents app crash
- [ ] Tested on iPhone 14 and similar devices
```

---

## 3. Label Semantic Matching

### Process
1. Receive list of available labels from Linear team
2. Analyze feedback content and extract keywords
3. Match keywords to label names using semantic similarity
4. Apply labels with >70% confidence match
5. Support multiple labels per issue

### Label Category Patterns

#### Bug Detection
**Keywords:** crash, error, broken, doesn't work, fails, bug, issue, problem, wrong, incorrect

**Match to labels like:** Bug, Defect, Issue, Problem, Broken

**Example:**
- Feedback: "Upload button doesn't work" → Label: "Bug"

#### Feature Detection
**Keywords:** add, new, would love, wish, could we, want, need, feature, support

**Match to labels like:** Feature, Enhancement, New Feature, Feature Request

**Example:**
- Feedback: "Would love dark mode" → Label: "Feature"

#### Improvement Detection
**Keywords:** better, improve, enhance, slow, faster, optimize, performance, UX

**Match to labels like:** Improvement, Enhancement, Performance, UX, Optimization

**Example:**
- Feedback: "Loading is too slow" → Label: "Performance" or "Improvement"

#### Platform Detection
**Keywords:** iOS, iPhone, iPad, Android, mobile, web, desktop, backend, API, server

**Match to labels like:** iOS, Android, Mobile, Web, Backend, API

**Example:**
- Feedback: "Crash on iPhone 14" → Labels: "Bug", "iOS"

#### Domain-Specific Labels
Look for mentions of specific features or modules and match to corresponding labels:
- "login", "auth", "signup" → "Authentication"
- "payment", "checkout" → "Payments"
- "notification", "push" → "Notifications"

### Multi-Label Strategy
Apply multiple labels when appropriate:
- Type label (Bug/Feature/Improvement) + Platform label (iOS/Android)
- Type label + Domain label (Bug + Authentication)
- Maximum 3-4 labels per issue for clarity

### No Match Handling
If no label achieves >70% confidence:
- Leave labels empty
- User can add manually in preview
- Log the missed match for future improvement

---

## 4. Priority Inference

### Priority Scale
- **0**: No priority (default)
- **1**: Urgent
- **2**: High
- **3**: Normal
- **4**: Low

### Detection Rules

#### Priority 1 (Urgent)
**Keywords:** crash, critical, urgent, ASAP, emergency, down, broken, blocker, can't use

**Context signals:**
- User reports app is unusable
- Revenue-impacting issues
- Security vulnerabilities
- ALL CAPS or multiple exclamation marks

**Example:** "APP CRASHES IMMEDIATELY ON LAUNCH!!!"

#### Priority 2 (High)
**Keywords:** important, soon, blocking, serious, major, significant, impacts many

**Context signals:**
- Affects core functionality
- Mentioned deadline or time constraint
- Many users affected

**Example:** "Login doesn't work for new users - blocking onboarding"

#### Priority 3 (Normal)
**Keywords:** should, would be good, normal, standard, regular

**Context signals:**
- Improvement to existing functionality
- Minor bugs with workarounds
- Standard feature requests

**Example:** "Would be nice to have better error messages"

#### Priority 4 (Low)
**Keywords:** minor, eventually, nice to have, small, trivial, cosmetic

**Context signals:**
- Polish or cosmetic issues
- Non-urgent improvements
- Far-future features

**Example:** "Minor typo in the footer"

#### Default (0)
When no clear urgency signals are present, default to 0 (No priority).

---

## 5. Acceptance Criteria Generation

### Guidelines
- Generate 3-5 testable criteria per issue
- Use markdown checklist format: `- [ ] Criterion`
- Make criteria specific and measurable
- Cover functional requirements, edge cases, and UX

### Template by Issue Type

#### Bug Issues
```markdown
- [ ] Bug no longer reproduces in test environment
- [ ] Error handling prevents [specific failure mode]
- [ ] User receives clear feedback when [condition]
- [ ] Tested on [relevant platforms/devices]
- [ ] No regression in related functionality
```

#### Feature Issues
```markdown
- [ ] [Feature] works as described
- [ ] User can [specific action]
- [ ] Feature accessible from [location]
- [ ] Error states handled gracefully
- [ ] Documentation updated
```

#### Improvement Issues
```markdown
- [ ] [Metric] improved by [target amount]
- [ ] User experience validated with [method]
- [ ] No negative impact on [related feature]
- [ ] Performance benchmarks met
- [ ] Changes backward compatible
```

### Examples

**Feedback:** "App crashes when uploading large images"

**Acceptance Criteria:**
```markdown
- [ ] Users can upload images >10MB without crashes
- [ ] Progress indicator shows during upload
- [ ] Clear error message if upload fails
- [ ] Tested on iOS and Android with 50MB+ images
- [ ] Memory usage optimized for large files
```

**Feedback:** "Add dark mode"

**Acceptance Criteria:**
```markdown
- [ ] Dark mode toggle available in settings
- [ ] All screens support dark mode
- [ ] Mode preference persists across sessions
- [ ] System theme preference respected
- [ ] No color contrast accessibility issues
```

---

## 6. Estimate Inference

### T-Shirt Sizes
- **XS**: Trivial change, <1 hour
- **S**: Small task, 1-4 hours
- **M**: Medium task, 1-2 days
- **L**: Large task, 3-5 days
- **XL**: Very large, 1+ weeks

### Detection Heuristics

#### Scope Keywords
- "typo", "text change", "color" → XS
- "button", "simple form", "single field" → S
- "page", "flow", "integration" → M
- "feature", "system", "architecture" → L
- "redesign", "migration", "platform" → XL

#### Bug Complexity
- Cosmetic bugs → XS/S
- Logic bugs with known cause → S/M
- Crashes or data corruption → M/L
- Systemic issues → L/XL

#### Feature Scope
- UI-only changes → S/M
- Backend + Frontend → M/L
- Third-party integrations → L
- Multi-platform → L/XL

### Examples

| Feedback | Estimate | Reasoning |
|----------|----------|-----------|
| "Fix typo in welcome message" | XS | Text change only |
| "Add logout button to settings" | S | Simple UI addition |
| "Implement password reset flow" | M | Multi-step user flow |
| "Add OAuth authentication" | L | Third-party integration |
| "Migrate to new database" | XL | Major architectural change |

### When Uncertain
Default to **M** (Medium) if complexity is unclear. User can adjust in preview.

---

## 7. Platform-Specific Handling

### Upfront Platform Context

The platform is collected at the start of the workflow via `AskUserQuestion`. This context:
- Determines title prefix convention (see section 1)
- Guides automatic label matching
- Filters relevant acceptance criteria templates
- Influences complexity estimates

### Platform Labels

When platform is selected:
- **iOS** → Auto-add "iOS" label if available in team labels
- **Android** → Auto-add "Android" label if available
- **Web** → Auto-add "Web" label if available
- **Backend/API** → Auto-add "Backend" or "API" label if available
- **Multiple/All platforms** → User manually selects applicable labels in preview

### Platform-Aware Acceptance Criteria Templates

Adjust acceptance criteria based on platform:

**iOS-specific:**
```markdown
- [ ] Tested on iOS 15+
- [ ] No memory leaks in Instruments
- [ ] Supports light and dark mode
- [ ] VoiceOver accessibility verified
```

**Android-specific:**
```markdown
- [ ] Tested on API 26+ (Android 8.0+)
- [ ] No ANRs (Application Not Responding)
- [ ] Material Design guidelines followed
- [ ] TalkBack accessibility verified
```

**Web-specific:**
```markdown
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)
- [ ] Responsive design verified (mobile, tablet, desktop)
- [ ] WCAG 2.1 AA accessibility standards met
- [ ] Lighthouse score acceptable
```

**Backend/API-specific:**
```markdown
- [ ] API documentation updated
- [ ] Rate limiting considered
- [ ] Error responses follow standard format
- [ ] Database migrations tested
- [ ] Performance impact measured
```

### Platform Context in Descriptions

Include platform details in the Context section:
```markdown
## Context
- Platform: iOS
- Device: iPhone 14
- Issue occurs specifically with large images (>10MB)
```

---

## Advanced Patterns

### Batch Splitting
Split feedback into multiple issues when:
- Multiple distinct problems mentioned
- Feature request with multiple components
- Bug report with separate reproducible cases

**Example:**
Input: "The app crashes on login AND the upload button is missing"

Split into:
1. "Fix crash on login" (Bug, High)
2. "Restore missing upload button" (Bug, High)

### Context Enrichment
Add inferred context from:
- Platform mentions → Add to description
- User role/persona → Add to description
- Related issues mentioned → Add links
- Screenshots or logs → Request in AC

### Confidence Scoring
For ambiguous cases, note confidence in description:
```markdown
[Note: Auto-parsed as Feature with Medium confidence - please verify]
```

---

## Example: Complete Parsing

**Raw Feedback:**
```
The app crashes every time I try to upload a video on my iPhone 14.
This is super urgent as I can't use the app at all!
```

**Parsed Issue:**

```yaml
Title: Fix crash when uploading videos on iPhone
Team: Mobile
Project: Bug Fixes
Labels: [Bug, iOS]
Priority: 1 (Urgent)
Estimate: M

Description: |
  User reported: "The app crashes every time I try to upload a video on my iPhone 14. This is super urgent as I can't use the app at all!"

  ## Context
  - Device: iPhone 14
  - Issue: Consistent crash during video upload
  - Impact: User cannot use app (critical functionality blocked)

  ## Acceptance Criteria
  - [ ] Video uploads work without crashes on iPhone 14
  - [ ] Tested with various video sizes and formats
  - [ ] Error handling prevents app crash if upload fails
  - [ ] User receives clear feedback during upload process
  - [ ] Memory management optimized for large video files
```

---

## Troubleshooting

### Low-Quality Feedback
When feedback is vague ("This is broken"):
- Extract what you can
- Add "[Needs clarification]" to title
- Generate AC that includes "Gather more details from reporter"

### Conflicting Signals
When feedback contains mixed signals:
- Prioritize explicit statements over tone
- Default to lower priority if ambiguous
- Note ambiguity in description

### Missing Information
When critical info is missing:
- Use sensible defaults
- Add AC item to gather missing info
- Flag in preview for user review

---

## 8. Media and Link Extraction

### URL Detection
Automatically extract http/https URLs from feedback text using regex pattern matching.

**URL Pattern Matching:**
- **Image files**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`
- **Video files**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
- **Video platforms**: `.loom.com`, `.vimeo.com`, `.youtube.com`, `.youtu.be`
- **Screenshot services**: `d.pr`, `cloudapp`, `droplr`, `cl.ly`, `snagit.com`
- **Reference URLs**: docs, repos, related issues, any other http/https URLs

**Detection Process:**
1. Scan feedback text for http/https URL patterns
2. Categorize each URL by type (image, video, screenshot service, reference)
3. Extract surrounding context (up to 50 chars before/after) for title generation
4. Store with detected type and context

### Link Title Generation
Generate descriptive titles based on URL type and surrounding context.

**Title Templates by Type:**

| URL Type | Title Pattern | Examples |
|----------|--------------|----------|
| Screenshot service | "Screenshot showing [context]" | "Screenshot showing crash on login", "Screenshot of error message" |
| Image file | "Image: [filename or context]" | "Image: broken_ui.png", "Image of layout issue" |
| Video platform | "Video reproduction of [issue]" | "Video reproduction of upload bug", "Video: steps to reproduce" |
| Video file | "Video: [filename or context]" | "Video: crash_recording.mov" |
| Documentation | "Reference: [doc name]" | "Reference: Linear API docs", "Reference: authentication guide" |
| GitHub/Repo | "Reference: [repo/path]" | "Reference: repo/issue/123", "Reference: main/docs/api.md" |
| Generic/Other | "Attachment" or use URL filename | "Attachment", "screenshot-2024.png" |

**Context-Based Title Enhancement:**
- Extract keywords from surrounding text: "crash", "error", "bug", "issue", "broken"
- Combine with URL type for descriptive titles
- Example: "See https://d.pr/abc where app crashes" → "Screenshot showing crash"

### User-Provided URL Parsing
When user explicitly provides URLs in Phase 1 step 9:

**Input Formats Supported:**
```
# One per line
https://d.pr/abc123
https://loom.com/share/xyz: Video of bug
https://docs.example.com (API documentation)

# Comma-separated
https://d.pr/abc123, https://loom.com/share/xyz

# With titles (colon or parentheses)
https://example.com/image.png: Screenshot of issue
https://example.com/video.mov (Video reproduction)
```

**Parsing Rules:**
- Split on commas or newlines
- Extract title from:
  - Text after colon: `URL: Title`
  - Text in parentheses: `URL (Title)`
- If no title provided, generate based on URL type
- Trim whitespace from URLs and titles

### Link Deduplication
Merge auto-detected URLs with user-provided URLs:

**Deduplication Process:**
1. Normalize URLs (trim whitespace, lowercase)
2. Compare auto-detected vs user-provided
3. Remove duplicates (same URL)
4. For duplicates: preserve user-provided title over auto-generated
5. Maintain order: user-provided first, then auto-detected

**Example:**
```
Auto-detected: [{url: "https://d.pr/abc", title: "Screenshot"}]
User-provided: [{url: "https://d.pr/abc", title: "Crash screenshot"}]

Result: [{url: "https://d.pr/abc", title: "Crash screenshot"}]
```

### Auto-Detection Examples

**Example 1: Screenshot with context**
```
Input: "App crashes when I tap the button. See https://d.pr/abc123 for screenshot"

Extracted:
- url: https://d.pr/abc123
- title: "Screenshot showing button crash"
- type: screenshot_service
```

**Example 2: Video link**
```
Input: "Here's a loom showing the bug: https://loom.com/share/xyz789"

Extracted:
- url: https://loom.com/share/xyz789
- title: "Video reproduction of bug"
- type: video_platform
```

**Example 3: Multiple URLs**
```
Input: "Issue described in https://docs.example.com/auth. Also see https://github.com/repo/issues/42"

Extracted:
- url: https://docs.example.com/auth
  title: "Reference: auth documentation"
- url: https://github.com/repo/issues/42
  title: "Reference: repo/issues/42"
```

**Example 4: Image file**
```
Input: "UI looks broken, check /uploads/broken_layout.png"

Extracted:
- url: /uploads/broken_layout.png
- title: "Image: broken_layout.png"
- type: image_file
```

### Link Array Structure
Final output format for Linear API:

```javascript
[
  {
    url: "https://d.pr/abc123",
    title: "Screenshot showing crash on login"
  },
  {
    url: "https://loom.com/share/xyz",
    title: "Video reproduction of upload bug"
  },
  {
    url: "https://docs.example.com/api",
    title: "Reference: API documentation"
  }
]
```

### Edge Cases

**URLs within code blocks:**
- Skip URLs within ```code blocks``` or `inline code`
- Only extract from prose text

**Malformed URLs:**
- Attempt to fix common issues (missing http://, spaces)
- If unfixable, skip and note in description

**Duplicate detection case-sensitivity:**
- Compare URLs case-insensitively
- Preserve original URL casing in output

**Empty or missing titles:**
- Auto-generate based on URL type
- Fallback to "Attachment" or URL filename
