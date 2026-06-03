# LinkedIn pair for cfo-filter-for-ai.html

Drafted 2026-05-13. Two versions. Both stay under 300 words, no em dashes, no emoji, no agency-speak. Pick one, schedule for 7:30am PT on the chosen Tuesday or Wednesday, then publish the blog post per `project_msiq_blog_protocol`.

---

## Version A | Primary (~270 words)

Most AI tools you'll hear about this month won't matter in two years.

I do not say that as a hot take. I say it as someone spending most of his week inside the actual agent-engineering space, watching peer founders lose weeks to frameworks that were unmaintained six months later.

The signal-to-noise ratio is bad and getting worse. You need a filter, not a feed.

Here are the five questions I run before letting any AI tool touch a workflow, or recommending one to a client:

1. Will this matter in two years?
2. Has someone you respect built something real on it and written about it honestly?
3. Does adopting it require throwing out your tracing, retries, config, and auth?
4. What does it cost you to skip this for six months?
5. Can you measure whether it actually helps?

Most launches fail at least one. A small number pass all five. Those are the ones worth your attention. The rest belong on a six-month watch list.

The deeper point is that every one of those questions requires judgment. Someone has to know what "matters in two years" means for this specific business. Someone has to know which operators to trust as references. Someone has to design the metric that proves the tool is helping.

That someone is the CFO. The person with budget authority, the cross-functional view, and the discipline to ask the boring questions when the rest of the room wants to ship the demo.

If the founder is making the AI buy call without that layer in the seat, the filter does not get run. What is your filter looking like right now?

[Link to blog post]

---

## Version B | Shorter, punchier (~210 words)

Every week a new AI tool lands in your inbox and your vendor list grows.

Most of them will not matter in two years.

Five questions to run before you adopt the next one:

1. Will this matter in two years, or is it a wrapper that gets absorbed by the model provider?
2. Has someone you respect run it through a real close cycle and written about it honestly?
3. Does adopting it require throwing out your existing tracing, retries, config, and auth?
4. What does it cost to skip this for six months and revisit?
5. Can you actually measure whether it helped?

The honest answer to question 4 is usually nothing. The honest answer to question 5 is usually no. Most teams refuse to run either test because skipping feels like falling behind, and measuring feels like work.

It is not falling behind. It is discipline. The CFOs who outperform on this in the next 24 months will be the ones who said no the most carefully, not the ones who tried the most.

Boring discipline pays. The most expensive thing in this category is being early, not being late.

What is your filter looking like right now?

[Link to blog post]

---

## Publish-day notes

- Post LinkedIn version (A or B, picked by Scott) at 7:30am PT on the chosen day.
- After LinkedIn is live, follow the publish-day checklist in `project_msiq_blog_protocol`:
  1. Add `<a class="blog-card">` to `blog/index.html` (decide series placement — likely "Acquisition Series" or a new "AI Practice" row).
  2. Optionally add `<ListItem>` to the CollectionPage JSON-LD ItemList on blog/index.html.
  3. Add `<url>` entry to `sitemap.xml` with the LinkedIn date as `<lastmod>`.
  4. Update `datePublished` in the HTML if the chosen date differs from 2026-06-10.
  5. Commit and push (msiq-site is publish-on-push).
- Pre-publish-gate chain (canonical-facts + scope-checker + brand-guardian + reality-checker) should run before LinkedIn ships.

## Source attribution note

The five-question framework is adapted from Rohit (@rohit4verse on X), "What to Learn, Build, and Skip in AI Agents (2026)," April 29 2026. The blog post credits him in the lede. LinkedIn version does not, by convention; if Scott wants explicit attribution there too, add one sentence after question 5: "Frame adapted from @rohit4verse, who wrote the cleanest version of this I have seen recently."
