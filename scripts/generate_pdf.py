"""
WeGoComply — PDF Documentation Generator

Combines all 8 project documentation files into a single
professionally styled PDF.

Usage:
    python3 scripts/generate_pdf.py

Output:
    docs/WeGoComply_Project_Documentation.pdf
"""

import os
import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# ---------------------------------------------------------------------------
# Document order and titles
# ---------------------------------------------------------------------------
DOCS = [
    ("docs/1_PROBLEM_AND_PERSONA.md",   "1. Problem & Persona Definition"),
    ("docs/2_POLICY_PACK.md",           "2. Policy Pack"),
    ("docs/3_WORKFLOW_USER_JOURNEY.md", "3. Workflow & User Journey"),
    ("docs/4_SOLUTION_ARCHITECTURE.md", "4. Solution Architecture"),
    ("docs/5_RULES_ENGINE.md",          "5. Rules Engine Logic"),
    ("docs/6_AI_USAGE.md",              "6. AI Usage Explanation"),
    ("docs/7_TESTING_VALIDATION.md",    "7. Testing & Validation"),
    ("docs/8_FINAL_PITCH.md",           "8. Final Pitch Presentation"),
]

OUTPUT = "docs/WeGoComply_Project_Documentation.pdf"

# ---------------------------------------------------------------------------
# CSS Styling
# ---------------------------------------------------------------------------
CSS_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

@page {
    size: A4;
    margin: 20mm 18mm 20mm 18mm;
    @bottom-right {
        content: "WeGoComply — " counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #6b7280;
        font-family: Inter, sans-serif;
    }
    @top-left {
        content: "WeGoComply — AI-Powered Compliance Platform";
        font-size: 9pt;
        color: #6b7280;
        font-family: Inter, sans-serif;
    }
}

@page cover {
    margin: 0;
    @bottom-right { content: none; }
    @top-left { content: none; }
}

* {
    box-sizing: border-box;
}

body {
    font-family: Inter, 'Segoe UI', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1f2937;
    background: white;
}

/* Cover page */
.cover {
    page: cover;
    height: 297mm;
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1d4ed8 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 40mm;
    page-break-after: always;
}

.cover-logo {
    font-size: 48pt;
    font-weight: 700;
    color: white;
    letter-spacing: -1px;
    margin-bottom: 8pt;
}

.cover-shield {
    font-size: 60pt;
    margin-bottom: 16pt;
}

.cover-subtitle {
    font-size: 16pt;
    color: #93c5fd;
    font-weight: 400;
    margin-bottom: 32pt;
}

.cover-tagline {
    font-size: 12pt;
    color: #bfdbfe;
    margin-bottom: 48pt;
    font-style: italic;
}

.cover-meta {
    font-size: 10pt;
    color: #60a5fa;
    border-top: 1px solid #3b82f6;
    padding-top: 16pt;
    width: 100%;
}

.cover-meta p {
    margin: 4pt 0;
}

/* Section break page */
.section-break {
    page-break-before: always;
    page-break-after: always;
    height: 100mm;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 20mm;
    background: #f8fafc;
    border-left: 6pt solid #2563eb;
    margin: 0 -18mm;
    padding-left: 24mm;
}

.section-number {
    font-size: 48pt;
    font-weight: 700;
    color: #dbeafe;
    line-height: 1;
    margin-bottom: 8pt;
}

.section-title {
    font-size: 22pt;
    font-weight: 700;
    color: #1e3a8a;
    margin: 0;
}

/* Headings */
h1 {
    font-size: 20pt;
    font-weight: 700;
    color: #1e3a8a;
    border-bottom: 2pt solid #2563eb;
    padding-bottom: 6pt;
    margin-top: 24pt;
    margin-bottom: 12pt;
    page-break-after: avoid;
}

h2 {
    font-size: 14pt;
    font-weight: 700;
    color: #1e40af;
    margin-top: 20pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
}

h3 {
    font-size: 11.5pt;
    font-weight: 600;
    color: #1d4ed8;
    margin-top: 14pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
}

h4 {
    font-size: 10.5pt;
    font-weight: 600;
    color: #374151;
    margin-top: 10pt;
    margin-bottom: 4pt;
}

