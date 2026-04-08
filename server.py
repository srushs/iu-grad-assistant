from mcp.server.fastmcp import FastMCP
import os
import uvicorn

mcp = FastMCP("iu-graduate-assistant")

SCHOOL_DATA = {
    "hamilton lugar": {
        "keywords": ["hamilton lugar", "hls", "international", "global affairs"],
        "name": "Hamilton Lugar School of Global and International Studies",
        "program_page": "https://hls.indiana.edu/academics/graduate/index.html",
        "contact_page": "https://hls.indiana.edu/about/contact.html",
    },
    "luddy": {
        "keywords": ["luddy", "informatics", "computer science", "data science",
                     "ai", "artificial intelligence", "cybersecurity", "computing"],
        "name": "Luddy School of Informatics, Computing, and Engineering",
        "program_page": "https://luddy.indiana.edu/academics/grad-programs/index.html",
        "contact_page": "https://luddy.iu.edu/about/contact.html",
    },
    "kelley": {
        "keywords": ["kelley", "business", "mba", "msis", "finance", "accounting"],
        "name": "Kelley School of Business",
        "program_page": "https://kelley.iu.edu/programs/index.html",
        "contact_page": "https://kelley.iu.edu/about/contact.html",
    },
    "oneill": {
        "keywords": ["o'neill", "oneill", "public affairs", "environmental affairs",
                     "public policy"],
        "name": "O'Neill School of Public and Environmental Affairs",
        "program_page": "https://oneill.indiana.edu/masters/index.html",
        "contact_page": "https://oneill.indiana.edu/contact/index.html",
    },
    "arts and sciences": {
        "keywords": ["arts and sciences", "college of arts", "liberal arts"],
        "name": "College of Arts and Sciences",
        "program_page": "https://college.indiana.edu/graduate/index.html",
        "contact_page": "https://college.indiana.edu/contact/index.html",
    },
    "law": {
        "keywords": ["law", "maurer", "legal"],
        "name": "Maurer School of Law",
        "program_page": "https://law.indiana.edu/academics/graduate-degrees/index.html",
        "contact_page": "https://law.indiana.edu/about/contact-us.html",
    },
    "education": {
        "keywords": ["education", "teaching", "school of education"],
        "name": "School of Education",
        "program_page": "https://education.indiana.edu/programs",
        "contact_page": "https://education.indiana.edu/contact/index.html",
    },
    "jacobs": {
        "keywords": ["jacobs", "music"],
        "name": "Jacobs School of Music",
        "program_page": "https://music.indiana.edu/admissions/graduate/index.html",
        "contact_page": "https://music.indiana.edu/contact/index.html",
    },
    "eskenazi": {
        "keywords": ["eskenazi", "architecture", "art", "design"],
        "name": "Eskenazi School of Art, Architecture + Design",
        "program_page": "https://eskenazi.indiana.edu/graduate/index.html",
        "contact_page": "https://eskenazi.indiana.edu/about/contact.html",
    },
}

FALLBACK_URL = "https://graduate.indiana.edu/programs/index.html"
IU_HOUSING_URL = "https://housing.indiana.edu/graduate-family/index.html"
IU_GRADUATE_HOUSING_URL = "https://gradoffice.indiana.edu/student-life/housing.html"

def find_school(school_input: str) -> tuple[str, dict] | tuple[None, None]:
    """Match a school name or keyword to school data."""
    lower = school_input.lower()
    for school_key, data in SCHOOL_DATA.items():
        if any(kw in lower for kw in data["keywords"]):
            return school_key, data
    return None, None


