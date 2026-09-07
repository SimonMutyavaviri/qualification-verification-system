"""Convert the Markdown deliverables into the .docx / .pptx / .xlsx files the
assignment asks for.

The Markdown files in reports/ and docs/ remain the source of truth: they are
diffable, reviewable in a pull request, and version-controlled. This script
renders them into Office formats for submission, so the two can never drift.

Run: python scripts/build_office_documents.py

Requires: python-docx, python-pptx, openpyxl (in requirements-dev.txt).
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from pptx import Presentation
from pptx.util import Inches as PptInches
from pptx.util import Pt as PptPt

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"
OUT = REPORTS / "submission"

# Markdown inline markers we strip when rendering to Word/PowerPoint.
_INLINE = re.compile(r"(\*\*|__|`)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def clean(text: str) -> str:
    """Strip Markdown inline syntax, keeping the visible text."""
    text = _LINK.sub(r"\1", text)
    return _INLINE.sub("", text).strip()


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def is_separator_row(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:\-|]+\|", line.strip()))


def split_row(line: str) -> list[str]:
    return [clean(cell) for cell in line.strip().strip("|").split("|")]


# ---------------------------------------------------------------------------
# Word
# ---------------------------------------------------------------------------


def style_document(doc: Document) -> None:
    """Apply a readable, conventional academic style."""
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.15

    for level, size in ((1, 20), (2, 16), (3, 13), (4, 12)):
        try:
            heading = doc.styles[f"Heading {level}"]
        except KeyError:  # pragma: no cover - style set varies by template
            continue
        heading.font.name = "Calibri"
        heading.font.size = Pt(size)
        heading.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        heading.font.bold = True


def add_table(doc: Document, rows: list[list[str]]) -> None:
    """Render a Markdown table as a real Word table."""
    if not rows:
        return
    width = max(len(r) for r in rows)
    table = doc.add_table(rows=0, cols=width)
    table.style = "Light Grid Accent 1"
    for index, row in enumerate(rows):
        cells = table.add_row().cells
        for col in range(width):
            value = row[col] if col < len(row) else ""
            cells[col].text = value
            if index == 0:
                for paragraph in cells[col].paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
    doc.add_paragraph()


def markdown_to_docx(md_path: Path, out_path: Path, subtitle: str = "") -> None:
    """Render one Markdown file to .docx."""
    doc = Document()
    style_document(doc)

    lines = md_path.read_text(encoding="utf-8").splitlines()

    table_buffer: list[list[str]] = []
    in_code = False
    code_lines: list[str] = []

    def flush_table() -> None:
        nonlocal table_buffer
        if table_buffer:
            add_table(doc, table_buffer)
            table_buffer = []

    def flush_code() -> None:
        nonlocal code_lines
        if code_lines:
            paragraph = doc.add_paragraph()
            run = paragraph.add_run("\n".join(code_lines))
            run.font.name = "Consolas"
            run.font.size = Pt(9)
            paragraph.paragraph_format.left_indent = Inches(0.3)
            code_lines = []

    for raw in lines:
        line = raw.rstrip()

        if line.strip().startswith("```"):
            if in_code:
                flush_code()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(raw)
            continue

        if is_table_row(line):
            if not is_separator_row(line):
                table_buffer.append(split_row(line))
            continue
        flush_table()

        if not line.strip():
            continue

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = clean(line.lstrip("#").strip())
            if level == 1 and not doc.paragraphs:
                title = doc.add_heading(text, level=0)
                title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if subtitle:
                    para = doc.add_paragraph(subtitle)
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    para.runs[0].font.size = Pt(13)
                    para.runs[0].font.color.rgb = RGBColor(0x47, 0x55, 0x69)
            else:
                doc.add_heading(text, level=min(level, 4))
            continue

        if re.fullmatch(r"[-*_]{3,}", line.strip()):
            continue

        if line.strip().startswith(("- ", "* ", "+ ")):
            text = clean(line.strip()[2:])
            if text.startswith("[ ] ") or text.startswith("[x] "):
                text = ("\u2610 " if text.startswith("[ ]") else "\u2611 ") + text[4:]
            doc.add_paragraph(text, style="List Bullet")
            continue

        if re.match(r"^\d+\.\s", line.strip()):
            doc.add_paragraph(clean(re.sub(r"^\d+\.\s", "", line.strip())), style="List Number")
            continue

        if line.strip().startswith(">"):
            para = doc.add_paragraph(clean(line.strip().lstrip(">").strip()))
            para.paragraph_format.left_indent = Inches(0.4)
            for run in para.runs:
                run.font.italic = True
                run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
            continue

        doc.add_paragraph(clean(line))

    flush_code()
    flush_table()
    doc.save(out_path)
    print(f"  {out_path.name}")


# ---------------------------------------------------------------------------
# PowerPoint
# ---------------------------------------------------------------------------


def markdown_to_pptx(md_path: Path, out_path: Path) -> None:
    """Render presentation.md into a .pptx deck.

    Slides are delimited by '## Slide N' headings; italic speaker-note lines
    become real PowerPoint speaker notes.
    """
    prs = Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.5)

    text = md_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n---\n", text)

    for block in blocks:
        lines = [ln.rstrip() for ln in block.strip().splitlines()]
        if not lines:
            continue
        header = next((ln for ln in lines if ln.startswith("## Slide")), None)
        if header is None:
            continue

        # The "## Slide N - Label" line is a fallback title. When the slide
        # body carries its own '#' heading, that is the real title.
        fallback_title = ""
        title = ""
        body: list[tuple[int, str]] = []
        notes: list[str] = []
        in_code = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Slide"):
                fallback_title = clean(re.split(r"\s[-—]\s", stripped, maxsplit=1)[-1])
                continue
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if stripped.startswith("*Speaker notes"):
                notes.append(clean(stripped.strip("*")))
                continue
            if not stripped or re.fullmatch(r"[-*_]{3,}", stripped):
                continue
            if stripped.startswith("#"):
                heading = clean(stripped.lstrip("#").strip())
                if not title:
                    title = heading
                else:
                    body.append((0, heading))
                continue
            if is_separator_row(stripped):
                continue
            if is_table_row(stripped):
                body.append((1, " · ".join(c for c in split_row(stripped) if c)))
                continue
            if stripped.startswith(("- ", "* ")):
                body.append((0, clean(stripped[2:])))
                continue
            if re.match(r"^\d+\.\s", stripped):
                body.append((0, clean(stripped)))
                continue
            if stripped.startswith(">"):
                body.append((1, clean(stripped.lstrip(">").strip())))
                continue
            if in_code:
                body.append((1, stripped))
                continue
            body.append((0, clean(stripped)))

        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = title or fallback_title or "Slide"
        slide.shapes.title.text_frame.paragraphs[0].runs[0].font.size = PptPt(34)

        if body:
            box = slide.shapes.add_textbox(
                PptInches(0.8), PptInches(1.9), PptInches(11.7), PptInches(4.9)
            )
            frame = box.text_frame
            frame.word_wrap = True
            for index, (level, content) in enumerate(body[:12]):
                para = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
                para.text = content
                para.level = level
                for run in para.runs:
                    run.font.size = PptPt(20 if level == 0 else 17)

        if notes:
            slide.notes_slide.notes_text_frame.text = "\n".join(notes)

    prs.save(out_path)
    print(f"  {out_path.name} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------


def test_cases_to_xlsx(md_path: Path, out_path: Path) -> None:
    """Render every table in the test-case document to one Excel workbook."""
    workbook = Workbook()
    workbook.remove(workbook.active)

    header_fill = PatternFill("solid", fgColor="0F172A")
    header_font = Font(color="FFFFFF", bold=True, size=11)

    current_section = "Test Cases"
    rows: list[list[str]] = []
    sheet_index = 0

    def flush() -> None:
        nonlocal rows, sheet_index
        if len(rows) < 2:
            rows = []
            return
        sheet_index += 1
        # Excel sheet names are capped at 31 characters and cannot contain []:*?/\
        name = re.sub(r"[\[\]:*?/\\]", "", f"{sheet_index}. {current_section}")[:31]
        sheet = workbook.create_sheet(name)
        for row in rows:
            sheet.append(row)
        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        for column in range(1, sheet.max_column + 1):
            longest = max(
                (
                    len(str(sheet.cell(row=r, column=column).value or ""))
                    for r in range(1, sheet.max_row + 1)
                ),
                default=10,
            )
            sheet.column_dimensions[get_column_letter(column)].width = min(max(longest + 2, 12), 60)
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        sheet.freeze_panes = "A2"
        rows = []

    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            flush()
            current_section = clean(re.sub(r"^##\s*\d*\.?\s*", "", line))
            continue
        if is_table_row(line):
            if not is_separator_row(line):
                rows.append(split_row(line))
            continue
        flush()
    flush()

    workbook.save(out_path)
    print(f"  {out_path.name} ({len(workbook.sheetnames)} sheets)")


# ---------------------------------------------------------------------------

DOCX_TARGETS = [
    (REPORTS / "technical-report.md", "technical-report.docx", "MIM736 Practical Assignment"),
    (
        REPORTS / "demonstration-script.md",
        "demonstration-script.docx",
        "10-15 minute demonstration",
    ),
    (REPORTS / "viva-preparation.md", "viva-preparation.docx", "36 questions with answers"),
    (
        REPORTS / "deployment-verification.md",
        "deployment-verification.docx",
        "Live deployment evidence",
    ),
    (REPORTS / "student-1-individual-report.md", "student-1-individual-report.docx", ""),
    (REPORTS / "student-2-individual-report.md", "student-2-individual-report.docx", ""),
    (REPORTS / "student-3-individual-report.md", "student-3-individual-report.docx", ""),
    (REPORTS / "student-4-individual-report.md", "student-4-individual-report.docx", ""),
    (DOCS / "user-manual.md", "user-manual.docx", "End-user guide"),
    (
        DOCS / "requirements-traceability.md",
        "requirements-traceability.docx",
        "Requirement to test to CI check",
    ),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Building submission documents into {OUT.relative_to(ROOT)}/\n")

    print("Word documents:")
    for source, name, subtitle in DOCX_TARGETS:
        if source.exists():
            markdown_to_docx(source, OUT / name, subtitle)
        else:
            print(f"  SKIPPED (missing): {source.name}")

    print("\nPresentation:")
    presentation = REPORTS / "presentation.md"
    if presentation.exists():
        markdown_to_pptx(presentation, OUT / "presentation.pptx")

    print("\nSpreadsheet:")
    test_cases = DOCS / "test-cases.md"
    if test_cases.exists():
        test_cases_to_xlsx(test_cases, OUT / "test-cases.xlsx")

    print("\nDone. The Markdown files remain the source of truth;")
    print("re-run this script after editing them.")


if __name__ == "__main__":
    main()
