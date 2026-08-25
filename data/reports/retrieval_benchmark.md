# PostgreSQL Full-Text Retrieval Benchmark Report

- **Total Benchmark Queries**: `7`
- **Hit@5 Accuracy**: `100.0%` (6/6)
- **Average Query Latency**: `59.54 ms`

## Detailed Evaluation Results

| ID | Query | Category | Top Retrieved Episode | Score | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `eval_01` | What does Lenny's Podcast say about MVPs? | direct_topic | Eric Ries (00:24:29) | 0.8543 | 118.21ms | **PASSED** |
| `eval_02` | How should a startup decide what NOT to build? | strategic_question | Ravi Mehta (00:06:03) | 0.5444 | 52.28ms | **PASSED** |
| `eval_03` | How do you know when a product has product-market fit? | pmf_definition | Naomi Gleit (00:41:56) | 1.0623 | 52.64ms | **PASSED** |
| `eval_04` | What does Andy Johns say about burnout? | guest_specific | Andy Johns (00:13:48) | 1.1062 | 47.83ms | **PASSED** |
| `eval_05` | What do different guests say about product roadmaps? | cross_episode | Nancy Duarte (01:09:41) | 0.5047 | 49.06ms | **PASSED** |
| `eval_06` | What are useful approaches to user research? | user_research | Judd Antin (00:23:55) | 0.5308 | 46.94ms | **PASSED** |
| `eval_07` | Explain quantum computing algorithms. | unsupported | None | 0.0 | 49.82ms | **PASSED** |

