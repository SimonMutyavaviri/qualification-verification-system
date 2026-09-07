"""Generate a Word guide for each teammate.

The guides are written for people who are not developers. They cover the
mechanics of contributing on GitHub in three routes, in order of how much
setup each needs:

  Route A - the GitHub website. No software at all.
  Route B - a terminal that runs inside the browser (GitHub Codespaces).
            Real commands, still nothing installed on the PC.
  Route C - a terminal on their own PC. Needs Git installed once.

They deliberately do NOT contain the code for each person's assigned task.
The assignment awards 15% for individual contribution and requires that
contributions are genuine, so each person writes their own change. The guides
give them the workflow, the file to open, the pattern to copy and the checks to
run.

Run: python scripts/build_teammate_guides.py
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "team-guides"

OWNER = "SimonMutyavaviri"
REPO = "qualification-verification-system"
REPO_URL = f"https://github.com/{OWNER}/{REPO}"
LIVE_URL = "https://qvs-mim736.fly.dev"

NAVY = RGBColor(0x0F, 0x17, 0x2A)
SLATE = RGBColor(0x47, 0x55, 0x69)
RED = RGBColor(0x9F, 0x12, 0x39)
GREEN = RGBColor(0x06, 0x5F, 0x46)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def shade(paragraph, hex_fill: str) -> None:
    """Give a paragraph a solid background colour."""
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    pPr.append(shd)


def command(doc: Document, text: str) -> None:
    """A command the reader copies and pastes."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(10)
    shade(p, "F1F5F9")


def callout(doc: Document, title: str, text: str, colour: RGBColor = SLATE,
            fill: str = "FFFBEB") -> None:
    """A highlighted box for warnings and important notes."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.15)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    t = p.add_run(f"{title}  ")
    t.bold = True
    t.font.color.rgb = colour
    t.font.size = Pt(10.5)
    b = p.add_run(text)
    b.font.size = Pt(10.5)
    b.font.color.rgb = NAVY
    shade(p, fill)


def step(doc: Document, number: int, text: str) -> None:
    """A numbered instruction."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_after = Pt(5)
    n = p.add_run(f"{number}.  ")
    n.bold = True
    n.font.color.rgb = NAVY
    p.add_run(text)


def bullet(doc: Document, text: str, bold_prefix: str = "") -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
    p.add_run(text)


def h(doc: Document, text: str, level: int = 1):
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = NAVY
    return heading


