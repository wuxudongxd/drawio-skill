# Visual Communication Methodology

Distilled from Gene Zelazny's *Say It with Charts* (McKinsey's visual-communication handbook). Read this when **planning** a diagram (workflow step 2) — it answers *what to draw and why*, before `references/diagram-types.md` answers *how to encode it in XML*.

Applies to two diagram families:

- **Data charts** (pie/bar/column/line/dot) — quantitative comparisons
- **Concept visuals** (flows, structures, interactions) — architecture diagrams, flowcharts, and everything else draw.io is typically used for

---

## 1. The message-first decision framework

Never start from the data or from a chart type. Always:

```
Data → ① Decide your MESSAGE (one-sentence conclusion)
     → ② Identify the COMPARISON TYPE implied by that message
     → ③ Pick the CHART FORM that fits the comparison
```

The same dataset supports many different messages, and each message demands a different chart. Example — one monthly sales table can yield:

- "Sales have grown steadily since January" → time series → line/column
- "Product A far outsells B and C in May" → item ranking → bar
- "Product A holds the largest share of May sales" → component → pie / 100% bar

**Practical rule:** write the message sentence FIRST. It becomes the chart title (see §2), and every later decision (ordering, emphasis, color) must serve it.

### When NOT to draw a chart

- The information is simple enough for a sentence — a chart would dilute it.
- The audience expects a fixed tabular format (e.g., P&L lines).
- More charts ≠ more impact: one chart in a report gets 100% of the attention; twenty get a fraction each.
- Distinguish **analysis charts** (your scratch work) from **communication charts** (the deliverable). Never ship the scratch version — simplify it first.

---

## 2. Message titles (the single strongest rule)

The title states the **conclusion**, not the topic.

| ❌ Topic title | ✅ Message title |
|---|---|
| Company sales trend | Company sales have doubled |
| Distribution of employee ages | Most employees are 35–45 |
| Salary vs. profit relationship | Salary is unrelated to profit |
| System architecture | The gateway is the single entry point |
| Request handling flow | Failed auth terminates the request at step 3 |
| Service latency comparison | P99 latency is dominated by the DB query |

Why it matters:

- A topic title forces readers to infer the point themselves — they often infer the wrong one.
- A message title locks attention onto exactly the data you want emphasized.
- Even if the final render omits the title (space constraints), *writing it* is mandatory — it is the design spec for the whole diagram.

---

## 3. Data charts: five comparison types → five forms

### 3.1 Recognition keywords

| Comparison | Meaning | Trigger words in the message |
|---|---|---|
| **Component** | parts of a whole (%) | share, percentage, portion of total |
| **Item** | ranking of things | larger than, smaller than, about equal, rank |
| **Time series** | change over time | grow, rise, decline, fluctuate, since, trend |
| **Frequency distribution** | how many items fall in each range | range, concentration, most fall between X and Y |
| **Correlation** | relationship between two variables | varies with, increases with, is (un)related to |

### 3.2 Form matrix

| | Pie | Bar (horizontal) | Column (vertical) | Line | Dot (scatter) |
|---|:---:|:---:|:---:|:---:|:---:|
| Component | ✅ primary | ✅ 100% bar — better when comparing 2+ wholes | ✅ 100% column | | |
| Item | | ✅ primary | | | paired bars as fallback |
| Time series | | | ✅ ≤7–8 periods | ✅ >8 periods | |
| Frequency distribution | | | ✅ few groups (histogram) | ✅ many groups | |
| Correlation | | paired bars (≤15 pairs) | | | ✅ primary |

Usage frequency guidance (Zelazny): line ≈ 25%+, column ≈ 25%, bar ≈ 25% (the workhorse), scatter ≈ 10%, **pie < 5%** — the most over-used form.

### 3.3 Per-form design rules

