"""builds docs/ from the case-study text below and the saved results of each project. run: python site/build.py"""
import ast
import csv
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO = "https://github.com/DaveNorine1/Portfolio/tree/main/projects"
EMAIL = "davidnorine@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/davidnorine"
GITHUB = "https://github.com/DaveNorine1"

mmm = json.loads((ROOT / "projects/media-mix-budget-cut/results/results.json").read_text())
geo = json.loads((ROOT / "projects/matched-market-test/results/results.json").read_text())


def read_csv(name):
    with open(ROOT / "projects/consumer-sentiment-capstone/results" / name, encoding="utf8") as f:
        return list(csv.DictReader(f))


def snippet(path, *names):
    #pulls functions straight from the project source so the page always shows the real code
    source = (ROOT / "projects" / path).read_text()
    tree = ast.parse(source)
    parts = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            parts.append((names.index(node.name), "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno])))
    code = "\n\n".join(p for _, p in sorted(parts))
    return f'<pre><code>{html.escape(code)}</code></pre>'


def pct(v, d=1, sign=False):
    return f"{v * 100:{'+' if sign else ''}.{d}f}%"


def _line(fn, cls="", n=48, x0=14, x1=306):
    pts = [(x0 + (x1 - x0) * i / (n - 1), fn(i / (n - 1))) for i in range(n)]
    d = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return f'<path pathLength="1" class="{cls}" d="{d}"/>'


def _wave(t, a=9, f=3.0, base=78, seed=0.0):
    return base + a * math.sin(t * f * 6.283 + seed) + a * 0.45 * math.sin(t * f * 15.1 + seed * 2)


_bars = [122, 118, 124, 120, 56, 50, 54, 60, 68, 76, 84, 92]
_dots = [(x, y) for x, y in [(52, 75), (72, 62), (72, 88)]]
_grown = [(188 + 26 * c, 40 + 24 * r) for c in range(4) for r in range(4)]
MOTIFS = {
    "budget-cut": _line(lambda t: 132 - 112 * (t ** 1.3 / (t ** 1.3 + 0.16)) * 1.16) + _line(lambda t: 132 - 76 * (t ** 1.3 / (t ** 1.3 + 0.28)) * 1.28, "c2") + _line(lambda t: 132 - 44 * (t ** 1.3 / (t ** 1.3 + 0.45)) * 1.45) + '<circle class="dot" cx="118" cy="51" r="5"/><circle class="dot d2" cx="150" cy="77" r="5"/>',
    "signal-loss": "".join(f'<rect class="bar{" b2" if 4 <= i else ""}" x="{22 + i * 24}" y="{h}" width="12" height="{136 - h}" rx="2"/>' for i, h in enumerate([28, 32, 26, 30, 106, 112, 108, 100, 88, 78, 68, 58])),
    "ai-agent": "".join(f'<rect class="doc" x="28" y="{y}" width="56" height="22" rx="2"/><path d="M34 {y + 8}h44M34 {y + 14}h30"/><path d="M84 {y + 11}L150 75"/>' for y in (18, 64, 110)) + '<circle class="dot d2" cx="158" cy="75" r="12"/><path class="c2" d="M170 75H214"/><rect class="doc" x="214" y="44" width="84" height="62" rx="4"/><path d="M226 62h60M226 74h60M226 86h36"/>',
    "matched-market": _line(lambda t: _wave(t, 8, 2.2, 88 if t < 0.66 else 88 - 44 * min(1, (t - 0.66) * 6)), "c2") + _line(lambda t: _wave(t, 8, 2.2, 92, 0.25)) + '<path class="guide" d="M207 14V136"/>',
    "building-the-team": "".join(f'<circle class="dot" cx="{x}" cy="{y}" r="7"/>' for x, y in _dots) + '<path class="c2" d="M100 75H160M150 65l10 10l-10 10"/>' + "".join(f'<circle class="dot{" d2" if (i % 5 == 0) else ""}" cx="{x}" cy="{y}" r="7"/>' for i, (x, y) in enumerate(_grown)),
    "consumer-sentiment": _line(lambda t: _wave(t, 16, 1.6, 74) if t < 0.7 else _wave(0.7, 16, 1.6, 74) + (t - 0.7) * 24) + _line(lambda t: _wave(0.7, 16, 1.6, 74) + (t - 0.7) * 24 - (t - 0.7) * 60 if t > 0.7 else _wave(0.7, 16, 1.6, 74), "c2", x0=218) + _line(lambda t: _wave(0.7, 16, 1.6, 74) + (t - 0.7) * 24 + (t - 0.7) * 60 if t > 0.7 else _wave(0.7, 16, 1.6, 74), "c2", x0=218),
}
MOTIFS["gpt-benchmark"] = _line(lambda t: 30 + 100 * (1 - 2.718 ** (-t * 9)), "") + _line(lambda t: 30 + 62 * (1 - 2.718 ** (-t * 14)) - 42 * max(0, t - 0.12), "c2")
MOTIFS["retention-ltv"] = _line(lambda t: 26 + 100 * (1 - 2.718 ** (-t * 3.2))) + _line(lambda t: 26 + 58 * (1 - 2.718 ** (-t * 2.2)), "c2") + '<path class="guide" d="M150 40V100"/>'
MOTIFS["catering"] = (
    '<rect class="doc" x="18" y="54" width="62" height="42" rx="3"/><path d="M18 56l31 22l31-22"/><path d="M80 75H118"/><circle class="dot d2" cx="130" cy="75" r="12"/>'
    + "".join(f'<path d="M142 75L188 {y}"/><rect class="doc" x="188" y="{y - 15}" width="46" height="30" rx="3"/>' for y in (28, 75, 122))
    + '<path d="M196 21h30M196 28h30M196 35h18M211 60v30M196 75h30M196 115h30M196 124h30M203 110v22M218 110v22"/>'
    + '<path class="c2" d="M234 28L270 75M234 75H270M234 122L270 75"/><circle class="c2 ring" cx="284" cy="75" r="14"/><path class="c2" d="M277 75l5 6l10-12"/>'
)
MOTIFS["consumer-sentiment"] = _line(lambda t: _wave(t * 0.7, 16, 1.6, 74), x1=218) + "".join(
    _line(lambda t, k=k: _wave(0.7, 16, 1.6, 74) + k * t, "c2", n=12, x0=218) for k in (-34, 34))


def motif(slug, cls="art"):
    return f'<svg class="{cls}" viewBox="0 0 320 150" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">{MOTIFS[slug]}</svg>'


def tile(slug, title, metric, depth=""):
    return f'<a class="tile" href="{depth}work/{slug}.html">{motif(slug)}<div class="tbody"><h3>{title}</h3><p class="num">{metric}</p></div></a>'


#response curves with diminishing returns, drawn once when the page loads
CURVES = """<svg class="curves" viewBox="0 0 600 320" preserveAspectRatio="xMaxYMid slice" aria-hidden="true" focusable="false"><path pathLength="1" d="M0 310C60 180 150 90 290 62S520 34 600 30"/><path pathLength="1" class="c2" d="M0 310C90 240 190 170 320 132S520 96 600 90"/><path pathLength="1" d="M0 310C120 285 240 240 350 205S530 165 600 155"/></svg>"""


def page(title, description, body, depth=0, script="", art=None):
    up = "../" * depth
    w = "wrap wide" if depth == 0 else "wrap"
    graphic = motif(art, "curves motif") if art else CURVES
    #everything before the marker sits in the color band
    tag = "section" if body.lstrip().startswith("<section") else "article"
    head, rest = body.split("<!--endband-->")
    head = head.replace(f'<{tag} class="hero">', "", 1)
    rest = f"<{tag}>" + rest
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title><meta name="description" content="{description}">
<meta name="author" content="Dave Norine"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&family=Libre+Franklin:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<link rel="stylesheet" href="{up}assets/site.css?v=5"></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="topband"><div class="{w} top"><a href="{up}index.html"><b>Dave Norine</b></a><nav><a href="{up}index.html#work">Work</a><a href="{LINKEDIN}">LinkedIn</a><a href="{GITHUB}">GitHub</a><a href="mailto:{EMAIL}">Email</a></nav></div></header>
<main id="main"><div class="band">{graphic}<div class="{w}">{head}</div></div><div class="{w}">{rest}</div></main>
<footer class="{w}">Dave Norine, Plymouth, Minnesota. <a href="mailto:{EMAIL}">{EMAIL}</a></footer>
{'<script src="' + up + 'assets/charts.js?v=2"></script><script>' + script + '</script>' if script else ''}
</body></html>
"""


def nav_next(slug, label):
    return f'<p class="next">Next: <a href="{slug}.html">{label}</a></p>'


# ---------- home
LOGO = '<img class="logo" src="assets/umich-logo.png" alt="University of Michigan">' if (DOCS / "assets/umich-logo.png").exists() else ""
home = f"""
<section class="hero">
<div class="kicker">Marketing analytics, data science and AI</div>
<h1>I build analytics and data science teams that leaders count on for their biggest decisions.</h1>
<p class="lede"><span class="longintro">I've spent 16 years doing this in medical device, consumer tech, consumer health, CPG, retail, and agency organizations, and I still write the models. Most recently I built a small support team into a data science, analytics, BI, and analytics engineering team more than three times its size, whose work informs an eight-figure annual marketing budget.</span><span class="shortintro">16 years across medical device, consumer tech, CPG, retail, and agencies, and I still write the models.</span></p>
<div class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a><a href="{LINKEDIN}">LinkedIn</a><a href="{GITHUB}">GitHub</a></div>
<!--endband-->
<div class="facts">
<div><b>16 years</b><span>in analytics, insights, and measurement</span></div>
<div><b>3</b><span>analytics practices built</span></div>
<div><b>10+ years</b><span>leading teams</span></div>
</div>
<div class="edu">{LOGO}<div><b>Master of Applied Data Science</b><span>University of Michigan</span></div><a class="resume" href="mailto:{EMAIL}?subject=Resume%20request">Email me for my resume</a></div>
</section>
<section id="work">
<h2>Selected work</h2>
<p class="small">My current employer is anonymized. Demos run on made-up data.</p>
<div class="tiles">
{tile("budget-cut", "Protecting results through a budget cut", "Leads fell a fraction of the assumed decline")}
{tile("signal-loss", "Rebuilding measurement after losing tracking", "Most tracking lost, much of it recovered")}
{tile("ai-agent", "Taking an AI agent to daily use", "Double-digit drop in onboarding time")}
{tile("matched-market", "Measuring lift with geo tests", "From causal read to scale-or-stop")}
{tile("building-the-team", "Building the team", "More than tripled, and three practices built")}
{tile("catering", "Automating catering inquiries, with approval", "10+ hours a week saved")}
</div>
<h2>Code</h2>
<div class="codes">
<a href="{REPO}/support-agent"><h3>Conversational support agent</h3><code>LangGraph agent, Chroma, citations, safety routing, memory</code><span>LangChain, Gradio</span></a>
<a href="{REPO}/media-mix-budget-cut"><h3>Media mix model</h3><code>adstock() hill() optimize_budget()</code><span>Python, SciPy</span></a>
<a href="{REPO}/matched-market-test"><h3>Matched-market test</h3><code>match_pairs() normal_posterior()</code><span>Python, SciPy</span></a>
<a href="work/retention-ltv.html"><h3>Retention and lifetime value</h3><code>churn, LTV, offer_value()</code><span>Python, scikit-learn</span></a>
<a href="work/gpt-benchmark.html"><h3>GPT from scratch</h3><code>113K tokens/sec on an A100</code><span>PyTorch, CUDA</span></a>
<a href="work/consumer-sentiment.html"><h3>Forecasting consumer sentiment</h3><code>model comparison, scenarios</code><span>University of Michigan capstone</span></a>
</div>
</section>
"""

# ---------- budget cut
s = mmm["scenario"]
names = ["Paid search", "Paid social", "Display", "CTV", "Email"]
truth_gap = s["optimized"]["truth"] - s["across_the_board"]["truth"]
rec = mmm["recovery"]
ax = mmm["across_seeds"]
rec_rows = "".join(
    f'<tr><td>{n}</td><td class="n">{rec[c]["true_decay"]:.2f}</td><td class="n">{rec[c]["fit_decay"]:.2f}</td><td class="n">{rec[c]["true_weekly_leads"]:.0f}</td><td class="n">{rec[c]["fit_weekly_leads"]:.0f}</td><td class="n wideonly">{rec[c]["true_half_sat"] / 1000:.0f}K</td><td class="n wideonly">{rec[c]["fit_half_sat"] / 1000:.0f}K</td></tr>'
    for n, c in zip(names, mmm["channels"]))
total_true = sum(rec[c]["true_weekly_leads"] for c in mmm["channels"])
total_fit = sum(rec[c]["fit_weekly_leads"] for c in mmm["channels"])
budget = f"""
<article class="hero">
<div class="kicker">Budget decisions</div>
<h1>Protecting results through a double-digit budget cut</h1>
<p class="lede">When budgets took a double-digit cut at a medical device division, I wrote the media mix models that showed senior leadership where to protect investment. Leads fell by only a fraction of the decline we assumed based on past cuts.</p>
<!--endband-->
<h2>The situation</h2>
<p>A cut that size can be spread evenly or placed deliberately, and the division needed to know what each choice would cost. This is a long-consideration purchase, with more than a year between a patient's first lead and a completed procedure, so waiting to see what the cut did to procedures wasn't an option.</p>
<h2>What I did</h2>
<ul>
<li>Wrote the Python media mix models myself, using a holdout and regression modeling so the guidance rested on incremental effects and not on correlations.</li>
<li>Worked with Finance on where to protect spend.</li>
<li>Took the results to the executive team: the division President and the VPs of Marketing, Sales, and Finance.</li>
</ul>
<div class="result"><strong>Result:</strong> leads fell by only a fraction of the decline we assumed based on past cuts.</div>
<h2>Demo: the same approach on made-up data</h2>
<p>The real data stays private, so I rebuilt the method on synthetic data. It simulates three years of weekly leads for a made-up brand across five channels, with carryover (adstock) and diminishing returns (saturation). Everything from here down is simulated. That has one advantage: I can grade the model against the truth, which you never get to do with real data. It's also a best case, since the data follows the model's own equations and the forecast below uses actual holdout spend. Real data won't be this kind.</p>
<figure><figcaption>Demo: on 26 weeks it never saw, the model averaged {pct(mmm['backtest']['mape'])} error, vs. {pct(mmm['backtest']['naive_mape'])} for a flat average</figcaption><div id="bt"></div></figure>
<h3>Demo: two ways to take a 20% cut</h3>
<figure><figcaption>Demo: reallocating costs fewer leads than cutting evenly, in one simulated world</figcaption><div id="sc"></div></figure>
<p>One simulated world can flatter a method, so I reran the whole exercise on {ax['runs']} of them. Reallocating beat the even cut in truth every time. But the model overstated the gain in {pct(ax['share_overstated'], 0)} of runs, promising {ax['mean_model_gain'] * 100:.1f} points on average and delivering {ax['mean_true_gain'] * 100:.1f}. That's the optimizer's curse: it moves money toward wherever the estimates happen to run high. The 95% ranges held up for the even cut, covering the truth {pct(ax['coverage_even_cut'], 0)} of the time, but were too narrow for the reallocation ({pct(ax['coverage_reallocation'], 0)}) and the gain ({pct(ax['coverage_gain'], 0)}). So I trust the direction of a reallocation, and I'd discount the size of the promised gain before taking it to Finance.</p>
<h3>Demo: try it yourself</h3>
<p>The demo uses a 20% cut. Each slider sets a channel's spend from 50% to 150% of plan, the same guardrails the optimizer uses. The figures are made up.</p>
<div id="sim"></div>
<h3>Demo: what the model got wrong</h3>
<p>Total media leads came in at {total_fit:.0f} a week against a true {total_true:.0f}, and channel estimates were noisier than the total. Email is the clearest miss. The model put its saturation point at about {rec['email']['fit_half_sat'] / 1000:.0f}K a week against a true {rec['email']['true_half_sat'] / 1000:.0f}K, believed the channel had room to grow, and gave it the largest increase the guardrails allow. That's the kind of move I'd validate with a geo test before committing to it.</p>
<div class="tablewrap"><table><thead><tr><th>Channel</th><th class="n">True carryover</th><th class="n">Fitted</th><th class="n">True leads/week</th><th class="n">Fitted</th><th class="n wideonly">True half-saturation</th><th class="n wideonly">Fitted</th></tr></thead><tbody>{rec_rows}</tbody></table></div>
<h3>The code</h3>
<p>The two transformations at the center of the model, from the repo:</p>
{snippet("media-mix-budget-cut/src/mmm.py", "adstock", "hill")}
<p><a href="{REPO}/media-mix-budget-cut">See the full model, optimizer, and tests on GitHub</a></p>
{nav_next('signal-loss', 'Rebuilding measurement after losing most of our tracking')}
</article>
"""
bud_js = f"""
const f1=v=>v.toFixed(0);
lineChart('bt',{{x:{json.dumps(list(range(1, 27)))},xName:'Holdout week',xTitle:'Holdout week',fmt:f1,label:'Actual and predicted weekly leads over the 26-week holdout',
 series:[{{name:'Actual',color:'--s2',values:{json.dumps([round(v, 1) for v in mmm['backtest']['actual']])}}},{{name:'Model forecast',color:'--s1',values:{json.dumps([round(v, 1) for v in mmm['backtest']['predicted']])}}}]}});
const p=v=>(v>0?'+':'')+(v*100).toFixed(1)+'%';
rangeChart('sc',{{label:'Change in weekly leads under two 20 percent cuts',fmt:p,labelW:170,legend:'<span><i style="background:var(--s1)"></i>Model estimate and 95% range</span><span><i style="background:var(--s2)"></i>Known truth (diamond)</span>',
 rows:[{{label:'Cut every channel 20%',mid:{s['across_the_board']['leads_change']},low:{s['across_the_board']['ci95'][0]},high:{s['across_the_board']['ci95'][1]},truth:{s['across_the_board']['truth']}}},
 {{label:"Model's reallocation",mid:{s['optimized']['leads_change']},low:{s['optimized']['ci95'][0]},high:{s['optimized']['ci95'][1]},truth:{s['optimized']['truth']}}}]}});
budgetSim('sim',{{names:{json.dumps(names)},sim:{json.dumps(mmm['simulator'])},opt:{json.dumps(s['optimized']['spend'])}}});
"""

# ---------- signal loss
signal = """
<article class="hero">
<div class="kicker">Leading through change</div>
<h1>Rebuilding measurement after losing most of our tracking</h1>
<p class="lede">A cookie consent change wiped out most of our trackable traffic at a medical device division. I rebuilt the KPI framework around what we could still trust and, with Legal and IT, helped drive the changes that recovered a large share of it in early results.</p>
<!--endband-->
<h2>The situation</h2>
<p>The dashboards kept running after the change, but they now described only the visitors who had opted in. Leadership needed to know which numbers still meant what they used to, and we needed a way to get the data back without crossing any privacy lines.</p>
<h2>What I did</h2>
<ul>
<li>Rebuilt the KPI framework and ran a KPI workshop, so we could keep making decisions while the data was incomplete.</li>
<li>Worked with Legal and IT and helped drive state-by-state opt-out consent and server-side collection.</li>
<li>Kept person-level data to measurement only. It's never used for targeting or advertising.</li>
</ul>
<div class="result"><strong>Result:</strong> early results show a large share of the lost traffic trackable again.</div>
<h2>How I think about what to trust</h2>
<p>This is the general version of the framework, with the company specifics taken out. When tracking gets partial, each question should move to the source least affected by the loss.</p>
<div class="tablewrap"><table><thead><tr><th>The question</th><th>Read this first</th><th>Be careful with</th></tr></thead><tbody>
<tr><td>Is the business healthy?</td><td>First-party outcomes in the CRM, such as leads and completed procedures</td><td>Site-analytics conversion counts, which fell with consent</td></tr>
<tr><td>Did marketing work?</td><td>Geo tests and media mix models, which use aggregates and don't need user-level tracking</td><td>Platform-reported conversions and last-touch attribution</td></tr>
<tr><td>Is this page or campaign improving?</td><td>Rates within the consented group, compared over time and against the same period</td><td>Comparing raw volumes across the date of the change</td></tr>
<tr><td>Is the data itself okay?</td><td>Share of traffic that's trackable, reported as its own KPI</td><td>Assuming consented visitors look like everyone else</td></tr>
</tbody></table></div>
<h2>Limits of the early read</h2>
<p>These are early results. And a higher trackable share doesn't make the sample representative, because the people who can be tracked may still differ from those who can't. That's why the framework stays in place after recovery.</p>
<p class="next">Next: <a href="ai-agent.html">Taking an AI agent from pilot to daily use</a></p>
</article>
"""
sig_js = """
barChart('tr',{label:'Trackable share of traffic before the change, after it, and in early results',labelW:190,valueName:'Trackable traffic',fmt:v=>v+'%',
 rows:[{label:'Before the consent change',value:100,text:'nearly 100%'},{label:'After the consent change',value:35,text:'35%'},{label:'Early results after the fixes',value:70,text:'near 70%'}]});
"""

# ---------- ai agent
agent = f"""
<article class="hero">
<div class="kicker">AI adoption</div>
<h1>Taking an AI agent from pilot to daily use</h1>
<p class="lede">As my division's AI Champion, I built a retrieval-based AI agent for a small patient engagement team that works as an inbound patient contact center. The team uses it daily. It delivered a double-digit drop in onboarding time and saves real working time every week.</p>
<!--endband-->
<h2>The situation</h2>
<p>The team's answers lived in dozens of approved decks, FAQs, and scripts. In a patient-facing setting, an assistant that makes something up is worse than having no assistant.</p>
<h2>What I did</h2>
<ul>
<li>Met with the team's leadership to define what the agent had to do.</li>
<li>Confirmed licensing with IT before investing build effort.</li>
<li>Brought in Legal, Privacy, and IT as governance partners.</li>
<li>Grounded every answer in the approved documents through retrieval.</li>
<li>Ran a structured pilot and tested its answers before launch.</li>
</ul>
<div class="result"><strong>Result:</strong> used daily by the team, with a double-digit drop in onboarding time and working time saved every week.</div>
<h2>Demo: a support agent you can inspect</h2>
<p>The real agent and documents are private, so everything from here down is a separate demo for a made-up company, Larkfield Water. I built it with LangChain, LangGraph, Chroma, and Gradio, and tested it with Llama 3.1 on a GPU.</p>
<p>The design keeps control in code:</p>
<ul>
<li><b>Safety first:</b> health and urgent questions go to a person before retrieval runs.</li>
<li><b>Find the source:</b> sentence embeddings find the right documents.</li>
<li><b>Approved words only:</b> the model picks a sentence, code confirms it's in the document, and the customer reads that sentence with its citation.</li>
<li><b>Know when to stop:</b> if nothing checks out, it declines and points to a lead.</li>
</ul>
<h3>Demo: test results</h3>
<div class="tablewrap"><table><thead><tr><th>Test questions</th><th class="n">Passed</th></tr></thead><tbody>
<tr><td>Answerable questions answered correctly</td><td class="n">16 of 20</td></tr>
<tr><td>Unanswerable questions declined</td><td class="n">5 of 8</td></tr>
<tr><td>Safety questions sent to a person</td><td class="n">12 of 12</td></tr>
</tbody></table></div>
<p><b>My call on this demo: ready for a supervised pilot, not for customers on its own.</b> Every safety question reached a person. On 3 of 8 unanswerable questions, it quoted a real sentence that didn't answer the question, and it declined 3 answerable ones, so I'd keep a person in the loop.</p>
<h3>Demo: four outputs from the agent</h3>
<div class="tablewrap"><table><thead><tr><th>Question</th><th>What it did</th></tr></thead><tbody>
<tr><td>what does a blinking red light mean</td><td>Answered: "A blinking red light means the filter is past its rated life and should be replaced now. [FILT-04]"</td></tr>
<tr><td>what's your CEO's email</td><td>Declined: "I can't find that in the approved material. Please check with a lead."</td></tr>
<tr><td>my daughter broke out in hives after her bath</td><td>Handed off: "This needs a person. Transferring you to the care specialist."</td></tr>
<tr><td>can I lease a system instead of buying</td><td>A miss: it quoted a real sentence about renters that doesn't answer the question. [INST-04]</td></tr>
</tbody></table></div>
<h3>The code</h3>
<p>The check every answer has to pass, from the repo:</p>
{snippet("support-agent/src/agent.py", "verify")}
<p><a href="{REPO}/support-agent">See the agent, documents, and tests on GitHub</a></p>
{nav_next('matched-market', 'Measuring lift with matched-market tests')}
</article>
"""

# ---------- matched market
e, dc, ck = geo["estimate"], geo["decision"], geo["checks"]
power = {p["pairs"]: p["power"] for p in geo["power"]}
market = f"""
<article class="hero">
<div class="kicker">Experimentation</div>
<h1>Measuring lift with matched-market tests</h1>
<p class="lede">At a medical device division I built the test-and-learn practice: A/B testing set up with IT and Legal, and matched-market tests run with IT, Finance, Sales, and Field Marketing to measure the lift from local campaigns. Here's how I run one and how I turn the read into a decision.</p>
<!--endband-->
<h2>Why geo tests</h2>
<p>A geo test needs no user-level tracking and gives a real control group. That makes it the best answer I know of when consent limits tracking and a campaign can't be randomized person by person. The hard part is reading the result honestly, because a handful of markets carries little statistical power.</p>
<h2>Demo: a worked example on made-up data</h2>
<p>My real test results stay private, and everything from here down is simulated. This simulation uses 40 markets over 86 weeks, with a campaign that truly lifts leads by {pct(geo['true_lift_pct'])} in test markets for 8 weeks. Here's the process:</p>
<ul>
<li><b>Match:</b> pair markets on level and shape over the first 52 weeks.</li>
<li><b>Check:</b> keep the 4 pairs that track each other best on the next 26 weeks, which matching never saw.</li>
<li><b>Assign:</b> flip a coin within each pair to choose the test market.</li>
<li><b>Estimate:</b> use difference-in-differences on log leads, by pair.</li>
</ul>
<figure><figcaption>Demo: test markets separate from their controls when the campaign starts</figcaption><div id="ts"></div></figure>
<figure><figcaption>Demo: all four pairs show lift</figcaption><div id="pr"></div></figure>
<h3>Demo: how sure can we be?</h3>
<p>A simple t-interval says the lift is {pct(e['low_pct'])} to {pct(e['high_pct'])}. That test is fine on average: run on the {ck['aa_pool_pairs']} untreated pairs in the same window, {ck['aa_draws']:,} random draws produced false positives {pct(ck['aa_false_positive'])} of the time, close to the expected 5%. But the width of any single interval rests on three degrees of freedom, and these four pairs happen to agree more than pairs usually do. So I took the noise level from those untreated draws, which is wider.</p>
<p>Using that noise and a weakly skeptical prior centered on zero, the Bayesian estimate of the lift is {pct(dc['posterior_mean_pct'])}, with a 95% range of {pct(dc['posterior_low_pct'])} to {pct(dc['posterior_high_pct'])}. With four pairs, an exact randomization test also can't get below p = {e['sign_flip_min_p']:.3f}. Four pairs can show direction, but they can't settle a close call.</p>
<h3>Demo: the decision</h3>
<div class="tablewrap"><table><tbody>
<tr><td>Probability the campaign lifts leads at all</td><td class="n">{pct(dc['prob_positive'], 0)}</td></tr>
<tr><td>Lift needed to pay back at a made-up value of ${dc['value_per_lead']:.0f} a lead</td><td class="n">{pct(dc['breakeven_lift_pct'])}</td></tr>
<tr><td>Cost per incremental lead at the point estimate</td><td class="n">${dc['cost_per_incremental_lead']:.0f}</td></tr>
<tr><td>Probability it pays back</td><td class="n">{pct(dc['prob_pays_back'], 0)}</td></tr>
</tbody></table></div>
<div class="result"><strong>My call on this demo: don't scale it as is.</strong> The campaign very likely works, and it probably doesn't pay for itself at this spend. A report that stopped at "significant lift" would have sent more money after it. I'd rerun at a lower spend per market with more pairs. Power to tell a lift of this size from zero climbs from {pct(power[4], 0)} at 4 pairs to {pct(power[8], 0)} at 8. Showing that it clears the payback line is a harder test, and it would need a new power estimate at the new spend.</div>
<p>The simulation lets me check the answer: the true lift of {pct(geo['true_lift_pct'])} falls inside the range, and the point estimate of {pct(e['lift_pct'])} landed close to it.</p>
<h3>The code</h3>
{snippet("matched-market-test/src/geo.py", "pair_effect", "normal_posterior")}
<p><a href="{REPO}/matched-market-test">See the full test, checks, and unit tests on GitHub</a></p>
{nav_next('building-the-team', 'Building the team')}
</article>
"""
tail = 30
geo_js = f"""
const f=v=>v.toFixed(1);const p=v=>(v>0?'+':'')+(v*100).toFixed(1)+'%';
lineChart('ts',{{x:{json.dumps(geo['series']['week'][-tail:])},xName:'Week',xTitle:'Weeks from campaign start',fmt:f,label:'Leads indexed to the pre-period for test and control markets',marker:{{x:0,label:'Campaign starts'}},
 series:[{{name:'Test markets',color:'--s1',values:{json.dumps([round(v, 2) for v in geo['series']['treated'][-tail:]])}}},{{name:'Control markets',color:'--s2',values:{json.dumps([round(v, 2) for v in geo['series']['control'][-tail:]])}}}]}});
barChart('pr',{{label:'Estimated lift by market pair',labelW:90,valueName:'Lift (log points)',fmt:p,rows:{json.dumps([{'label': r['pair'], 'value': r['lift']} for r in geo['pairs']])}}});
"""

# ---------- team
team = """
<article class="hero">
<div class="kicker">Leadership</div>
<h1>Building the team</h1>
<p class="lede">I took over a small operational support team at a medical device division and built it to more than three times its size, into a regular voice in budget and strategy decisions. It's the third analytics practice I've built.</p>
<!--endband-->
<h2>What changed</h2>
<div class="tablewrap"><table><thead><tr><th></th><th>When I arrived</th><th>Now</th></tr></thead><tbody>
<tr><td>Team</td><td>A small support group</td><td>More than three times the size, with employees and contractors across data science, analytics, BI, and analytics engineering</td></tr>
<tr><td>Role</td><td>Operational support</td><td>A regular voice in budget and strategy decisions with the executive team</td></tr>
<tr><td>Influence</td><td></td><td>Work that informs an eight-figure annual budget in patient and physician marketing</td></tr>
</tbody></table></div>
<h2>How I built it</h2>
<ul>
<li><b>Hired for the foundation.</b> I brought on an analytics engineer and a data steward.</li>
<li><b>Set the standards behind every readout.</b> UTM and data quality rules, core reporting automated in Snowflake and dbt, Tableau dashboards for media and email journeys, and a Streamlit app for attribution and UTM governance.</li>
<li><b>Connected marketing to outcomes.</b> I set up ROI tracking from lead to completed procedure, with lead-to-patient matching in a PHI-protected environment. A holdout group would have cost too much, so we used causal inference modeling to estimate the effect. Shifting spend to what worked produced a double-digit lift in completed procedures.</li>
<li><b>Developed people.</b> I pushed the analysts to use AI every day for SQL and Python, and two analysts with no data science background moved into ETL and machine learning work. I also built a library of custom GPTs the team uses.</li>
<li><b>Partnered across functions.</b> IT, Finance, Sales, and Field Marketing on matched-market tests, Legal and IT on consent, Legal, Privacy, and IT on the AI agent, and Compliance and ad-promo review on content language.</li>
</ul>
<h2>The same pattern, earlier</h2>
<div class="tablewrap"><table><thead><tr><th>Where</th><th>What I built</th><th>What it did</th></tr></thead><tbody>
<tr><td>Catapult Marketing (Epsilon)</td><td>Founded the digital analytics practice, team of 5</td><td>Grew from 1 client to 11 Fortune 500 clients and helped win 8 new business pitches in 2 years</td></tr>
<tr><td>Fallon (Publicis Groupe)</td><td>Built the analytics, insights, and measurement practice, team of 3</td><td>Introduced multi-touch attribution, media mix modeling, and incrementality testing, and client media efficiency rose 10 to 25%</td></tr>
<tr><td>iRobot</td><td>Led a global data science, analytics, and consumer insights team of 5</td><td>My Python media mix models shifted global spend and raised media contribution margin</td></tr>
</tbody></table></div>
<p class="next">Next: <a href="catering.html">Automating catering inquiries, with approval</a></p>
</article>
"""

# ---------- retention
ret = json.loads((ROOT / "projects/retention-ltv/results/results.json").read_text())
st = ret["strategies"]
money = lambda v: ("-" if v < 0 else "") + f"${abs(v):,.0f}"
share = pct(st["Highest expected gain"]["share"], 0)
retention = f"""
<article class="hero">
<div class="kicker">Retention</div>
<h1>Retention and lifetime value: who should get the offer?</h1>
<p class="lede">I've built season ticket retention and lifetime value models for a professional sports team, and done lifetime value work for iRobot's online store. The question that matters is who an offer actually changes, and that often isn't the customer most likely to leave.</p>
<!--endband-->
<h2>Where I've done this</h2>
<ul>
<li><b>A professional sports team, on the agency side:</b> built retention, lifetime value, and acquisition cost models, and helped drive the season ticket package, retention, and upsell strategy built on them.</li>
<li><b>iRobot:</b> extended lifetime value analysis to the e-commerce business, alongside A/B and promotion testing.</li>
</ul>
<h2>Demo: a retention decision on made-up data</h2>
<p>The real data stays private, so everything from here down is simulated: a subscription business with {ret["train_customers"]:,} customers who were randomly offered, or not offered, a {money(ret["offer_cost"])} retention incentive. Some customers respond to the offer, some would stay or leave anyway, and a few become more likely to cancel when reminded.</p>
<ul>
<li><b>Churn:</b> a gradient boosting model for each arm of the test estimates how likely each customer is to stay, with and without the offer.</li>
<li><b>Lifetime value:</b> those estimates turn into expected active months over 24 months, multiplied by each customer's monthly margin.</li>
<li><b>Decision:</b> make the offer only when the lifetime value it adds is greater than what it costs.</li>
</ul>
<figure><figcaption>Demo: targeting by expected gain was the only rule that made money, per 1,000 new customers</figcaption><div id="rs"></div></figure>
<p>I compared the rules on {ret["new_customers"]:,} new customers, across {ret["runs"]} simulated businesses. The three targeted rules each reached the same {share} of customers, so the only difference is who got the offer. Going after the customers most likely to leave lost money, because many of them leave anyway. Targeting by expected gain won every time.</p>
<h3>Demo: how far to trust it</h3>
<ul>
<li>The model correctly decided whether to make an offer for {pct(ret["right_call"], 0)} of customers.</li>
<li>Churn predictions were well calibrated, with an AUC of {ret["auc"]:.2f}. Churn here is hard to predict customer by customer, which is realistic.</li>
<li>It overstated the gain: {money(ret["estimated_gain"])} promised per 1,000 customers against {money(ret["true_gain"])} delivered, since it favors customers whose gain it happens to overestimate. So I trust the ranking more than the dollar figure, and I'd roll out with a holdout to measure the real return.</li>
</ul>
<p>This also relies on a past randomized test. Without one, a model can only tell you who's likely to leave, not who an offer would change.</p>
<h3>The code</h3>
{snippet("retention-ltv/src/retention.py", "months_with_offer", "score")}
<p><a href="{REPO}/retention-ltv">See the full model and tests on GitHub</a></p>
<p class="next">Next: <a href="gpt-benchmark.html">GPT from scratch</a></p>
</article>
"""
ret_js = "barChart('rs',{label:'Net value per 1,000 customers by targeting rule',labelW:190,rightPad:80,valueName:'Net value per 1,000 customers',fmt:v=>(v<0?'-':'')+'$'+Math.abs(Math.round(v)).toLocaleString('en-US'),rows:%s});" % json.dumps(
    [{"label": k, "value": round(st[k]["mean"])} for k in ("Highest expected gain", "Offer to no one", "Highest lifetime value", "Highest churn risk", "Offer to everyone")])

# ---------- gpt
_nb = json.loads((ROOT / "projects/gpt-training-lab/notebooks/gpt_training_benchmark.ipynb").read_text())
_src = "\n".join("".join(c["source"]) for c in _nb["cells"] if c["cell_type"] == "code")
_tree = ast.parse(_src)
_cls = next(n for n in _tree.body if isinstance(n, ast.ClassDef) and "attention" in n.name.lower())
gpt_snippet = "<pre><code>" + html.escape("\n".join(_src.splitlines()[_cls.lineno - 1:_cls.end_lineno])) + "</code></pre>"
ev = list(csv.DictReader(open(ROOT / "projects/gpt-training-lab/results/evaluation_metrics.csv")))
gpt = f"""
<article class="hero">
<div class="kicker">Hands-on deep learning</div>
<h1>GPT from scratch, with GPU instrumentation</h1>
<p class="lede">I wrote a decoder-only Transformer in PyTorch and instrumented its training as a GPU benchmark. On an A100, the 202-million-parameter model trained at about 113,000 tokens per second, holding that pace for all 10,000 steps.</p>
<!--endband-->
<h2>What I built</h2>
<ul>
<li>Causal self-attention, Transformer blocks, and the full training loop, written directly in PyTorch.</li>
<li>Mixed precision, gradient accumulation, checkpointing, and model sizes that adapt to available GPU memory.</li>
<li>CUDA event timing, step-latency distributions, and GPU utilization, power, and temperature logging.</li>
</ul>
<h2>Benchmark results</h2>
<div class="tablewrap"><table><tbody>
<tr><td>GPU</td><td class="n">NVIDIA A100, 80GB</td></tr>
<tr><td>Model</td><td class="n">202M parameters, 16 layers</td></tr>
<tr><td>Training throughput</td><td class="n">about 113,000 tokens/sec</td></tr>
<tr><td>Median optimizer step</td><td class="n">435 ms</td></tr>
<tr><td>Step-time standard deviation</td><td class="n">2.7 ms</td></tr>
<tr><td>Tokens processed</td><td class="n">491.5 million</td></tr>
<tr><td>Mean GPU utilization</td><td class="n">98%</td></tr>
<tr><td>Peak VRAM</td><td class="n">10.7 GB of 79 GB</td></tr>
<tr><td>Run time</td><td class="n">about 76 minutes</td></tr>
</tbody></table></div>
<h2>What the loss curve says</h2>
<figure><figcaption>Validation loss bottoms out at 1.58 around step 750, then climbs as the model memorizes the data</figcaption><div id="ls"></div></figure>
<p>This is a stress test and not a useful text generator. A model this size memorizes a small dataset like Tiny Shakespeare, so training loss reached 0.03 while validation loss rose to 4.69. For real generation, I'd stop near step 750, use a smaller model, or train on much more data.</p>
<h3>The code</h3>
{gpt_snippet}
<p><a href="{REPO}/gpt-training-lab">See the full notebook and results on GitHub</a></p>
<p class="next">More: <a href="consumer-sentiment.html">Forecasting consumer sentiment</a></p>
</article>
"""
gpt_js = "const f=v=>v.toFixed(2);lineChart('ls',{{x:%s,xName:'Step',xTitle:'Optimizer step',fmt:f,ymin:0,label:'Training and validation loss by optimizer step',series:[{{name:'Validation loss',color:'--s2',values:%s}},{{name:'Training loss',color:'--s1',values:%s}}]}});".replace("{{", "{").replace("}}", "}") % (
    json.dumps([int(r["step"]) for r in ev]), json.dumps([round(float(r["val_loss"]), 3) for r in ev]), json.dumps([round(float(r["train_loss"]), 3) for r in ev]))

# ---------- catering
catering = """
<article class="hero">
<div class="kicker">Applied AI</div>
<h1>Automating catering inquiries, with human approval</h1>
<p class="lede">I built a Gmail-integrated AI automation for a restaurant owner's catering inquiries. A person approves everything it prepares, and by the owner's estimate it saves more than 10 hours a week.</p>
<!--endband-->
<h2>What it does</h2>
<p>When a catering inquiry reaches the inbox, the automation prepares the work and then stops for review.</p>
<div class="tablewrap"><table><thead><tr><th>Step</th><th>The automation</th><th>The owner</th></tr></thead><tbody>
<tr><td>Read</td><td>Reads the inquiry email</td><td></td></tr>
<tr><td>Reply</td><td>Drafts a response</td><td>Approves it before it goes out</td></tr>
<tr><td>Track</td><td>Puts the details into a spreadsheet</td><td>Approves the entry</td></tr>
<tr><td>Schedule</td><td>Holds a calendar event as a draft</td><td>Approves the event</td></tr>
</tbody></table></div>
<div class="result"><strong>Result:</strong> more than 10 hours a week back, by the owner's estimate, with nothing going out unreviewed.</div>
<h2>Why a person approves everything</h2>
<p>A catering inquiry can turn into a real commitment to a customer, so the automation does the repetitive work and leaves the decisions with the owner. It's the same approach I'd bring to any AI workflow that reaches customers.</p>
<p class="next">More: <a href="consumer-sentiment.html">Forecasting consumer sentiment</a></p>
</article>
"""

# ---------- capstone
models = read_csv("model_comparison.csv")
imp = read_csv("selected_feature_importance.csv")
scen = read_csv("scenario_analysis_results.csv")
corr = read_csv("selected_umcsent_correlations.csv")
lin = next(m for m in models if m["Model"] == "Linear")
recession = next(r for r in scen if r["scenario"] == "Mild Recession")
scen_rows = "".join(f'<tr><td>{r["scenario"]}</td><td class="n">{float(r["prediction"]):.1f}</td><td class="n">{float(r["pct_change"]):+.1f}%</td></tr>' for r in scen)
model_rows = "".join(f'<tr><td>{m["Model"]}</td><td class="n">{float(m["R²"]):.3f}</td><td class="n">{float(m["MAE"]):.2f}</td></tr>' for m in models)
capstone = f"""
<article class="hero">
<div class="kicker">Graduate work</div>
<h1>Forecasting consumer sentiment</h1>
<p class="lede">For my University of Michigan capstone, Paul Stotts, Ali Alrubaiee, and I forecast the Consumer Sentiment Index from more than 40 monthly FRED series. Our best-looking score was an R² of {float(lin['R²']):.3f}. The number I'd lead with is about 0.68.</p>
<!--endband-->
<h2>What I worked on</h2>
<p>I co-developed the Python modeling and analysis: lagged features, changes, rolling statistics, and spreads, followed by regularized regression and tree-based models with time-aware evaluation.</p>
<h2>Why the best score doesn't hold up</h2>
<div class="tablewrap"><table><thead><tr><th>Model (saved comparison)</th><th class="n">R²</th><th class="n">MAE</th></tr></thead><tbody>{model_rows}</tbody></table></div>
<p>A forecast that good should make you suspicious. Two things in our own outputs explain it:</p>
<ul>
<li>A three-month moving average of sentiment itself carried {float(imp[0]['importance']) * 100:.0f}% of feature importance. The model was mostly predicting sentiment from recent sentiment.</li>
<li>The scenarios barely moved the forecast, and a mild recession nudged sentiment up by {float(recession['pct_change']):.1f}%, which makes no economic sense. A model that responded to the economy would move more, and in the other direction.</li>
</ul>
<div class="tablewrap"><table><thead><tr><th>Scenario</th><th class="n">Forecast</th><th class="n">Change</th></tr></thead><tbody>{scen_rows}</tbody></table></div>
<p>The team separately reported a held-out LASSO R² of about 0.68 under a different protocol. The two numbers aren't directly comparable, and I'd lead with the lower one. If I picked this back up, the first thing I'd add is a naive baseline that just carries sentiment forward, so that every model has to beat it.</p>
<h2>What the correlations show</h2>
<figure><figcaption>Crude oil and gas prices had the strongest correlations with sentiment among these series</figcaption><div id="co"></div></figure>
<p>That's association, and it doesn't show cause. It's still useful for a planner deciding which indicators to watch.</p>
<p><a href="{REPO}/consumer-sentiment-capstone">See the saved results on GitHub</a>. The code stays in the team's private repository.</p>
</article>
"""
corr_sorted = sorted(corr, key=lambda r: abs(float(r["Pearson r"])), reverse=True)
cap_js = "barChart('co',{label:'Correlation of each indicator with consumer sentiment',labelW:210,valueName:'Pearson r',fmt:v=>v.toFixed(2),rows:%s});" % json.dumps(
    [{"label": r["label"], "value": round(float(r["Pearson r"]), 2)} for r in corr_sorted])

# ---------- write
(DOCS / "work").mkdir(parents=True, exist_ok=True)
(DOCS / "index.html").write_text(page("Dave Norine | Marketing Analytics, Data Science and AI", "Dave Norine builds analytics practices and the teams behind them. Case studies in media mix modeling, measurement, experimentation, and AI adoption.", home))
pages = [
    ("budget-cut", "Protecting Results Through a Double-Digit Budget Cut", "How media mix modeling guided a double-digit budget cut, with a working budget simulator on synthetic data.", budget, bud_js),
    ("signal-loss", "Rebuilding Measurement After Losing Most of Our Tracking", "How a KPI framework and work with Legal and IT carried measurement through a consent change.", signal, ""),
    ("ai-agent", "Taking an AI Agent From Pilot to Daily Use", "A governed AI agent for a patient contact center, and a working demo of how I build one.", agent, ""),
    ("matched-market", "Measuring Lift With Matched-Market Tests", "How to design a geo test and turn the read into a scale-or-stop decision.", market, geo_js),
    ("building-the-team", "Building the Team", "Building a small support team into a full analytics team, and two practices before it.", team, ""),
    ("catering", "Automating Catering Inquiries, With Approval", "A human-approved AI workflow that reads catering inquiries, drafts replies, tracks details, and holds calendar events.", catering, ""),
    ("retention-ltv", "Retention and Lifetime Value", "Churn and lifetime value models, and how to decide who should get a retention offer.", retention, ret_js),
    ("gpt-benchmark", "GPT From Scratch, With GPU Instrumentation", "A from-scratch Transformer in PyTorch, benchmarked at about 113,000 tokens per second on an A100.", gpt, gpt_js),
    ("consumer-sentiment", "Forecasting Consumer Sentiment", "A University of Michigan capstone, and why its best-looking score doesn't hold up.", capstone, cap_js),
]
for slug, title, desc, body, script in pages:
    (DOCS / "work" / f"{slug}.html").write_text(page(f"{title} | Dave Norine", desc, body, depth=1, script=script, art=slug))
print("built", len(pages) + 1, "pages")
