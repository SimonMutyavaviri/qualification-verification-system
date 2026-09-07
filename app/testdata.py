"""Test dataset for demonstration, manual testing and the viva.

Three universities, seven staff accounts and a deliberately varied register of
qualifications: valid, expiring soon, expired, revoked, records with missing
holder contact details, and one holder carrying an unusual number of
credentials. The spread exists so that every screen, every verification result
and every review-assistant signal can be demonstrated with real data rather
than being described.

Credential IDs are fixed and readable so they can be quoted in a demonstration,
and they avoid the characters O, 0, I and 1 for the same reason the generator
does: those get misread off a printed certificate.

No password appears in this file. ``flask seed-testdata`` reads them from the
environment or generates strong random ones and prints them once.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.models.enums import QualificationStatus, Role, VerificationResult

TODAY = date.today()


def _days(n: int) -> date:
    """A date ``n`` days before today (negative n gives a future date)."""
    return TODAY - timedelta(days=n)


# ---------------------------------------------------------------------------
# Institutions - three universities
# ---------------------------------------------------------------------------

UNIVERSITIES = [
    {
        "code": "MSU",
        "name": "Midlands State University",
        "country": "Zimbabwe",
        "contact_email": "registry@msu.ac.zw",
    },
    {
        "code": "UZ",
        "name": "University of Zimbabwe",
        "country": "Zimbabwe",
        "contact_email": "registry@uz.ac.zw",
    },
    {
        "code": "NUST",
        "name": "National University of Science and Technology",
        "country": "Zimbabwe",
        "contact_email": "registry@nust.ac.zw",
    },
]

# Any institution that is not one of the three universities is deactivated by
# the seeder rather than deleted: credentials it has already issued must stay
# verifiable, which is itself worth demonstrating.
UNIVERSITY_CODES = {u["code"] for u in UNIVERSITIES}


# ---------------------------------------------------------------------------
# Users - (username, full name, role, institution code or None, env var)
# ---------------------------------------------------------------------------

USERS = [
    ("admin", "System Administrator", Role.ADMIN, None, "SEED_ADMIN_PASSWORD"),
    ("auditor", "Kudzai Zhou", Role.ADMIN, None, "SEED_AUDITOR_PASSWORD"),
    ("registry.msu", "Tendai Chikwanha", Role.ISSUER, "MSU", "SEED_MSU_PASSWORD"),
    ("registry.uz", "Nyasha Gumbo", Role.ISSUER, "UZ", "SEED_UZ_PASSWORD"),
    ("registry.nust", "Blessing Sibanda", Role.ISSUER, "NUST", "SEED_NUST_PASSWORD"),
    ("hr.verifier", "Tapiwa Marufu", Role.VERIFIER, None, "SEED_VERIFIER_PASSWORD"),
    ("admissions", "Chiedza Mapfumo", Role.VERIFIER, None, "SEED_ADMISSIONS_PASSWORD"),
]

USER_NOTES = {
    "admin": "Full access. Use for the audit trail and user management screens.",
    "auditor": "Second administrator, so admin actions can be shown being reviewed.",
    "registry.msu": "Registers and revokes credentials for Midlands State University.",
    "registry.uz": "Registers and revokes credentials for the University of Zimbabwe.",
    "registry.nust": "Registers and revokes credentials for NUST.",
    "hr.verifier": "Employer checking a job applicant. Sees only their own history.",
    "admissions": "Admissions officer at another institution. Also verifier-only.",
}


# ---------------------------------------------------------------------------
# Qualifications
#
# (credential_id, title, type, holder, holder_email, institution,
#  award_days_ago, expiry_days_ago or None, status, revocation_reason)
#
# A negative expiry means the date is in the future, i.e. still valid.
# ---------------------------------------------------------------------------

QUALIFICATIONS = [
    # -- Midlands State University -----------------------------------------
    (
        "MSU-2023-BSC247",
        "BSc Honours in Information Systems",
        "Degree",
        "Tinashe Moyo",
        "tinashe.moyo@example.com",
        "MSU",
        640,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "MSU-2023-BSC583",
        "BSc Honours in Computer Science",
        "Degree",
        "Rutendo Chirwa",
        "rutendo.chirwa@example.com",
        "MSU",
        640,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "MSU-2022-MSC742",
        "MSc in Information Management",
        "Degree",
        "Farai Ncube",
        "farai.ncube@example.com",
        "MSU",
        980,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "MSU-2024-DIP395",
        "Diploma in Business Administration",
        "Diploma",
        "Anesu Kadzviti",
        "anesu.kadzviti@example.com",
        "MSU",
        280,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "MSU-2021-BSC926",
        "BSc Honours in Accounting",
        "Degree",
        "Panashe Zvobgo",
        "panashe.zvobgo@example.com",
        "MSU",
        1420,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "MSU-2024-CER638",
        "Certificate in Data Protection",
        "Certificate",
        "Rudo Chikafu",
        "rudo.chikafu@example.com",
        "MSU",
        300,
        -400,
        QualificationStatus.ACTIVE,
        None,
    ),
    # Expires in three weeks - useful for showing a credential nearing expiry.
    (
        "MSU-2022-CER459",
        "Certificate in Project Management",
        "Certificate",
        "Tarisai Mhlanga",
        "tarisai.mhlanga@example.com",
        "MSU",
        900,
        -21,
        QualificationStatus.ACTIVE,
        None,
    ),
    # Already expired.
    (
        "MSU-2019-CER274",
        "Certificate in Occupational Safety",
        "Certificate",
        "Simbarashe Dube",
        "simbarashe.dube@example.com",
        "MSU",
        2100,
        45,
        QualificationStatus.ACTIVE,
        None,
    ),
    # Revoked.
    (
        "MSU-2021-DIP847",
        "Diploma in Project Management",
        "Diploma",
        "Munashe Chirume",
        "munashe.chirume@example.com",
        "MSU",
        1300,
        None,
        QualificationStatus.REVOKED,
        "Awarded in error following a records audit; the holder had not completed "
        "the final module.",
    ),
    # No holder email - triggers the review assistant's contact signal.
    (
        "MSU-2020-BSC352",
        "BSc Honours in Economics",
        "Degree",
        "Kundai Marara",
        None,
        "MSU",
        1600,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    # -- University of Zimbabwe --------------------------------------------
    (
        "UZ-2023-LLB592",
        "Bachelor of Laws (LLB)",
        "Degree",
        "Nomsa Mutasa",
        "nomsa.mutasa@example.com",
        "UZ",
        620,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "UZ-2022-MBB734",
        "Bachelor of Medicine and Surgery (MBChB)",
        "Degree",
        "Tanaka Shumba",
        "tanaka.shumba@example.com",
        "UZ",
        1010,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "UZ-2024-BSC468",
        "BSc Honours in Statistics",
        "Degree",
        "Vimbai Nyoni",
        "vimbai.nyoni@example.com",
        "UZ",
        260,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "UZ-2021-MBA875",
        "Master of Business Administration",
        "Degree",
        "Takudzwa Mangwiro",
        "takudzwa.mangwiro@example.com",
        "UZ",
        1380,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "UZ-2023-LIC539",
        "Practising Licence - Legal Practitioner",
        "Licence",
        "Nomsa Mutasa",
        "nomsa.mutasa@example.com",
        "UZ",
        540,
        -180,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "UZ-2020-LIC627",
        "Practising Licence - Medical Officer",
        "Licence",
        "Tanaka Shumba",
        "tanaka.shumba@example.com",
        "UZ",
        1700,
        120,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "UZ-2022-SHC783",
        "Short Course in Research Ethics",
        "Short Course",
        "Vimbai Nyoni",
        "vimbai.nyoni@example.com",
        "UZ",
        870,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "UZ-2019-BSC294",
        "BSc Honours in Sociology",
        "Degree",
        "Kudakwashe Nyamande",
        "kudakwashe.nyamande@example.com",
        "UZ",
        2200,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "UZ-2021-DIP658",
        "Diploma in Public Administration",
        "Diploma",
        "Ropafadzo Chigumba",
        "ropafadzo.chigumba@example.com",
        "UZ",
        1450,
        None,
        QualificationStatus.REVOKED,
        "Withdrawn by the Senate following an academic misconduct finding.",
    ),
    # -- National University of Science and Technology ---------------------
    (
        "NUST-2023-BEN472",
        "BEng Honours in Civil Engineering",
        "Degree",
        "Mthokozisi Ndlovu",
        "mthokozisi.ndlovu@example.com",
        "NUST",
        600,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "NUST-2022-BEN935",
        "BEng Honours in Electronic Engineering",
        "Degree",
        "Sibusiso Moyo",
        "sibusiso.moyo@example.com",
        "NUST",
        960,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "NUST-2024-BSC386",
        "BSc Honours in Applied Chemistry",
        "Degree",
        "Nokuthula Ncube",
        "nokuthula.ncube@example.com",
        "NUST",
        240,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "NUST-2021-MSC549",
        "MSc in Renewable Energy",
        "Degree",
        "Thabani Sibanda",
        "thabani.sibanda@example.com",
        "NUST",
        1360,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "NUST-2023-PRO627",
        "Chartered Engineer Registration",
        "Professional Certification",
        "Mthokozisi Ndlovu",
        "mthokozisi.ndlovu@example.com",
        "NUST",
        520,
        -730,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "NUST-2020-PRO843",
        "Certified Quality Auditor",
        "Professional Certification",
        "Sibusiso Moyo",
        "sibusiso.moyo@example.com",
        "NUST",
        1750,
        200,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "NUST-2022-SHC259",
        "Short Course in Industrial Safety",
        "Short Course",
        "Nokuthula Ncube",
        "nokuthula.ncube@example.com",
        "NUST",
        840,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "NUST-2024-CER764",
        "Certificate in Structural Design",
        "Certificate",
        "Lindiwe Mpofu",
        None,
        "NUST",
        190,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    (
        "NUST-2020-BEN538",
        "BEng Honours in Mechanical Engineering",
        "Degree",
        "Bongani Khumalo",
        "bongani.khumalo@example.com",
        "NUST",
        1820,
        None,
        QualificationStatus.REVOKED,
        "Certificate reported as fraudulent by the awarding faculty.",
    ),
    # -- Records that exist to demonstrate the review assistant ------------
    # Award date about 70 years ago, beyond the 60-year plausibility window.
    (
        "UZ-1955-BSC486",
        "BSc in Natural Sciences",
        "Degree",
        "Ephraim Chatambudza",
        "ephraim.chatambudza@example.com",
        "UZ",
        25600,
        None,
        QualificationStatus.ACTIVE,
        None,
    ),
    # Awarded and expiring 14 days later - an implausibly short validity window.
    (
        "NUST-2025-SHC672",
        "Short Course in Site Induction",
        "Short Course",
        "Melusi Ngwenya",
        "melusi.ngwenya@example.com",
        "NUST",
        120,
        106,
        QualificationStatus.ACTIVE,
        None,
    ),
]

# One holder deliberately carries six credentials, which trips the review
# assistant's "unusually many credentials for one holder" rule (threshold 5).
BUSY_HOLDER = "Tapiwa Chidziva"
BUSY_HOLDER_CREDENTIALS = [
    ("MSU-2019-SHC423", "Short Course in Financial Reporting", "Short Course", "MSU", 2000),
    ("MSU-2020-SHC736", "Short Course in Taxation", "Short Course", "MSU", 1750),
    ("MSU-2021-SHC582", "Short Course in Auditing", "Short Course", "MSU", 1400),
    ("UZ-2022-SHC297", "Short Course in Corporate Governance", "Short Course", "UZ", 1050),
    ("UZ-2023-SHC645", "Short Course in Risk Management", "Short Course", "UZ", 700),
    ("NUST-2024-SHC358", "Short Course in Data Analytics", "Short Course", "NUST", 350),
]


# ---------------------------------------------------------------------------
# Verification history - (credential_id, performed_by username, days ago)
#
# Includes references that do not exist, so the register shows what a failed
# lookup looks like. One reference is attempted repeatedly, which trips the
# review assistant's "repeated failed lookups" rule.
# ---------------------------------------------------------------------------

VERIFICATIONS = [
    ("MSU-2023-BSC247", "hr.verifier", 12),
    ("MSU-2023-BSC247", "admissions", 9),
    ("UZ-2023-LLB592", "hr.verifier", 11),
    ("NUST-2023-BEN472", "admissions", 10),
    ("UZ-2022-MBB734", "hr.verifier", 8),
    ("MSU-2022-MSC742", "admissions", 7),
    ("NUST-2022-BEN935", "hr.verifier", 6),
    ("MSU-2021-DIP847", "hr.verifier", 6),  # REVOKED
    ("UZ-2021-DIP658", "admissions", 5),  # REVOKED
    ("MSU-2019-CER274", "hr.verifier", 5),  # EXPIRED
    ("UZ-2020-LIC627", "admissions", 4),  # EXPIRED
    ("NUST-2020-PRO843", "hr.verifier", 4),  # EXPIRED
    ("MSU-2024-DIP395", "admissions", 3),
    ("UZ-2024-BSC468", "hr.verifier", 3),
    ("NUST-2024-BSC386", "admissions", 2),
    ("MSU-2020-BSC352", "hr.verifier", 2),
    ("UZ-2021-MBA875", "admissions", 1),
    ("NUST-2021-MSC549", "hr.verifier", 1),
    # References that were never registered - these return INVALID.
    ("MSU-2023-FAKE47", "hr.verifier", 9),
    ("UZ-2024-BOGUS3", "admissions", 6),
    ("NUST-2022-NONE24", "hr.verifier", 3),
    # The same unregistered reference tried five times, which is the pattern a
    # fraud investigation would want to see.
    ("MSU-2022-TRY777", "admissions", 8),
    ("MSU-2022-TRY777", "admissions", 8),
    ("MSU-2022-TRY777", "hr.verifier", 7),
    ("MSU-2022-TRY777", "admissions", 5),
    ("MSU-2022-TRY777", "hr.verifier", 2),
    # A registered credential checked repeatedly, every time coming back
    # REVOKED. Five non-VALID results on one reference is what the review
    # assistant's "repeated failed lookups" rule is looking for.
    ("NUST-2020-BEN538", "hr.verifier", 14),
    ("NUST-2020-BEN538", "admissions", 11),
    ("NUST-2020-BEN538", "hr.verifier", 9),
    ("NUST-2020-BEN538", "admissions", 6),
    ("NUST-2020-BEN538", "hr.verifier", 2),
]


# Credentials worth quoting in the demonstration, with the result each returns.
DEMO_CREDENTIALS = [
    ("MSU-2023-BSC247", VerificationResult.VALID, "A clean, current degree. The everyday case."),
    (
        "UZ-2023-LLB592",
        VerificationResult.VALID,
        "A second valid credential, from a different university.",
    ),
    ("MSU-2022-CER459", VerificationResult.VALID, "Valid, but expires in about three weeks."),
    ("MSU-2019-CER274", VerificationResult.EXPIRED, "Genuinely awarded, but past its expiry date."),
    ("UZ-2020-LIC627", VerificationResult.EXPIRED, "An expired practising licence."),
    ("MSU-2021-DIP847", VerificationResult.REVOKED, "Revoked after a records audit."),
    (
        "UZ-2021-DIP658",
        VerificationResult.REVOKED,
        "Revoked following an academic misconduct finding.",
    ),
    (
        "NUST-2020-BEN538",
        VerificationResult.REVOKED,
        "Revoked as fraudulent - the strongest case to show.",
    ),
    (
        "MSU-2023-FAKE47",
        VerificationResult.INVALID,
        "Well-formed but never registered. Shows that nothing is disclosed.",
    ),
    (
        "NOT-A-CREDENTIAL",
        VerificationResult.INVALID,
        "Malformed input. Handled as INVALID rather than as an error.",
    ),
]