def para(doc: Document, text: str, size: float = 11, italic: bool = False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.italic = italic
    return p


def table(doc: Document, headers: list[str], rows: list[list[str]],
          widths: list[float] | None = None) -> None:
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, head in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = head
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(10)
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = value
            for p in cells[i].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(10)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()


def style_document(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.15
    for level, size in ((1, 18), (2, 14), (3, 12)):
        s = doc.styles[f"Heading {level}"]
        s.font.name = "Calibri"
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = NAVY


# ---------------------------------------------------------------------------
# Per-person configuration
# ---------------------------------------------------------------------------

TEAMMATES = [
    {
        "handle": "Progress861",
        "display": "Progress861",
        "filename": "GUIDE-Progress861.docx",
        "student": 2,
        "area": "Qualification Management",
        "plain_area": "the part of the system that registers and searches qualifications",
        "reviews": "AnesuCK",
        "reviewed_by": "SimonMutyavaviri",
        "needs_account": False,
        "task_title": "Make the qualification list sortable",
        "task_plain": (
            "At the moment the qualification register always shows the newest "
            "record first. A registry clerk who wants to see credentials in "
            "order of award date, or alphabetically by holder name, cannot. "
            "Your job is to let people sort the list by clicking a column heading."
        ),
        "task_files": [
            ("app/repositories/qualification_repository.py",
             "the search() function - this is where the ordering is decided"),
            ("app/routes/qualification_routes.py",
             "the list_qualifications() view - this reads what the user asked for"),
            ("app/templates/qualifications/list.html",
             "the table headings the user clicks"),
            ("tests/unit/test_qualification_service.py",
             "where you add tests proving sorting works"),
        ],
        "task_hint": (
            "Look at how the existing status filter works - it is passed from "
            "the route into search() and then used in the query. Sorting follows "
            "exactly the same path. IMPORTANT: never put the user's text straight "
            "into order_by(). Use a dictionary that maps allowed column names to "
            "real columns, and ignore anything not in it. There is a note about "
            "why in docs/collaboration-plan.md under Task 2.2."
        ),
        "issue_title": "[Task] Allow the qualification register to be sorted",
        "branch": "feature/qualifications-sortable-columns",
    },
    {
        "handle": "AnesuCK",
        "display": "AnesuCK",
        "filename": "GUIDE-AnesuCK.docx",
        "student": 3,
        "area": "Verification and Audit",
        "plain_area": "the part of the system that checks credentials and keeps the history",
        "reviews": "SimonMutyavaviri",
        "reviewed_by": "Progress861",
        "needs_account": False,
        "task_title": "Let the audit trail be filtered by date and exported",
        "task_plain": (
            "The audit trail is the permanent record of everything that has "
            "happened in the system. Right now you can only filter it by the type "
            "of action, and you cannot get the records out of the system at all. "
            "If an auditor asks 'show me everything that happened in March', "
            "nobody can answer. Your job is to add a date filter and a button "
            "that downloads the results as a spreadsheet file (CSV)."
        ),
        "task_files": [
            ("app/repositories/audit_repository.py",
             "the list_logs() function - where the filtering happens"),
            ("app/services/audit_service.py",
             "the layer the page talks to"),
            ("app/routes/admin_routes.py",
             "the audit() view and a new export view"),
            ("app/templates/admin/audit.html",
             "the filter form and the download button"),
            ("tests/integration/test_workflows.py",
             "where you add tests"),
        ],
        "task_hint": (
            "Copy the pattern of the existing action filter - it goes from the "
            "form, to the route, to list_logs(). Two things to be careful about: "
            "reject a date range where the end is before the start, and remember "
            "that exporting the audit trail is itself something that should be "
            "written into the audit trail. There is more detail in "
            "docs/collaboration-plan.md under Task 3.1."
        ),
        "issue_title": "[Task] Add date-range filtering and CSV export to the audit trail",
        "branch": "feature/audit-export-and-date-filter",
    },
    {
        "handle": "[HER GITHUB USERNAME]",
        "display": "third teammate",
        "filename": "GUIDE-third-teammate.docx",
        "student": 1,
        "area": "Login and User Management",
        "plain_area": "the part of the system that handles signing in and managing accounts",
        "reviews": "Progress861",
        "reviewed_by": "AnesuCK",
        "needs_account": True,
        "task_title": "Lock an account after repeated failed sign-in attempts",
        "task_plain": (
            "At the moment, if somebody keeps guessing passwords they are slowed "
            "down but never actually stopped. The system counts the failed "
            "attempts but does nothing with the count. Your job is to lock an "
            "account after five wrong passwords in a row, and unlock it "
            "automatically after fifteen minutes."
        ),
        "task_files": [
            ("app/models/user.py",
             "the User record - it already has failed_login_count; you add a "
             "locked_until date"),
            ("app/config.py",
             "where the five attempts and fifteen minutes are configured"),
            ("app/services/user_service.py",
             "the authenticate() function - this is where the locking decision goes"),
            ("tests/unit/test_auth_and_audit.py",
             "where you add tests"),
        ],
        "task_hint": (
            "Read the authenticate() function first. It already counts failures "
            "and resets the count on a successful sign-in, so you are adding to "
            "something that already works. One thing matters a lot: the message "
            "shown to a locked-out user must not tell an attacker whether the "
            "account exists. There is more detail in docs/collaboration-plan.md "
            "under Task 1.1."
        ),
        "issue_title": "[Task] Lock an account after repeated failed sign-in attempts",
        "branch": "feature/auth-account-lockout",
    },
]


# ---------------------------------------------------------------------------
# Document sections
# ---------------------------------------------------------------------------


def title_page(doc: Document, person: dict) -> None:
    t = doc.add_heading("Qualification Verification System", level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in t.runs:
        r.font.color.rgb = NAVY

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Your step-by-step contribution guide")
    r.font.size = Pt(15)
    r.font.color.rgb = SLATE

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"Prepared for: {person['display']}")
    r.font.size = Pt(13)
    r.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"Your area: {person['area']}\nMIM736 Practical Assignment")
    r.font.size = Pt(11)
    r.font.color.rgb = SLATE

    doc.add_paragraph()
    callout(
        doc,
        "You do not need to install anything.",
        "Everything in Part 1 to Part 6 of this guide happens on the GitHub "
        "website in your web browser. If you would rather type commands, Part 7 "
        "shows you how to do that in a terminal that also runs in your browser. "
        "Nothing has to be installed on your computer either way.",
        GREEN,
        "ECFDF5",
    )

    doc.add_page_break()


def why_section(doc: Document, person: dict) -> None:
    h(doc, "Part 1 - What this is and why it matters")

    para(doc,
         "Our team has built a system that lets a university register the "
         "qualifications it awards, and lets an employer check whether a "
         "certificate someone is showing them is genuine. It is finished and "
         "running on the internet right now:")
    command(doc, LIVE_URL)

    para(doc,
         "The code lives on a website called GitHub. Think of GitHub as a shared "
         "folder that remembers every single change anybody makes, who made it, "
         "and when:")
    command(doc, REPO_URL)

    h(doc, "Why you have to do this yourself", level=2)
    para(doc,
         "The assignment does not only mark the finished system. Fifteen percent "
         "of the total mark is for each person's individual contribution, and it "
         "is judged on evidence that GitHub records automatically: your commits, "
         "your branches, your pull requests and your code reviews.")
    para(doc,
         "That evidence has your name on it and cannot be transferred. If "
         "somebody else does your part, you get no marks for it, and the "
         "lecturer can see exactly who did what by looking at the repository. "
         "So the work in Part 6 has to be genuinely yours.")

    callout(
        doc,
        "The good news.",
        "The system already works. You are not building anything from nothing. "
        "You are making one improvement to something that already runs, and this "
        "guide walks you through every click.",
        GREEN,
        "ECFDF5",
    )

    h(doc, "Five words you will keep seeing", level=2)
    table(
        doc,
        ["Word", "What it actually means"],
        [
            ["Repository (or repo)",
             "The shared folder holding all our code and documents."],
            ["Branch",
             "Your own private copy of the folder to work in, so you cannot break "
             "anything while you experiment."],
            ["Commit",
             "Saving a change, with a short note explaining what you changed and "
             "why. This is what gets counted as your contribution."],
            ["Pull request (PR)",
             "Asking the team to look at your change and put it into the main "
             "version. This is where reviews happen."],
            ["Review",
             "Reading somebody else's change and either approving it or asking "
             "for something to be fixed."],
        ],
        [1.5, 4.7],
    )

    h(doc, "The order things happen in", level=2)
    para(doc,
         "Every change anybody makes follows the same six steps. You will do "
         "this twice: once as a practice run in Part 5, and once for real in "
         "Part 6.")
    for i, s in enumerate(
        [
            "Write an issue - a short note saying what you are going to do.",
            "Make a branch - your private copy to work in.",
            "Make your change and commit it - save it with a note.",
            "Open a pull request - ask the team to include your work.",
            "Wait for the automatic checks, then get a teammate to review it.",
            "Merge it - your change becomes part of the real system.",
        ],
        start=1,
    ):
        step(doc, i, s)

    doc.add_page_break()


def setup_section(doc: Document, person: dict) -> None:
    h(doc, "Part 2 - Getting in (do this first)")

    if person["needs_account"]:
        h(doc, "Step A - Create a GitHub account", level=2)
        para(doc, "Skip this if you already have one.")
        step(doc, 1, "Go to github.com/signup in your browser.")
        step(doc, 2, "Enter your email address, then choose a password and a username.")
        step(doc, 3,
             "Your username is what everybody will see. Something like your own "
             "name is ideal. Write it down - you will need it in a moment.")
        step(doc, 4, "Confirm your email address by clicking the link GitHub sends you.")
        step(doc, 5,
             f"Send your username to {OWNER} so he can invite you to the project. "
             "You cannot do anything else until he does.")
        callout(
            doc,
            "Use a real email you can open.",
            "GitHub sends a confirmation link and you cannot continue without "
            "clicking it.",
        )

    h(doc, "Step B - Accept the invitation", level=2)
    para(doc,
         f"{OWNER} has invited you to the project. Until you accept, you can "
         "look but not change anything.")
    step(doc, 1, "Check your email for a message from GitHub with 'invited you' in it.")
    step(doc, 2,
         "Click the green 'View invitation' button. If you cannot find the "
         "email, go straight to this address instead while signed in:")
    command(doc, f"{REPO_URL}/invitations")
    step(doc, 3, "Click 'Accept invitation'.")
    step(doc, 4, "You should now see the project files. That is it - you are in.")

    callout(
        doc,
        "Invitations expire after seven days.",
        f"If yours has expired, message {OWNER} and ask him to send it again.",
    )

    h(doc, "Step C - Have a look around", level=2)
    para(doc, "Before changing anything, spend five minutes looking at these:")
    table(
        doc,
        ["Where to click", "What you will see"],
        [
            ["The 'Code' tab",
             "All the files. The README on the front page explains the whole "
             "project."],
            ["The 'Issues' tab",
             "The list of jobs to be done. Yours will go here."],
            ["The 'Pull requests' tab",
             "Changes waiting to be reviewed and included."],
            ["The 'Actions' tab",
             "The automatic checking. Green tick means everything passed."],
            [LIVE_URL,
             "The actual working system. Ask " + OWNER + " for a login."],
        ],
        [1.9, 4.3],
    )

    doc.add_page_break()


def rules_section(doc: Document) -> None:
    h(doc, "Part 3 - Four rules that will save you trouble")

    h(doc, "Rule 1 - Never edit the main version directly", level=2)
    para(doc,
         "The 'main' and 'develop' versions are protected. If you try to change "
         "them directly, GitHub will stop you. This is deliberate and it is "
         "protecting you: it means you cannot accidentally break the working "
         "system. Always work on your own branch.")

    h(doc, "Rule 2 - Small changes are better than big ones", level=2)
    para(doc,
         "Three small changes that work are worth far more than one enormous "
         "change that does not. They are also much easier for a teammate to "
         "review, and each one is separately recorded as your contribution.")

    h(doc, "Rule 3 - Wait for the green tick", level=2)
    para(doc,
         "Every time you propose a change, the project automatically runs 264 "
         "tests against it. This takes about two minutes. A red cross means "
         "something is broken - do not ask for a review until it is green.")

    h(doc, "Rule 4 - Never type a password into a file", level=2)
    para(doc,
         "The project is public, so anybody can read it. If you ever put a "
         "password, a key or a token into a file and save it, treat it as leaked "
         f"and tell {OWNER} immediately.")

    callout(
        doc,
        "You cannot break anything permanently.",
        "Every change is recorded and can be undone. The protected main version "
        "cannot be damaged by anything you do on your own branch. Do not be "
        "afraid to try things.",
        GREEN,
        "ECFDF5",
    )

    doc.add_page_break()


def browser_workflow(doc: Document, person: dict) -> None:
    h(doc, "Part 4 - How to do everything in the browser")
    para(doc,
         "This is the reference section. Part 5 walks you through it with a real "
         "example, so you may prefer to read that first and come back here.")

    h(doc, "How to write an issue", level=2)
    step(doc, 1, f"Go to {REPO_URL}/issues")
    step(doc, 2, "Click the green 'New issue' button.")
    step(doc, 3,
         "You will be offered some templates. Choose 'Assigned task' and click "
         "'Get started'.")
    step(doc, 4, "Fill in the title and the boxes, then click 'Submit new issue'.")
    step(doc, 5,
         "Note the number it is given - something like #7. You will need it later.")

    h(doc, "How to make a branch", level=2)
    step(doc, 1, f"Go to the front page of the project: {REPO_URL}")
    step(doc, 2,
         "Just above the file list on the left there is a button showing the "
         "word 'main'. Click it.")
    step(doc, 3,
         "A box appears with 'Find or create a branch...'. First click 'main' in "
         "the list and change it to 'develop' - we always branch from develop.")
    step(doc, 4,
         "Click the button again, type your branch name into the box, and click "
         "'Create branch: ... from develop'.")
    callout(
        doc,
        "Check this carefully.",
        "The small print under the box must say 'from develop'. If it says 'from "
        "main', click 'main' in the list first and try again.",
    )

    h(doc, "How to change a file", level=2)
    step(doc, 1,
         "Make sure the branch button shows YOUR branch name, not 'main'. If it "
         "does not, click it and choose your branch.")
    step(doc, 2,
         "Click through the folders to the file you want. Folders are listed "
         "first, then files.")
    step(doc, 3,
         "Click the pencil icon near the top right of the file. If you do not "
         "see a pencil, you are not on your own branch - go back to step 1.")
    step(doc, 4, "Make your change in the box.")
    step(doc, 5, "Click the green 'Commit changes...' button at the top right.")
    step(doc, 6,
         "A box appears asking for a description. Fill it in following the "
         "pattern below, make sure 'Commit directly to the ... branch' is "
         "selected, and click 'Commit changes'.")

    h(doc, "How to write the commit description", level=2)
    para(doc,
         "The team uses a set pattern. The first line is short and starts with a "
         "word saying what kind of change it is:")
    table(
        doc,
        ["Start with", "When to use it"],
        [
            ["feat:", "You added something new"],
            ["fix:", "You corrected something that was wrong"],
            ["test:", "You added or changed tests"],
            ["docs:", "You changed documentation or text"],
            ["chore:", "Housekeeping - settings, tidying up"],
        ],
        [1.3, 4.9],
    )
    para(doc, "So the first line looks like one of these:")
    command(doc, "feat: allow the qualification list to be sorted by award date")
    command(doc, "docs: add my name to the team table in the README")
    para(doc,
         "In the larger 'extended description' box, write one or two sentences "
         "explaining WHY you made the change, and add the issue number on its "
         "own line at the bottom:")
    command(doc, "Closes #7")

    h(doc, "How to open a pull request", level=2)
    step(doc, 1,
         "After committing, GitHub usually shows a yellow bar saying your branch "
         "'had recent pushes' with a green 'Compare & pull request' button. "
         "Click it.")
    step(doc, 2,
         f"If you do not see the bar, go to {REPO_URL}/pulls and click 'New "
         "pull request', then choose your branch.")
    step(doc, 3,
         "IMPORTANT: at the top there are two dropdowns, 'base:' and 'compare:'. "
         "'base:' must say develop. 'compare:' must say your branch. Change "
         "'base:' if it says main.")
    step(doc, 4,
         "A form appears, already filled with headings. Complete it and tick the "
         "boxes that apply. Write 'Closes #7' with your issue number.")
    step(doc, 5, "Click 'Create pull request'.")
    step(doc, 6,
         "On the right-hand side, under 'Reviewers', click the gear icon and "
         f"choose {person['reviewed_by']}.")

    h(doc, "How to read the automatic checks", level=2)
    para(doc,
         "About thirty seconds after you open the pull request, a box appears at "
         "the bottom listing checks.")
    table(
        doc,
        ["What you see", "What it means", "What to do"],
        [
            ["Yellow dot", "Still running", "Wait about two minutes."],
            ["Green tick", "Everything passed", "Ask for your review."],
            ["Red cross", "Something is broken",
             "Click 'Details' next to the red one, scroll to the red text, and "
             "read the message. Then fix the file and commit again - the checks "
             "re-run by themselves."],
        ],
        [1.3, 1.9, 3.0],
    )

    h(doc, "How to review a teammate's work", level=2)
    para(doc,
         f"You are reviewing {person['reviews']}. This is required - you get "
         "marks for reviews you give, not only for your own code.")
    step(doc, 1, f"Go to {REPO_URL}/pulls and open their pull request.")
    step(doc, 2,
         "Click the 'Files changed' tab. Green lines were added, red lines were "
         "removed.")
    step(doc, 3,
         "To comment on a specific line, hover over it and click the blue plus "
         "sign that appears on the left.")
    step(doc, 4, "Type your comment and click 'Start a review'.")
    step(doc, 5,
         "When finished, click the green 'Review changes' button at the top "
         "right, choose 'Approve' or 'Request changes', and click 'Submit "
         "review'.")

    para(doc, "If you are not sure what to say, these are always fair questions:")
    bullet(doc, "Does what they did match what the issue asked for?")
    bullet(doc, "Did they add a test for the new behaviour?")
    bullet(doc, "Are the checks green?")
    bullet(doc, "Is there anything you did not understand? Ask - that is a useful review comment.")

    callout(
        doc,
        "Do not just click Approve.",
        "A review with no comments looks exactly like what it is. Write at least "
        "one real observation or question on every review you give - it is worth "
        "marks, and it is the whole point of reviewing.",
    )

    h(doc, "How to merge", level=2)
    para(doc, "Once the checks are green and your reviewer has approved:")
    step(doc, 1, "Open your pull request.")
    step(doc, 2, "Click the green 'Squash and merge' button at the bottom.")
    step(doc, 3, "Click 'Confirm squash and merge'.")
    step(doc, 4, "Click 'Delete branch' when it offers. This is just tidying up.")
    step(doc, 5, "Your issue closes by itself if you wrote 'Closes #7' correctly.")

    doc.add_page_break()


def practice_section(doc: Document, person: dict) -> None:
    h(doc, "Part 5 - Your practice run (do this today, it takes 20 minutes)")

    para(doc,
         "Before your real task, do this small one. It is a genuine change that "
         "the project actually needs - the team table in the README still has "
         "blank placeholders where our names should be. It is also completely "
         "safe: it is a text file, so you cannot break the system.")

    callout(
        doc,
        "The point of this exercise.",
        "It takes you through the entire process from start to finish once, so "
        "that when you do your real task you already know where every button is.",
        GREEN,
        "ECFDF5",
    )

    h(doc, "Step 1 - Write the issue", level=2)
    step(doc, 1, f"Go to {REPO_URL}/issues and click 'New issue'.")
    step(doc, 2, "Choose 'Assigned task' and click 'Get started'.")
    step(doc, 3, "Title:")
    command(doc, "[Task] Add my name to the team table in the README")
    step(doc, 4, "In the body, write something like:")
    command(doc,
            "The team table in README.md still shows [INSERT NAME] placeholders.\n"
            "I am filling in my own row.\n\n"
            "Acceptance criteria:\n"
            "- [ ] My name and student number replace the placeholder\n"
            "- [ ] My area of responsibility is correct\n"
            "- [ ] The automatic checks pass")
    step(doc, 5, "Click 'Submit new issue' and write down the number you get.")

    h(doc, "Step 2 - Make your branch", level=2)
    step(doc, 1, f"Go to {REPO_URL}")
    step(doc, 2, "Click the branch button (it says 'main').")
    step(doc, 3, "Click 'develop' in the list to switch to it.")
    step(doc, 4, "Click the branch button again and type this name:")
    command(doc, f"docs/add-{person['handle'].lower()}-to-team-table")
    step(doc, 5, "Click 'Create branch: ... from develop'. Check it says 'from develop'.")

    h(doc, "Step 3 - Make the change", level=2)
    step(doc, 1, "Check the branch button now shows your new branch name.")
    step(doc, 2, "Click on 'README.md' in the file list.")
    step(doc, 3, "Click the pencil icon at the top right.")
    step(doc, 4,
         "Press Ctrl+F and search for 'INSERT NAME' to find the team table near "
         "the bottom.")
    step(doc, 5,
         "Replace the placeholder on YOUR row only - leave the others alone. "
         "Your row is the one that says:")
    command(doc, f"| `[INSERT NAME]` `[INSERT STUDENT NUMBER]` | {AREA_LOOKUP[person['student']]} |")
    step(doc, 6, "Change it to your real name and student number, for example:")
    command(doc, f"| Jane Moyo M123456 | {AREA_LOOKUP[person['student']]} |")
    step(doc, 7, "Click the green 'Commit changes...' button.")
    step(doc, 8, "In the first box put:")
    command(doc, "docs: add my name to the team table")
    step(doc, 9, "In the description box put (using your real issue number):")
    command(doc, "Fills in my row of the team table, which still held a\n"
                 "placeholder.\n\nCloses #7")
    step(doc, 10, "Click 'Commit changes'.")

    h(doc, "Step 4 - Open the pull request", level=2)
    step(doc, 1, "Click the green 'Compare & pull request' button in the yellow bar.")
    step(doc, 2, "Check 'base:' says develop. Change it if it says main.")
    step(doc, 3, "Fill in the form. Write 'Closes #7' with your number.")
    step(doc, 4, "Click 'Create pull request'.")
    step(doc, 5, f"On the right, add {person['reviewed_by']} as a reviewer.")

    h(doc, "Step 5 - Wait for the green tick", level=2)
    para(doc,
         "Scroll to the bottom of your pull request. Wait about two minutes and "
         "refresh the page. You want to see 'All checks have passed'.")

    h(doc, "Step 6 - Get it reviewed and merge it", level=2)
    step(doc, 1, f"Message {person['reviewed_by']} and ask them to review it.")
    step(doc, 2, "When they approve, click 'Squash and merge', then confirm.")
    step(doc, 3, "Click 'Delete branch'.")

    callout(
        doc,
        "You have now done the whole process.",
        "Issue, branch, commit, pull request, automatic checks, review, merge. "
        "Your real task in Part 6 is exactly the same sequence - only the change "
        "itself is different.",
        GREEN,
        "ECFDF5",
    )

    doc.add_page_break()


AREA_LOOKUP = {
    1: "Authentication, backend hardening, user management",
    2: "Qualification management",
    3: "Verification and audit",
    4: "DevOps, QA, Docker and deployment",
}


def task_section(doc: Document, person: dict) -> None:
    h(doc, "Part 6 - Your real task")

    p = doc.add_paragraph()
    r = p.add_run(person["task_title"])
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = NAVY

    h(doc, "What the problem is", level=2)
    para(doc, person["task_plain"])

    h(doc, "Where to look", level=2)
    para(doc, "These are the files involved. Read them before changing anything:")
    table(
        doc,
        ["File", "What it does"],
        [[f, d] for f, d in person["task_files"]],
        [2.6, 3.6],
    )

    h(doc, "How to approach it", level=2)
    para(doc, person["task_hint"])
    para(doc,
         "The full description, with the complete list of things your change "
         "must do, is in the project itself. Open this file and find your "
         "section:")
    command(doc, "docs/collaboration-plan.md")

    h(doc, "The steps", level=2)
    step(doc, 1, "Write the issue. Use this title:")
    command(doc, person["issue_title"])
    step(doc, 2, "Copy the acceptance criteria from docs/collaboration-plan.md into it.")
    step(doc, 3, "Make your branch from develop, named:")
    command(doc, person["branch"])
    step(doc, 4,
         "Make your change. Do it in several small commits rather than one big "
         "one - it is easier and it shows more clearly what you did.")
    step(doc, 5,
         "Add at least one test. Open the test file listed above and copy the "
         "shape of a test that is already there.")
    step(doc, 6, "Open the pull request and wait for the checks.")
    step(doc, 7, f"Ask {person['reviewed_by']} to review it.")
    step(doc, 8, "Fix anything they raise, then merge.")

    callout(
        doc,
        "This must be your own work.",
        "The lecturer can see exactly who wrote what. Ask teammates for help "
        "understanding something - that is normal and fine - but the commits "
        "must be yours. If somebody else writes it, you get no mark for it.",
        RED,
        "FFF1F2",
    )

    h(doc, "If you get stuck", level=2)
    bullet(doc, "Read the error message. It usually says exactly what is wrong.",
           "Start here: ")
    bullet(doc, "Look at how something similar was already done in the same file. "
                "Almost everything you need already has an example.")
    bullet(doc, "Make a smaller change. Get one small piece working, commit it, "
                "then do the next piece.")
    bullet(doc, f"Ask {OWNER}. Send him the link to your pull request and the red "
                "error text.")
    bullet(doc, "Comment on your own pull request describing what you tried. That "
                "is a real record of problem-solving, and your individual report "
                "asks for exactly that.")

    doc.add_page_break()


def commands_section(doc: Document, person: dict) -> None:
    h(doc, "Part 7 - If you would rather type commands")

    para(doc,
         "Everything above can be done by pointing and clicking. If you would "
         "prefer to type commands, you have two options.")

    h(doc, "Option 1 - A terminal inside your browser (nothing to install)", level=2)
    para(doc,
         "GitHub can give you a full computer running in your browser, with all "
         "the tools already set up. Nothing is installed on your own PC.")
    step(doc, 1, f"Go to {REPO_URL}")
    step(doc, 2, "Click the green 'Code' button.")
    step(doc, 3, "Click the 'Codespaces' tab in the little window that opens.")
    step(doc, 4, "Click 'Create codespace on develop'.")
    step(doc, 5,
         "Wait about a minute. A code editor opens in your browser with a black "
         "terminal panel at the bottom.")
    step(doc, 6, "Type the commands below into that terminal, pressing Enter after each.")

    callout(
        doc,
        "Free allowance.",
        "GitHub gives every account free Codespaces hours each month, which is "
        "far more than this project needs. Click 'Stop codespace' when you "
        "finish for the day so you do not use it up.",
    )

    h(doc, "Option 2 - On your own PC (one install)", level=2)
    para(doc,
         "If you want the commands on your own machine, you need Git. It is one "
         "small free program. Open the Start menu, type 'cmd', open Command "
         "Prompt, and paste:")
    command(doc, "winget install --id Git.Git -e")
    para(doc, "Close Command Prompt, open it again, and check it worked:")
    command(doc, "git --version")
    para(doc, "Then download the project into a folder on your PC:")
    command(doc, f"cd %USERPROFILE%\\Documents\ngit clone {REPO_URL}.git\ncd {REPO}")
    para(doc, "Tell Git who you are - use the email on your GitHub account:")
    command(doc,
            'git config user.name "Your Name"\n'
            'git config user.email "your-github-email@example.com"')
    callout(
        doc,
        "The email matters.",
        "GitHub matches your commits to your account by email address. If you "
        "use the wrong one, your work will not be credited to you and you lose "
        "the evidence for your individual mark.",
        RED,
        "FFF1F2",
    )

    h(doc, "The commands themselves", level=2)
    para(doc,
         "These are the same in the browser terminal and on your own PC. This is "
         "the whole cycle, in order.")

    para(doc, "Start a new piece of work - get the latest version, then branch:")
    command(doc,
            "git checkout develop\n"
            "git pull origin develop\n"
            f"git checkout -b {person['branch']}")

    para(doc, "See what you have changed:")
    command(doc, "git status")

    para(doc, "Save your change with a note:")
    command(doc,
            "git add .\n"
            'git commit -m "feat: short description of what you did"')

    para(doc, "Send it up to GitHub:")
    command(doc, f"git push -u origin {person['branch']}")

    para(doc,
         "The output includes a link. Open it in your browser to create the pull "
         "request, then carry on from Part 4.")

    para(doc, "Later, to add more changes to the same branch:")
    command(doc,
            "git add .\n"
            'git commit -m "test: add a test for the new behaviour"\n'
            "git push")

    para(doc, "To check your own work before pushing (browser terminal only):")
    command(doc, "pytest -q")

    h(doc, "Commands you may need to get out of trouble", level=2)
    table(
        doc,
        ["Problem", "Command"],
        [
            ["I want to throw away my changes to one file",
             "git restore path/to/file.py"],
            ["I want to see what I changed", "git diff"],
            ["I want to see my commits", "git log --oneline"],
            ["Which branch am I on?", "git branch"],
            ["Switch back to develop", "git checkout develop"],
            ["My branch is behind develop",
             "git merge origin/develop"],
        ],
        [2.9, 3.3],
    )

    callout(
        doc,
        "Never use these.",
        "git push --force and git reset --hard can permanently destroy other "
        f"people's work. If somebody tells you to run either, check with {OWNER} "
        "first.",
        RED,
        "FFF1F2",
    )

    doc.add_page_break()


def evidence_section(doc: Document, person: dict) -> None:
    h(doc, "Part 8 - Screenshots you must take")

    para(doc,
         "You need these for your individual report, which is worth 15% on its "
         "own. Take them as you go - it is very hard to recreate them later, and "
         "recreated ones look wrong.")

    para(doc,
         "To take a screenshot on Windows: press the Windows key, Shift and S "
         "together, drag a box around what you want, then paste it into a "
         "document with Ctrl+V.")

    table(
        doc,
        ["#", "What to capture", "Done"],
        [
            ["1", "The issue you wrote, showing the acceptance criteria", ""],
            ["2", "Your branch in the branch list", ""],
            ["3", "Your commits, showing your name next to them", ""],
            ["4", "Your pull request, with the description filled in", ""],
            ["5", "The checks passing - the green 'All checks have passed'", ""],
            ["6", "A check FAILING, if it ever does (this is worth marks)", ""],
            ["7", "The review you received", ""],
            ["8", f"The review you GAVE to {person['reviews']}, showing your comments", ""],
            ["9", "The pull request after it was merged", ""],
            ["10", "Your contribution graph (Insights tab, then Contributors)", ""],
        ],
        [0.4, 5.3, 0.5],
    )

    callout(
        doc,
        "Include the address bar.",
        "A screenshot that shows the web address and the date is evidence. One "
        "that shows only text could be anything.",
    )

    h(doc, "Your individual report", level=2)
    para(doc,
         "There is a template waiting for you in the project. Open this file and "
         "fill it in:")
    command(doc, f"reports/student-{person['student']}-individual-report.md")
    para(doc,
         "It asks for your commit numbers, your pull request numbers, what you "
         "found difficult and what you learned. Write about real difficulties. "
         "A genuine small problem you solved reads far better than an invented "
         "impressive one, and lecturers can tell the difference.")

    doc.add_page_break()


def troubleshooting_section(doc: Document, person: dict) -> None:
    h(doc, "Part 9 - When something goes wrong")

    table(
        doc,
        ["What you see", "What it means and what to do"],
        [
            ["There is no pencil icon on the file",
             "You are looking at the protected main version. Click the branch "
             "button at the top left and switch to your own branch."],
            ["'You must have write access'",
             "You have not accepted the invitation yet, or you are signed in as "
             "the wrong person. Check the top right corner of GitHub."],
            ["A red cross on my pull request",
             "Click 'Details' beside the failing check, scroll down to the red "
             "text and read it. It names the file and the line. Fix it, commit "
             "again, and the checks re-run automatically."],
            ["'This branch has conflicts that must be resolved'",
             "You and somebody else changed the same lines. GitHub shows a "
             "'Resolve conflicts' button. It shows both versions - keep both "
             "people's work unless it obviously makes no sense, delete the "
             "<<<<<<< and ======= and >>>>>>> marker lines, then click 'Mark as "
             "resolved'. Ask " + OWNER + " if unsure - this one is genuinely "
             "tricky."],
            ["'Merging is blocked'",
             "Either the checks are not green yet, or nobody has approved it "
             "yet. The page tells you which."],
            ["I committed to the wrong branch",
             "Nothing is lost. Tell " + OWNER + " - it takes him a minute to "
             "move it."],
            ["I cannot find my pull request",
             REPO_URL + "/pulls - then click 'Closed' if it has been merged "
             "already."],
        ],
        [1.9, 4.3],
    )

    h(doc, "Who to ask", level=2)
    para(doc,
         f"{OWNER} set the project up and knows all of it. When you ask, send "
         "him three things: the link to your pull request, a screenshot of the "
         "error, and what you were trying to do. That is enough for him to "
         "answer straight away.")

    h(doc, "A last word", level=2)
    para(doc,
         "Every developer gets red crosses and confusing errors, every single "
         "day. It is not a sign that you are doing badly - it is how the work "
         "goes. The checks exist to catch mistakes before they matter, which is "
         "exactly what they are doing when they fail. Read the message, change "
         "one thing, try again.")


# ---------------------------------------------------------------------------


def build_guide(person: dict) -> Path:
    doc = Document()
    style_document(doc)

    title_page(doc, person)
    why_section(doc, person)
    setup_section(doc, person)
    rules_section(doc)
    browser_workflow(doc, person)
    practice_section(doc, person)
    task_section(doc, person)
    commands_section(doc, person)
    evidence_section(doc, person)
    troubleshooting_section(doc, person)

    path = OUT / person["filename"]
    doc.save(path)
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Writing guides to {OUT.relative_to(ROOT)}/\n")
    for person in TEAMMATES:
        path = build_guide(person)
        print(f"  {path.name}  (Student {person['student']} - {person['area']})")
    print("\nDone.")


if __name__ == "__main__":
    main()