## Query Breakdown & Retrieved Evidence
### `eval_01` — What does Lenny's Podcast say about MVPs?
- **Category**: direct_topic
- **Relevance Assessment**: Retrieved relevant chunk from 'Eric Ries' - 'Reflections on a movement | Eric Ries (creator of the Lean Startup methodology)' (Score: 0.8543)
- **Top 3 Retrieved Chunks**:
  1. **Eric Ries** - [Reflections on a movement | Eric Ries (creator of the Lean Startup methodology)](https://www.youtube.com/watch?v=xzebbzIntFc&t=1469) at `00:24:29` (Score: `0.8543`)
     > "Lenny (00:24:29): So along those same lines, so you wrote the book 12 years ago. If you could go back and change something in the book, is there somet..."
  2. **Nicole Forsgren** - [How to measure AI developer productivity in 2025 | Nicole Forsgren](https://www.youtube.com/watch?v=SWcDfPVTizQ&t=3516) at `00:58:36` (Score: `0.5066`)
     > "Lenny Rachitsky (00:58:36): It's so interesting. For example, Claude Code, "Find ways to clean up storage on my laptop," and it just tells you there's..."
  3. **Nicole Forsgren 2.0** - [How to measure AI developer productivity in 2025 | Nicole Forsgren](https://www.youtube.com/watch?v=SWcDfPVTizQ&t=3516) at `00:58:36` (Score: `0.5066`)
     > "Lenny Rachitsky (00:58:36): It's so interesting. For example, Claude Code, "Find ways to clean up storage on my laptop," and it just tells you there's..."

### `eval_02` — How should a startup decide what NOT to build?
- **Category**: strategic_question
- **Relevance Assessment**: Retrieved relevant chunk from 'Ravi Mehta' - 'How to build your product strategy stack | Ravi Mehta (Tinder, Facebook, Tripadvisor, Outpace)' (Score: 0.5444)
- **Top 3 Retrieved Chunks**:
  1. **Ravi Mehta** - [How to build your product strategy stack | Ravi Mehta (Tinder, Facebook, Tripadvisor, Outpace)](https://www.youtube.com/watch?v=tncs0m5pmQg&t=363) at `00:06:03` (Score: `0.5444`)
     > "Spent about six years there, worked on stuff on the platform side, on the content side. It was a really great experience, but I knew I wanted to go ea..."
  2. **Uri Levine 2.0** - [A founder’s guide to crisis management | Uri Levine (Waze co-founder, serial entrepreneur)](https://www.youtube.com/watch?v=lQdogVBHMdA&t=308) at `00:05:08` (Score: `0.5427`)
     > "Lenny Rachitsky (00:05:08): I should have said welcome back to the podcast, this is your second time here, which is a pretty rare feat. And the reason..."
  3. **Dalton Caldwell** - [Lessons from 1,000+ YC startups: Resilience, tar pit ideas, pivoting, more | Dalton Caldwell (YC)](https://www.youtube.com/watch?v=m7LvNTbaqSI&t=1510) at `00:25:10` (Score: `0.5225`)
     > "For people that are familiar with this terminology from us, sometimes they get defensive and don't get what we were saying. By definition it is only a..."

### `eval_03` — How do you know when a product has product-market fit?
- **Category**: pmf_definition
- **Relevance Assessment**: Retrieved relevant chunk from 'Naomi Gleit' - 'Meta’s head of product on working with Mark Zuckerberg, early growth tactics, and more | Naomi Gleit' (Score: 1.0623)
- **Top 3 Retrieved Chunks**:
  1. **Naomi Gleit** - [Meta’s head of product on working with Mark Zuckerberg, early growth tactics, and more | Naomi Gleit](https://www.youtube.com/watch?v=sTYuKgzZoL8&t=2516) at `00:41:56` (Score: `1.0623`)
     > "Lenny Rachitsky (00:41:56): I love that framework of micro barriers and macro barriers, just thinking about ways to make this accessible to more peopl..."
  2. **Naomi Gleit** - [Meta’s head of product on working with Mark Zuckerberg, early growth tactics, and more | Naomi Gleit](https://www.youtube.com/watch?v=sTYuKgzZoL8&t=1697) at `00:28:17` (Score: `0.91`)
     > "Lenny Rachitsky (00:28:17): One of the most interesting lessons from this activation metric that people talk about, because right now everyone's like,..."
  3. **Elena Verna 4.0** - [The new AI growth playbook for 2026 | How Lovable hit $200M ARR in one year](https://www.youtube.com/watch?v=6qAB6aUMIeA&t=3622) at `01:00:22` (Score: `0.7966`)
     > "Lenny Rachitsky (01:00:22): Awesome. Okay, great segue too. I want to talk about product-market fit in competition. You have this really interesting p..."

### `eval_04` — What does Andy Johns say about burnout?
- **Category**: guest_specific
- **Relevance Assessment**: Retrieved relevant chunk from 'Andy Johns' - 'When enough is enough | Andy Johns (ex-FB, Twitter, Quora)' (Score: 1.1062)
- **Top 3 Retrieved Chunks**:
  1. **Andy Johns** - [When enough is enough | Andy Johns (ex-FB, Twitter, Quora)](https://www.youtube.com/watch?v=_93m4PriHyc&t=828) at `00:13:48` (Score: `1.1062`)
     > "For the last two years, I've been doing a lot of writing, and most of my writing has really just been me opening up and sharing this personal side of ..."
  2. **Jonny Miller** - [Managing nerves, anxiety, and burnout | Jonny Miller (Nervous Systems Mastery)](https://www.youtube.com/watch?v=-kN8Agqee4w&t=3088) at `00:51:28` (Score: `0.5048`)
     > "Yeah, it's a good question. And some people do have a very high interoceptive capacity, and that can be overwhelming. In which case I would recommend ..."
  3. **Brian Chesky** - [Brian Chesky’s new playbook](https://www.youtube.com/watch?v=4ef0juAMqoE&t=2944) at `00:49:04` (Score: `0.5013`)
     > "But the last thing I'll say about adding a zero, Lenny, is I remember there was a story about a great basketball coach named John Wooden. He was one o..."

### `eval_05` — What do different guests say about product roadmaps?
- **Category**: cross_episode
- **Relevance Assessment**: Retrieved relevant chunk from 'Nancy Duarte' - 'Storytelling with Nancy Duarte: How to craft compelling presentations and tell a story that sticks' (Score: 0.5047)
- **Top 3 Retrieved Chunks**:
  1. **Nancy Duarte** - [Storytelling with Nancy Duarte: How to craft compelling presentations and tell a story that sticks](https://www.youtube.com/watch?v=-kHkWgjGD7U&t=4181) at `01:09:41` (Score: `0.5047`)
     > "And it was just because they actually thought about, okay. She goes, brushes their teeth, they do this. They were just literally walking through the l..."
  2. **Alex Komoroske** - [Thinking like a gardener, slime mold, the adjacent possible: Product advice from Alex Komoroske](https://www.youtube.com/watch?v=PoWRYBWSqpU&t=2408) at `00:40:08` (Score: `0.5024`)
     > "And sometimes I get it wrong, especially if I try to do it earlier, but when people feel very seen and they feel acknowledged for that, they now are w..."
  3. **Lauryn Isford** - [Mastering onboarding | Lauryn Isford (Head of Growth at Airtable)](https://www.youtube.com/watch?v=dLku0AiGPVA&t=0) at `00:00:00` (Score: `0.5015`)
     > "Lauryn Isford (00:00:00): An activation rate that falls in a lower percentage range, maybe for most companies five to 15%, is better than one that fal..."

### `eval_06` — What are useful approaches to user research?
- **Category**: user_research
- **Relevance Assessment**: Retrieved relevant chunk from 'Judd Antin' - 'The UX Research reckoning is here | Judd Antin (Airbnb, Meta)' (Score: 0.5308)
- **Top 3 Retrieved Chunks**:
  1. **Judd Antin** - [The UX Research reckoning is here | Judd Antin (Airbnb, Meta)](https://www.youtube.com/watch?v=L6RKi9ZvkT4&t=1435) at `00:23:55` (Score: `0.5308`)
     > "Lenny (00:23:55): Such a good point. And you have this actual term that you call user-centered performance, where it's the performance of being user-c..."
  2. **Noah Weiss** - [The 10 traits of great PMs, AI, and Slack’s approach to product | Noah Weiss (Slack, Google)](https://www.youtube.com/watch?v=XrRlVOWe5GE&t=2784) at `00:46:24` (Score: `0.5171`)
     > "Noah Weiss (00:46:24): We did a lot of user research. We looked at all these cohort curves, which you can imagine suddenly they're like, "Huh, they're..."
  3. **Noah Weiss** - [The 10 traits of great PMs, AI, and Slack’s approach to product | Noah Weiss (Slack, Google)](https://www.youtube.com/watch?v=XrRlVOWe5GE&t=2577) at `00:42:57` (Score: `0.5112`)
     > "Noah Weiss (00:42:57): Fine. Usability. I'm a big believer in you want to be data-informed, but you don't want to be so data-driven that you actually ..."

### `eval_07` — Explain quantum computing algorithms.
- **Category**: unsupported
- **Relevance Assessment**: Unsupported query correctly yielded no/low-confidence results (top score: 0.0)