**Pie**
- ≤6 slices; merge the tail into "Other".
- Start at 12 o'clock, clockwise; most important slice first, darkest fill.
- Comparing components across 2+ wholes? Never place pies side by side — use a 100% bar/column chart instead.
- No pyramids/cylinders/3D substitutes — they distort percentage perception.

**Bar (item ranking)**
- Prefer horizontal bars over columns for item comparisons — text labels fit without wrapping.
- Gap between bars < bar width.
- Order is a statement: high→low emphasizes the leader; deliberate scatter emphasizes unevenness. Always have a reason.
- Scale axis OR end-of-bar numbers — never both. Round the numbers (12%, not 12.3%).
- Variants: deviation (±), sliding (two components), range (min–max endpoints), paired (two measures), grouped (≤2 time points only), subdivided (most important component against the baseline — it's the only one measurable from a straight line).

**Column (time series, few periods)**
- Gap < column width; ≤7–8 periods, otherwise switch to line.
- Y axis starts at 0 — a truncated axis on columns fakes the trend.
- Positive/negative values cross the zero baseline with distinct fills.
- Overlapped columns (plan vs. actual): only if the back series is always larger.
- Subdivided columns: ≤5 components; if components must be measured precisely, split into separate small charts instead.

**Line**
- Trend line thicker than baseline; baseline thicker than axis.
- Solid = actuals, dashed = forecast; mark "today" on the axis.
- ≤4–5 lines per chart. Spaghetti? Split into small multiples — one panel per competitor, your line repeated in each.
- Surface (stacked area) charts: only the bottom layer reads accurately; put the most important component there.
- Dual axes: avoid unless scales are reconciled (use indexed values, base = 100, instead).
- Log scale shows growth *rate* (constant % = straight line) — never for levels or negative values.

**Dot (scatter)**
- Show the expected-pattern line (dashed diagonal); the message is whether points follow it.
- ≤15 pairs → paired bars are often clearer.
- Bubble size = optional third dimension.

### 3.4 Banned techniques

- 3D perspective charts (no reliable read point)
- Reversed time axes (newest on the left)
- Truncated Y axis on columns/bars (OK on line charts only when the zoom is deliberate and labeled)
- Scale grids drawn over perspective shapes
- Same data, two units repeated in one chart — pick one

---

## 4. Concept visuals: relationship type → visual form

This is the system most relevant to architecture and flow diagrams. First classify the relationship your message expresses, then pick the matching visual grammar. **The grammars are not interchangeable** — an arrow chain says "equal sequential steps"; a staircase says "each step builds on the last"; mixing them sends the wrong signal.

| Relationship | Visual grammar | Tech-diagram use |
|---|---|---|
| **Linear flow** | box→arrow chain (equal steps) · staircase (cumulative steps) · converging arrows (fan-in) · diverging arrows (fan-out) | pipelines, request paths, aggregation gateways, broadcast |
| **Vertical flow** | layers stacking upward, many-into-one upward arrow | layered architecture, capability stacks |
| **Cyclic flow** | closed ring (pure loop) · 3-segment recycle (Build-Test-Deploy) · spiral (loop + growth) | event loops, retry, CI/CD, iterative delivery |
| **Interaction** | bidirectional arrows · two ends + mediator in the middle · hub with radiating spokes | service-to-service deps, message queue/gateway mediation, hub-spoke topology |
| **Converging forces** | many arrows aimed at one focal node | multiple consumers pressuring one core service |
| **Leverage / balance** | scale/seesaw, tilted or level | trade-off slides (latency vs. throughput, debt vs. features) |
| **Penetration / barrier** | solid wall blocking arrows · grid some arrows pass through · stacked filter plates | firewall, ACL, middleware filter chain, rate limiting |
| **Interrelationship** | Venn overlap · concentric rings (core-extension) · hexagon honeycomb (peer mesh) · node-link network | shared components, plugin cores, service mesh |
| **Process / branching** | input→transform→output · tree expansion | state machines, decision trees, multi-level routing |
| **Partition** | whole cube exploding into modules · stacked planes · grid cells | service decomposition, layered tiers, capability matrix |
| **Course change** | zigzag rising arrow · tangled-to-aligned arrows | progress against friction, standardization/consolidation effect |

### Visual metaphors (use sparingly, verify with a colleague)

| Metaphor | Says | Use for |
|---|---|---|
| Maze | path is unclear, must find a way out | legacy-migration complexity |
| Puzzle pieces | incomplete without every piece | components that only work together |
| Staircase | each step builds on the previous | maturity models, phased migration |
| Broken chain | strength = weakest link | single point of failure |
| Funnel / sieve | progressive selection | request pipeline, multi-stage filtering |
| Gears | interlocked cooperation | CI/CD stages, system integration |
| Iceberg | visible API vs. hidden internals | abstraction layers |
| Bridge / wall | connection / isolation | integration layer / firewall |

Metaphor rule: a metaphor must make the audience *feel* the relationship instantly. If you have to explain it, drop it. Test on a colleague before shipping.

---

## 5. Four improvement strategies

When a draft chart doesn't land, apply in order:

1. **Simpler is better.** Every element must serve the message; delete the rest. One unit of measure, not two. No IP+port+version on every node — pick the one label that matters. Don't number every tick — anchor points only.
2. **Split, don't compress.** "Five points on five slides take the same time as five points on one slide." One diagram = one message. An architecture diagram should not show deployment topology + data flow + trust boundaries at once — make three views. For a diagram series, add a **tracker** (a mini-map with the current section highlighted).
3. **Change the form, don't tweak it.** The test: *cover the text — can you still see the conclusion from the shape alone?* If not, switch chart types entirely. A spiderweb of arrows → dependency matrix. Add/subtract relationships → waterfall, not pie. Multi-dimension comparison → small multiples, not one mega-chart.
4. **Get creative for unordered lists.** Parallel, equal, independent items beat bullet lists when shaped: puzzle (complementary), gear ring (mutually driving), honeycomb (flat peers), pyramid (layered support), network (fully connected), quadrant matrix + bubbles (2D positioning + magnitude).

---

## 6. Emphasis & layout discipline

Emphasis toolbox, in order of preference:

1. **Fill contrast** — darkest fill on the element the title talks about; everything else light/hollow. Three fill depths = done/current/pending in a flow.
2. **Position** — key slice at 12 o'clock; key path through the center; hub nodes central so edges radiate.
3. **Line weight** — your service's line thick and solid; competitors thin and dashed.
4. **Arrows / callouts** — point at the anomaly, state the delta ("6×").
5. **Reference lines** — dashed average/target/expectation lines.
6. **Separation** — explode the key pie slice; isolate the key module.

Layout discipline:

- **Order is a statement** — sorted high→low says "look who leads"; source order says "no judgement". Choose deliberately.
- Labels live next to their data (inside shapes, mid-edge), not in a distant legend — eliminate eye travel.
- Same components across multiple charts keep the same order and the same colors.

### Medium decides density

- **Screen / presentation:** presenter controls pacing → one message per diagram, large shapes, split aggressively (strategy 2).
- **Document (README, wiki, design doc):** reader controls pacing → a denser overview diagram is fine, but pair it with split detail views.

Default for this skill's output: document density, unless the user says it's for slides.

---

## 7. Pre-generation checklist

Run through before writing XML (workflow step 2):

1. What is the one-sentence message? Is it the title?
2. Does every element serve that message? Delete what doesn't.
3. Cover the text — does the shape alone show the conclusion? If not, change the form (§3 matrix / §4 table).
4. Screen or document? Set density accordingly; split multi-message diagrams.
5. Is the element order deliberate (rank / flow / importance)?
6. Is the key element visually dominant (fill / weight / position)?
7. Are labels adjacent to their data?
8. Would a relationship grammar or metaphor (§4) say it faster than boxes and text?