@mcp.tool()
def get_school_page_urls(school: str, query_type: str = "general") -> str:
    """
    Returns official IU school webpage URLs (program page and/or contact page)
    to SUPPLEMENT the knowledge source response.

    This tool provides links only — it does not answer factual questions.
    The knowledge source should always be consulted first for the actual answer.

    ── WHEN TO CALL THIS TOOL ───────────────────────────────────────────────────
    Call this tool whenever a student's question involves a specific IU school
    AND falls into one of these categories:
      - Questions about programs, courses, curriculum, or what a school offers
      - Questions about admissions, how to apply, deadlines, requirements, fees
      - Questions asking for links, URLs, or where to find information
      - Any question where a school-specific link would help the student

    Do NOT call this tool for general questions (e.g., housing, campus life,
    tuition) that do not reference a specific school.

    ── RESOLVING THE SCHOOL FROM CONTEXT ────────────────────────────────────────
    The student's current message may not name a school explicitly. This happens
    often with short follow-ups like "Yes", "Sure", "Please", "Tell me more",
    "What about courses?", "Can I get that link?", or "What are the deadlines?".

    In these cases, you MUST resolve which school the student is referring to by
    looking at the most recent prior message in the conversation that named a
    specific IU school. Use that school as the `school` parameter.

    Example: If the prior context was about Luddy School and the student says
    "Yes, give me the link", call this tool with school="Luddy".

    If the school cannot be resolved from context even after reviewing the full
    conversation history, ask the student: "Which IU school are you asking about?"
    Do NOT call this tool with a guessed or fabricated school name.

    ── RESOLVING THE QUERY TYPE FROM CONTEXT ────────────────────────────────────
    Similarly, if the student's current message is ambiguous (e.g., "Tell me more"),
    infer query_type from the most recent specific topic they asked about:
      - "program"    → programs, courses, curriculum
      - "admissions" → applying, deadlines, requirements, fees
      - "navigation" → explicitly asking for a link or URL
      - "general"    → spans multiple categories or unclear

    ── BREAKING THE CONFIRMATION LOOP ───────────────────────────────────────────
    CRITICAL: If the previous assistant message ended with a question like
    "Would you like a link?", "Would you like more details?", "Would you like
    the direct URL?", or any similar offer — and the student replies with "yes",
    "sure", "please", "ok", "yeah", or any affirmative — you MUST immediately
    provide the link or information that was offered. Do NOT ask again.
    Do NOT re-describe what you are about to provide. Just provide it.

    Asking the same confirmation question more than once is a hard failure.
    The student said yes. Give them what they asked for now.

    ── SINGLE-TOPIC FOCUS ────────────────────────────────────────────────────────
    Each response must address exactly ONE topic — the topic of the student's
    most recent message. If the conversation has touched on multiple topics
    (e.g., application steps AND housing), do NOT merge them.
    Pick the single topic the student is currently asking about and answer only
    that. Blending topics in one response is confusing and unhelpful.

    Args:
        school: Name or keyword of the IU school (e.g., 'Luddy', 'Kelley',
                'O Neill', 'Hamilton Lugar', 'Law', 'Education', 'Jacobs',
                'Eskenazi', 'Arts and Sciences')
        query_type: One of 'program', 'admissions', 'navigation', 'general'
    """
    school_key, school_data = find_school(school)

    if not school_data:
        return (
            f"[SUPPLEMENTARY LINKS]\n"
            f"Could not identify a specific IU school from '{school}'.\n"
            f"Fallback: {FALLBACK_URL}\n\n"
            f"[USAGE INSTRUCTION]\n"
            f"The school could not be identified — this likely means the student's "
            f"message was a short follow-up (e.g., 'Yes', 'Sure', 'Please'). "
            f"Check whether the previous assistant message offered the student a "
            f"link or more information. If it did, provide that information now "
            f"without asking again. "
            f"If a school can be found from conversation history, call this tool "
            f"again with that school name. "
            f"If no school can be determined, include the fallback link and ask "
            f"the student which school they are referring to."
        )

    if query_type == "program":
        links = f"Graduate Programs: {school_data['program_page']}"
    elif query_type == "admissions":
        links = f"Contact & Admissions: {school_data['contact_page']}"
    elif query_type == "navigation":
        links = (
            f"Graduate Programs: {school_data['program_page']}\n"
            f"Contact & Admissions: {school_data['contact_page']}"
        )
    else:  
        links = (
            f"Graduate Programs: {school_data['program_page']}\n"
            f"Contact & Admissions: {school_data['contact_page']}"
        )

    return (
        f"[SUPPLEMENTARY LINKS for {school_data['name']}]\n"
        f"{links}\n\n"
        f"[USAGE INSTRUCTION]\n"
        f"These links supplement the knowledge source response. Follow these rules:\n"
        f"1. If the knowledge source fully answered the student's question with "
        f"specific details (deadlines, steps, requirements, fees, etc.), "
        f"do NOT include these links — the answer is already complete.\n"
        f"2. If the knowledge source provided a partial or vague answer, "
        f"append the relevant link at the END of your response as a "
        f"'For more information' reference.\n"
        f"3. If the knowledge source had NO relevant information, use these "
        f"links as the primary reference and direct the student to visit them.\n"
        f"4. If the student explicitly asked for a link or URL, always include it.\n"
        f"5. Never explain why you are or aren't including a link.\n"
        f"6. CONTEXT CONTINUITY: Stay focused on the single topic the student asked "
        f"about in their current message. Do not merge multiple topics (e.g., housing "
        f"AND programs) into one response. Answer the most recent question only, then "
        f"append a relevant link if appropriate.\n"
        f"7. NO REPEAT OFFERS: If the previous assistant message already asked "
        f"'Would you like a link?' and the student said yes, do NOT ask again. "
        f"Provide the link directly and immediately."
    )


@mcp.tool()
def get_housing_links(campus: str = "bloomington") -> str:
    """
    Returns official IU housing webpage URLs for graduate students.

    ONLY call this tool when:
      - The student explicitly asks about housing, accommodation, or where to live
      - The student confirms they want housing links after a prior housing discussion
        (e.g., they said "yes", "sure", "please" after the assistant offered housing info)

    Do NOT call this tool for questions about programs, admissions, or coursework.

    ── BREAKING THE CONFIRMATION LOOP ───────────────────────────────────────────
    CRITICAL: If the previous assistant message offered housing links and the student
    replied "yes", "sure", "please" or any affirmative — provide the links NOW.
    Do NOT ask again whether they want the links. Just give them.

    Args:
        campus: The IU campus (default: 'bloomington')
    """
    if "bloomington" in campus.lower() or campus.lower() in ("iu", "iub", ""):
        links = (
            f"IU Bloomington Graduate & Family Housing: {IU_HOUSING_URL}\n"
            f"Graduate School Housing Resources: {IU_GRADUATE_HOUSING_URL}"
        )
        campus_name = "IU Bloomington"
    else:
        links = f"IU Graduate Programs (for campus housing info): {FALLBACK_URL}"
        campus_name = campus

    return (
        f"[HOUSING LINKS for {campus_name}]\n"
        f"{links}\n\n"
        f"[USAGE INSTRUCTION]\n"
        f"Provide these links directly to the student without re-describing the "
        f"housing options or asking another confirmation question. "
        f"A short intro like 'Here are the housing links for IU Bloomington:' "
        f"is sufficient. Do not merge housing information with program or "
        f"admissions information in the same response."
    )


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
