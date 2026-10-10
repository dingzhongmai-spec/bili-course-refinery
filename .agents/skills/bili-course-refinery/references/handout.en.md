# Teaching design for course handouts

Use this to organize verified course material into a handout suitable for independent learning. It supplements source verification and the five reviews. See [upstream-notice.md](upstream-notice.md) for provenance and adaptation.

## 1. Inspect materials before organizing them

Keep course scope in the manifest. Maintain task-local `handout-plan.md` with existing user requirements, audience and prerequisites, structure, priorities, length target if any, density, editions and formats, main file, missing evidence and next actions. Revise one plan rather than creating successive final copies.

Reuse conversation context and delivery agreements. Existing authorization to produce the handout permits continued production. Ask only when essential conditions, scope or delivery choices cannot be inferred; continue independent work. Without a length target, record an adjustable estimate without blocking production. Preserve this project's explanatory LaTeX/PDF default; do not automatically add instructor editions, workbooks or other formats.

Record actual processing needs; these may coexist and are not mutually exclusive tiers:

|Material|Handling and evidence limits|
|---|---|
|Text-bearing PDF, TeX, Markdown, subtitles|Read relevant content and record actual coverage; a text layer does not establish that figures or formulas were verified|
|Scans, photographs, board frames|Use available AI vision or OCR; retain actual recognition output and original-image locators, revisit ambiguities. Record the tool and confidence information it actually supplies; do not invent confidence scores|
|Audio/video|Acquire subtitles or ASR plus board frames; retain lesson, page, time range and tool version. ASR supplies transcription clues|
|DOCX/PPTX with embedded images|When using authentic figures, prefer extracting original assets; verify their source-page placement, cropping, labels and context. Extraction alone does not establish inspection|
|Damaged, restricted or unreliable material|Record the cause, affected entries and alternatives; never silently omit it or claim it was read|

When images establish board content or problem conditions, preserve authentic shapes, scales, arrows and labels. An editor's redrawn teaching diagram is permitted with clear attribution; it cannot replace the evidence image.

## 2. Move from a topic list to learner actions

Build a knowledge outline in the plan from read material: topic → concept/method → prerequisites and common errors, usually within three or four levels. Keep an editable Markdown list canonical; derive Mermaid only when useful and synchronize revisions. Mark core, important, background and unverified nodes. Video duration and repetition do not automatically determine teaching priority.

Maintain task-local `coverage.md`:

|Content ID|Observable learner action|Explanation location|Verified example|Practice/diagnosis if relevant|Common error/media|Source locator and verification status|
|---|---|---|---|---|---|---|

Every included knowledge node has a row traceable to its lessons and original examples. Use actual BV/page/time ranges or local file/page locators; mark unavailable locators unverified. `coverage.md` records teaching coverage, `manifest.json` records course scope, and `progress.json` records actual execution. Cross-reference them; the matrix does not replace progress evidence.

Check both source coverage and learning coverage: were all designated course materials processed, and does the reader have the explanation and demonstration needed for each action? Mentioning a concept or printing a formula does not establish usable understanding. Recall may be brief; substitution, proof and graph interpretation need checkable demonstrations. Add practice only when it serves the user's goal.

When practice is requested, select immediate checks, independent work, variants or enrichment by teaching function, with difficulty and source/editor attribution. Prioritize questions that reveal misconceptions and then progression; avoid filling quotas. For larger sets, add a question outline and distribution counts. If one question has several function labels, state deduplication rules; label counts are not unique question counts.

## 3. Connect explanation, demonstration and checking

Retain the method card's first intuition, justification, conditions and simpler-route comparison. A useful sequence is obstacle → key transformation → complete example → small check when relevant → error or counterexample. Adapt actions and difficulty to the reader; do not force every stage into every topic.

This minimal illustration is editor-created, not course content, and has no invented timestamp:

- Learner action: recognize the derivative of a function inside a radical and express remaining factors in the new variable.
- Example: integrate `x³/√(1+x²)` over real x. Set `u=1+x²`, so `x³ dx=(u−1)du/2`; the antiderivative is `(1+x²)^(3/2)/3−√(1+x²)+C`.
- Explanation focus: substitution simplifies both the radical and differential; naming u alone is insufficient.
- Optional immediate check: integrate `x/√(1+x²)` and explain the factor 1/2 after substitution. The answer is `√(1+x²)+C`; differentiation verifies it.
- Error check: losing 1/2 or the integration constant. Differentiating the answer verifies this step only. Do not claim a CAS check unless actually run.

For actual tasks, replace illustration entries with verified course problems and locators; keep added exercises attributed to the editor.

## 4. Length, editions and delivery

Choose outline, explanatory or practice-focused density according to the user's goal. When length is specified, record section budgets and actual compiled page counts. If over budget, remove redundant explanations, merge repetitive practice or restructure; preserve necessary derivations and designated lessons/examples. Report concrete scope/length conflicts and ask for a choice while continuing independent work. Do not hide excessive length or overflow by shrinking fonts.

Content editions and file formats are separate dimensions. If learner/instructor editions are requested, derive both from one canonical source: the learner edition contains stems, necessary hints and work space; the instructor edition adds full solutions, teaching prompts and common errors. Check answer visibility, images, references, equations and pagination in each edition. Preserve answer appendices when requested; verify what is actually visible.

For LaTeX/PDF, revise the current main TeX in place. Produce other formats only when requested and actually supported by available tools, derive them from the same content, record conversion differences and inspect each format. Installer readiness does not imply Word/PPT export support. Prefer user templates; PDF/images are visual references, not editable templates. Do not impose the upstream physics template.

Integrate with the existing five reviews: coverage checks knowledge nodes, course materials and matrix; mathematics/recalculation checks original and added problems and answers; method review checks whether demonstrations and checks serve learner actions; layout checks actual PDF pages, length and answer visibility. Report actual coverage, reading limits, page counts and budget deviations, format-specific inspection coverage and outstanding items.