/* Paragraphs */
p {
    margin: 0 0 8pt 0;
    orphans: 3;
    widows: 3;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

thead {
    background: #1e3a8a;
    color: white;
}

thead th {
    padding: 7pt 10pt;
    text-align: left;
    font-weight: 600;
    font-size: 9pt;
}

tbody tr:nth-child(even) {
    background: #f0f4ff;
}

tbody tr:nth-child(odd) {
    background: white;
}

tbody td {
    padding: 6pt 10pt;
    border-bottom: 0.5pt solid #e5e7eb;
    vertical-align: top;
}

/* Code blocks */
pre {
    background: #0f172a;
    color: #e2e8f0;
    padding: 12pt;
    border-radius: 4pt;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 8pt;
    line-height: 1.5;
    overflow-x: auto;
    margin: 10pt 0;
    page-break-inside: avoid;
    border-left: 3pt solid #3b82f6;
}

code {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 8.5pt;
    background: #f1f5f9;
    color: #1e40af;
    padding: 1pt 4pt;
    border-radius: 2pt;
}

pre code {
    background: none;
    color: #e2e8f0;
    padding: 0;
}

/* Lists */
ul, ol {
    margin: 6pt 0 10pt 0;
    padding-left: 18pt;
}

li {
    margin-bottom: 3pt;
}

/* Blockquotes */
blockquote {
    border-left: 3pt solid #3b82f6;
    margin: 10pt 0;
    padding: 8pt 12pt;
    background: #eff6ff;
    color: #1e40af;
    font-style: italic;
}

/* Horizontal rule */
hr {
    border: none;
    border-top: 1pt solid #e5e7eb;
    margin: 16pt 0;
}

/* Strong / emphasis */
strong {
    font-weight: 700;
    color: #111827;
}

em {
    color: #374151;
}

/* Section content wrapper */
.section-content {
    page-break-before: always;
}

/* TOC */
.toc {
    page-break-after: always;
    padding: 20pt 0;
}

.toc h1 {
    font-size: 18pt;
    margin-bottom: 20pt;
}

.toc-item {
    display: flex;
    justify-content: space-between;
    padding: 6pt 0;
    border-bottom: 0.5pt dotted #d1d5db;
    font-size: 11pt;
}

.toc-number {
    color: #2563eb;
    font-weight: 600;
    min-width: 30pt;
}

.toc-title {
    flex: 1;
    padding: 0 8pt;
}
"""

# ---------------------------------------------------------------------------
# Cover page HTML
# ---------------------------------------------------------------------------
COVER_HTML = """
<div class="cover">
    <div class="cover-shield">🛡</div>
    <div class="cover-logo">WeGoComply</div>
    <div class="cover-subtitle">AI-Powered Compliance Platform for Nigerian Financial Institutions</div>
    <div class="cover-tagline">"Compliance that just works."</div>
    <div class="cover-meta">
        <p><strong>KYC Automation · Real-Time AML Monitoring · TIN Verification · SupTech Reporting</strong></p>
        <p>Built on Microsoft Azure AI · FIRS ATRS · CBN/NFIU Compliant</p>
        <p style="margin-top: 12pt; color: #93c5fd;">github.com/jvcByte/WeGoComply</p>
    </div>
</div>
"""

# ---------------------------------------------------------------------------
# Table of Contents HTML
# ---------------------------------------------------------------------------
TOC_ITEMS = [
    ("1", "Problem & Persona Definition"),
    ("2", "Policy Pack (5 Compliance Rules)"),
    ("3", "Workflow & User Journey"),
    ("4", "Solution Architecture"),
    ("5", "Rules Engine Logic Explanation"),
    ("6", "AI Usage Explanation"),
    ("7", "Testing & Validation Cases"),
    ("8", "Final Pitch Presentation"),
]

def build_toc():
    items_html = ""
    for num, title in TOC_ITEMS:
        items_html += f"""
        <div class="toc-item">
            <span class="toc-number">{num}.</span>
            <span class="toc-title">{title}</span>
        </div>"""
    return f"""
    <div class="toc">
        <h1>Table of Contents</h1>
        {items_html}
    </div>
    """

# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def read_md(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def md_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "codehilite", "toc", "nl2br"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False}
        }
    )

def build_section_break(number: str, title: str) -> str:
    return f"""
    <div class="section-break">
        <div class="section-number">{number}</div>
        <div class="section-title">{title}</div>
    </div>
    """

def generate_pdf():
    print("WeGoComply PDF Generator")
    print("=" * 40)

    # Build full HTML
    body_parts = [COVER_HTML, build_toc()]

    for i, (filepath, title) in enumerate(DOCS, 1):
        print(f"  Processing: {filepath}")
        if not os.path.exists(filepath):
            print(f"  WARNING: {filepath} not found, skipping")
            continue

        md_text = read_md(filepath)
        html_content = md_to_html(md_text)

        # Section break page
        num = str(i)
        short_title = title.split(". ", 1)[1] if ". " in title else title
        body_parts.append(build_section_break(num, short_title))

        # Section content
        body_parts.append(f'<div class="section-content">{html_content}</div>')

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>WeGoComply — Project Documentation</title>
    </head>
    <body>
        {''.join(body_parts)}
    </body>
    </html>
    """

    # Generate PDF
    print(f"\nGenerating PDF → {OUTPUT}")
    css = CSS(string=CSS_STYLE)
    HTML(string=full_html, base_url=".").write_pdf(
        OUTPUT,
        stylesheets=[css],
        presentational_hints=True,
    )

    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"Done! PDF saved: {OUTPUT} ({size_kb:.0f} KB)")
    print(f"\nOpen with: xdg-open {OUTPUT}")

if __name__ == "__main__":
    generate_pdf()
