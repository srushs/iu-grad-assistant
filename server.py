from mcp.server.fastmcp import FastMCP
import os
import uvicorn

# ─── Initialize the MCP server ───────────────────────────────────────────────
mcp = FastMCP("iu-graduate-assistant")


# ─── School Data ─────────────────────────────────────────────────────────────
SCHOOL_DATA = {
    "hamilton lugar": {
        "keywords": ["hamilton lugar", "hls", "international", "global affairs"],
        "program_page": "https://hls.indiana.edu/academics/graduate/index.html",
        "contact_page": "https://hls.indiana.edu/about/contact.html",
    },
    "luddy": {
        "keywords": ["luddy", "informatics", "computer science", "data science",
                     "ai", "artificial intelligence", "cybersecurity", "computing"],
        "program_page": "https://luddy.indiana.edu/academics/grad-programs/index.html",
        "contact_page": "https://luddy.iu.edu/about/contact.html",
    },
    "kelley": {
        "keywords": ["kelley", "business", "mba", "msis", "finance", "accounting"],
        "program_page": "https://kelley.iu.edu/programs/index.html",
        "contact_page": "https://kelley.iu.edu/about/contact.html",
    },
    "oneill": {
        "keywords": ["o'neill", "oneill", "public affairs", "environmental affairs",
                     "public policy"],
        "program_page": "https://oneill.indiana.edu/masters/index.html",
        "contact_page": "https://oneill.indiana.edu/contact/index.html",
    },
    "arts and sciences": {
        "keywords": ["arts and sciences", "college of arts", "liberal arts"],
        "program_page": "https://college.indiana.edu/graduate/index.html",
        "contact_page": "https://college.indiana.edu/contact/index.html",
    },
    "law": {
        "keywords": ["law", "maurer", "legal"],
        "program_page": "https://law.indiana.edu/academics/graduate-degrees/index.html",
        "contact_page": "https://law.indiana.edu/about/contact-us.html",
    },
    "education": {
        "keywords": ["education", "teaching", "school of education"],
        "program_page": "https://education.indiana.edu/programs",
        "contact_page": "https://education.indiana.edu/contact/index.html",
    },
    "jacobs": {
        "keywords": ["jacobs", "music"],
        "program_page": "https://music.indiana.edu/admissions/graduate/index.html",
        "contact_page": "https://music.indiana.edu/contact/index.html",
    },
    "eskenazi": {
        "keywords": ["eskenazi", "architecture", "art", "design"],
        "program_page": "https://eskenazi.indiana.edu/graduate/index.html",
        "contact_page": "https://eskenazi.indiana.edu/about/contact.html",
    },
}

FALLBACK_URL = "https://graduate.indiana.edu/programs/index.html"


# ─── Helper Function ──────────────────────────────────────────────────────────
def find_school(school_input: str) -> dict | None:
    """Match a school name or keyword to school data."""
    lower = school_input.lower()
    for school_key, data in SCHOOL_DATA.items():
        if any(kw in lower for kw in data["keywords"]):
            return data
    return None


# ─── Tool 1: Get Programs Page ────────────────────────────────────────────────
@mcp.tool()
def get_program_page(school: str) -> str:
    """
    Returns the graduate programs page URL for a specific IU school.

    Use this tool when a student asks about:
    - What graduate programs or degrees a school offers
    - Program overviews, curriculum, or courses
    - Whether a specific school offers a certain degree
    - General "what can I study at X school" questions

    Args:
        school: Name or keyword of the IU school.
                Examples: 'Luddy', 'Kelley', 'O Neill', 'Hamilton Lugar',
                'Law', 'Education', 'Jacobs', 'Eskenazi', 'Arts and Sciences'
    """
    school_data = find_school(school)
    if school_data:
        return (
            f"Here is the graduate programs page for that school:\n"
            f"{school_data['program_page']}"
        )
    return (
        f"I could not find a specific match for '{school}'. "
        f"Please visit the IU Graduate School directory:\n{FALLBACK_URL}"
    )


# ─── Tool 2: Get Admissions / Contact Page ────────────────────────────────────
@mcp.tool()
def get_admissions_contact(school: str) -> str:
    """
    Returns the admissions and contact page URL for a specific IU school.

    Use this tool when a student asks about:
    - How to apply to a graduate program
    - Application deadlines or requirements
    - GRE, TOEFL, or document submission questions
    - Application fees
    - Who to contact at a specific school
    - General admissions process questions

    Args:
        school: Name or keyword of the IU school.
                Examples: 'Luddy', 'Kelley', 'O Neill', 'Hamilton Lugar',
                'Law', 'Education', 'Jacobs', 'Eskenazi', 'Arts and Sciences'
    """
    school_data = find_school(school)
    if school_data:
        return (
            f"For admissions information and to contact the school directly:\n"
            f"{school_data['contact_page']}"
        )
    return (
        f"I could not find a specific match for '{school}'. "
        f"Please visit the IU Graduate School directory:\n{FALLBACK_URL}"
    )


# ─── Tool 3: Get Both Links ───────────────────────────────────────────────────
@mcp.tool()
def get_school_links(school: str) -> str:
    """
    Returns both the graduate programs page and admissions contact page
    for a specific IU school.

    Use this tool when:
    - The student's question is general or navigational ("where do I find info on X school")
    - The student needs both program and admissions information
    - It is unclear whether they need programs info or admissions help
    - The student asks for an overview of a school

    Args:
        school: Name or keyword of the IU school.
                Examples: 'Luddy', 'Kelley', 'O Neill', 'Hamilton Lugar',
                'Law', 'Education', 'Jacobs', 'Eskenazi', 'Arts and Sciences'
    """
    school_data = find_school(school)
    if school_data:
        return (
            f"Here are the key pages for that school:\n\n"
            f"Graduate Programs: {school_data['program_page']}\n"
            f"Admissions & Contact: {school_data['contact_page']}"
        )
    return (
        f"I could not identify a specific IU school from '{school}'. "
        f"Please visit the IU Graduate School directory:\n{FALLBACK_URL}"
    )


# ─── Run the Server ───────────────────────────────────────────────────────────

class FixHostMiddleware:
    """Allows MCP server to accept requests from Render's proxy."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            new_headers = []
            for key, value in scope.get("headers", []):
                if key == b"host":
                    new_headers.append((b"host", b"localhost:8000"))
                else:
                    new_headers.append((key, value))
            scope["headers"] = new_headers
        await self.app(scope, receive, send)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = mcp.streamable_http_app()
    app = FixHostMiddleware(app)
    uvicorn.run(app, host="0.0.0.0", port=port)