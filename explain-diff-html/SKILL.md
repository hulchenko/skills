---
name: explain-diff-html
description: Use when the user asks for a rich explanation of a code change, diff, branch, or PR. Produces HTML output.
---

# Explain Diff

Please make me a rich, interactive explanation of the specified code change.

It should have these sections:

- Background: Explain the existing system relevant to this change. (You should broadly explore surrounding code for this.) We don't know how much the reader already knows, so include a deep background for beginners (note that it can be skipped if the reader is already familiar), and then a more narrow background directly relevant to the change.
- Intuition: Explain the core intuition for the code change. The focus here is to explain the essence, not the full details. Use concrete examples with toy data. Use figures and diagrams liberally.
- Code: Do a high-level walkthrough of the changes to the code. Group/order the changes in an understandable way.
- Quiz: Come up with five questions that test the reader's knowledge of this PR. This should be medium difficulty, difficult enough that you actually need to understand the substance of the PR to answer them, but not gotchas. The goal is to help the reader make sure that they've actually understood. These should be presented as interactive multiple-choice questions, and when the user clicks, it tells them whether they were correct and gives feedback.

Format:

- Output a single self-contained HTML file which includes CSS and JavaScript. Make the whole thing one long page with section headers and a table of contents. Don't use tabs for the top-level structure. Basic responsive styling so you can view it on a phone is nice too. Put the file in a global place on my computer outside of the code repo, and make sure the filename always starts with today's date in `YYYY-MM-DD-` format, because it helps keep the files time-sorted and out of version control. For example: /tmp/2026-01-12-explanation-<slug>.html
- Please write with the clarity and flow of Martin Kleppmann, making it engaging and written in classic style. Transitions between sections should be smooth.

Language rules (apply to all prose on the page, including callouts and quiz text). Diagram labels may be short noun phrases:

- Write short paragraphs. Use 1 to 3 sentences each. Put the main point in the first sentence. Use one idea in each sentence.
- Say what the code does. Name the mechanism, the file, the function, or the number. Cut a sentence that could appear unchanged in another PR.
- Use the active voice. Name the actor. Use the plain word: "use", not "utilize" or "leverage".
- Use "is" or "has", not "serves as", "stands as", "boasts", or "features".
- Do not use these words: additionally, crucial, delve, enhance, foster, landscape, pivotal, showcase, testament, underscore, vibrant, robust, seamless.
- Do not end a sentence with an empty "-ing" phrase ("ensuring...", "highlighting...").
- Do not use "not just X, but Y". State the point. Do not force ideas into groups of three.
- Use one name for one thing. Repeat the name. Do not vary it for style.
- Do not use em dashes, en dashes, or hyphens as dashes. Use a period or a comma. Use a colon only before a list or an example.
- Do not use a metaphor, an aphorism, or a figurative verb where a literal phrase exists.
- Do not use a bold label with a colon that repeats its line. Do not bold every proper noun. Do not use emojis. Use straight quotes.
- Use sentence case for headings.
- Use at most one hedge ("may"). Do not write a praise opener, a chatbot phrase, or a generic closing sentence.
- Write whole sentences in prose. Spell out arrows in prose. Expand an abbreviation the first time you use it. Arrows are allowed inside diagrams.
- Some tips on diagrams. Ideally, you should pick a small number of diagram families that can be reused throughout the explanation to explain various cases. Some useful kinds of diagrams:
  - A very simplified version of the UI that the user sees in the app, to explain UI changes.
  - A system diagram showing data flow or communication between components. Make sure to include example data here!
- Don't use ASCII diagrams. Always use simple HTML designs for your diagrams, HTML lists for lists of things, etc.
  - For code blocks, always use `<pre>` tags. If you use a custom styled div instead, it **must** have
    `white-space: pre-wrap` in its CSS, or the browser will collapse all newlines into a single line.
    Before saving the file, scan each code block in the HTML source and confirm its CSS includes
    `white-space: pre` or `pre-wrap`.
- Use callouts for key concepts or definitions, important edge cases, etc.
