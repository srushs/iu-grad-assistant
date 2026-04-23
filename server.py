"""
IU Graduate Programs MCP Server (Combined)

A lightweight MCP server that provides official webpage URLs, contact
page links, and housing resources for Indiana University graduate schools.
Designed to work alongside ChatAIU's knowledge sources as a supplement,
not a replacement.

The knowledge sources handle content questions (program details, courses,
requirements). This server handles structured link data (program page URLs,
contact/admissions page URLs, housing resources).

Supports 15 IU graduate schools with smart keyword + word-boundary matching,
including multi-school comparison queries.

Transport: SSE (Server-Sent Events) over HTTP (default)
           Streamable HTTP via PORT env var (set USE_STREAMABLE_HTTP=1)
Framework: FastMCP (official Python MCP SDK)

Usage:
    Development:  python server.py
    Production:   uvicorn server:app --host 0.0.0.0 --port 10000
"""

import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from schools import SCHOOLS, FALLBACK_URL, IU_HOUSING_URL, IU_GRADUATE_HOUSING_URL
from matching import find_school, find_multiple_schools
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.applications import Starlette

# Server setup


mcp = FastMCP(
    "IU Graduate Programs",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 10000)),
    instructions=(
        "Provides official webpage URLs, contact/admissions links, and housing "
        "resources for all 15 Indiana University graduate schools. Use this server "
        "to supply students with direct links to program pages, admissions contacts, "
        "and graduate housing information."
    ),
)


# Tools


@mcp.tool()
def get_program_links(school_name: str) -> str:
    """Returns the official graduate programs webpage URL for an Indiana
    University school. Use this to provide students with a direct link
    to explore program details, degree options, and curriculum information
    on the school's website.

    ── WHEN TO CALL THIS TOOL ───────────────────────────────────────────────────
    Call this tool whenever a student's question involves a specific IU school
    AND falls into one of these categories:
      - Questions about programs, courses, curriculum, or what a school offers
      - Questions asking for a program page link or URL
      - Comparison queries referencing multiple schools (e.g. "Compare Luddy and Kelley")

    ── RESOLVING THE SCHOOL FROM CONTEXT ────────────────────────────────────────
    The student's current message may not name a school explicitly. This happens
    often with short follow-ups like "Yes", "Sure", "Please", "Tell me more",
    "What about courses?", or "Can I get that link?".

    In these cases, resolve which school the student is referring to by looking
    at the most recent prior message in the conversation that named a specific
    IU school. Use that school as the `school_name` parameter.

    If the school cannot be resolved from context even after reviewing the full
    conversation history, ask the student: "Which IU school are you asking about?"
    Do NOT call this tool with a guessed or fabricated school name.

    ── BREAKING THE CONFIRMATION LOOP ───────────────────────────────────────────
    CRITICAL: If the previous assistant message ended with a question like
    "Would you like a link?" or "Would you like more details?" — and the student
    replies with "yes", "sure", "please", "ok", or any affirmative — you MUST
    immediately provide the link. Do NOT ask again.

    Asking the same confirmation question more than once is a hard failure.
    The student said yes. Give them what they asked for now.

    Args:
        school_name: Name or keyword identifying the school.
                     Examples: "Luddy", "Kelley", "Data Science",
                     "Business", "O'Neill", "Public Health",
                     "Compare Luddy and Kelley" (multi-school supported)
    """
    schools = find_multiple_schools(school_name)

    if not schools:
        return (
            f"Could not identify a specific IU school from '{school_name}'.\n"
            f"IU Graduate Programs: {FALLBACK_URL}\n\n"
            f"[USAGE INSTRUCTION]\n"
            f"The school could not be identified — check whether the student's "
            f"message is a short follow-up (e.g., 'Yes', 'Sure', 'Please'). "
            f"If a school can be found from conversation history, call this tool "
            f"again with that school name. If no school can be determined, "
            f"include the fallback link and ask the student which school they mean."
        )

    if len(schools) == 1:
        school = schools[0]
        return (
            f"[PROGRAM LINK for {school['full_name']}]\n"
            f"Graduate Programs: {school['program_url']}\n\n"
            f"[USAGE INSTRUCTION]\n"
            f"Append this link at the END of your response as a 'For more information' "
            f"reference, unless the student explicitly asked for a link — in that case, "
            f"provide it directly. Never explain why you are or aren't including a link."
        )

    lines = [f"[PROGRAM LINKS — {len(schools)} schools matched]\n"]
    for school in schools:
        lines.append(f"{school['full_name']}")
        lines.append(f"Graduate Programs: {school['program_url']}\n")
    lines.append(
        "[USAGE INSTRUCTION]\n"
        "List each school and its link clearly. Do not merge their details."
    )
    return "\n".join(lines)


@mcp.tool()
def get_contact_info(school_name: str) -> str:
    """Returns the official contact and admissions page URL for an Indiana
    University school. Use this when a student needs to reach the school
    directly about applications, deadlines, requirements, fees, or any
    admissions-related questions.

    ── WHEN TO CALL THIS TOOL ───────────────────────────────────────────────────
    Call this tool whenever a student's question involves a specific IU school
    AND falls into one of these categories:
      - Questions about admissions, how to apply, deadlines, requirements, or fees
      - Questions asking for a contact page link or URL
      - Any question where a direct school contact would help the student

    ── RESOLVING THE SCHOOL FROM CONTEXT ────────────────────────────────────────
    The student's current message may not name a school explicitly. Short follow-ups
    like "What are the deadlines?", "How do I apply?", or "Can I get that link?"
    should be resolved by looking at the most recent prior message that named a
    specific IU school.

    If the school cannot be resolved from context, ask:
    "Which IU school are you asking about?"
    Do NOT call this tool with a guessed or fabricated school name.

    ── BREAKING THE CONFIRMATION LOOP ───────────────────────────────────────────
    CRITICAL: If the previous assistant message offered a contact link and the
    student replied "yes", "sure", "please", or any affirmative — provide the
    link NOW. Do NOT ask again whether they want it. Just give it.

    Args:
        school_name: Name or keyword identifying the school.
                     Examples: "Luddy", "Kelley", "Law",
                     "Nursing", "Maurer", "MBA"
    """
    schools = find_multiple_schools(school_name)

    if not schools:
        return (
            f"Could not identify a specific IU school from '{school_name}'.\n"
            f"IU Graduate Admissions: {FALLBACK_URL}\n\n"
            f"[USAGE INSTRUCTION]\n"
            f"The school could not be identified — check whether the student's "
            f"message is a short follow-up. If a school can be found from "
            f"conversation history, call this tool again with that school name. "
            f"If no school can be determined, include the fallback link and ask "
            f"the student which school they mean."
        )

    if len(schools) == 1:
        school = schools[0]
        return (
            f"[CONTACT LINK for {school['full_name']}]\n"
            f"Contact/Admissions: {school['contact_url']}\n\n"
            f"[USAGE INSTRUCTION]\n"
            f"Append this link at the END of your response as a 'For more information' "
            f"reference, unless the student explicitly asked for a link — in that case, "
            f"provide it directly. Never explain why you are or aren't including a link."
        )

    lines = [f"[CONTACT LINKS — {len(schools)} schools matched]\n"]
    for school in schools:
        lines.append(f"{school['full_name']}")
        lines.append(f"Contact/Admissions: {school['contact_url']}\n")
    lines.append(
        "[USAGE INSTRUCTION]\n"
        "List each school and its contact link clearly. Do not merge their details."
    )
    return "\n".join(lines)


@mcp.tool()
def get_housing_links(campus: str = "bloomington") -> str:
    """Returns official IU housing webpage URLs for graduate students.

    ONLY call this tool when:
      - The student explicitly asks about housing, accommodation, or where to live
      - The student confirms they want housing links after a prior housing discussion
        (e.g., they said "yes", "sure", "please" after the assistant offered housing info)

    Do NOT call this tool for questions about programs, admissions, or coursework.

    ── BREAKING THE CONFIRMATION LOOP ───────────────────────────────────────────
    CRITICAL: If the previous assistant message offered housing links and the student
    replied "yes", "sure", "please" or any affirmative — provide the links NOW.
    Do NOT ask again whether they want the links. Just give them.

    ── SINGLE-TOPIC FOCUS ────────────────────────────────────────────────────────
    Each response must address exactly ONE topic — the topic of the student's
    most recent message. Do NOT merge housing information with program or
    admissions information in the same response.

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


# Middleware

class HostRewriteMiddleware(BaseHTTPMiddleware):
    """Rewrites the Host header so the MCP server accepts requests
    forwarded through Render's (or any) reverse proxy."""
    async def dispatch(self, request, call_next):
        request.scope["headers"] = [
            (b"host", b"localhost") if k == b"host" else (k, v)
            for k, v in request.scope["headers"]
        ]
        return await call_next(request)

# Health endpoint

async def health(request):
    return JSONResponse({"status": "ok"})

# App assembly


USE_STREAMABLE_HTTP = os.environ.get("USE_STREAMABLE_HTTP", "").strip() == "1"

if USE_STREAMABLE_HTTP:
    _base_app = mcp.streamable_http_app()

    class _FixHostMiddleware:
        """Raw ASGI host-rewrite for streamable HTTP transport."""
        def __init__(self, inner_app):
            self._app = inner_app

        async def __call__(self, scope, receive, send):
            if scope["type"] in ("http", "websocket"):
                scope["headers"] = [
                    (b"host", b"localhost:8000") if k == b"host" else (k, v)
                    for k, v in scope.get("headers", [])
                ]
            await self._app(scope, receive, send)

    app = _FixHostMiddleware(_base_app)

else:
    sse_app = mcp.sse_app()

    app = Starlette(
        routes=[
            Route("/health", health),
            Mount("/", app=sse_app),
        ],
        middleware=[
            Middleware(HostRewriteMiddleware)
        ],
    )

# Main

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    if USE_STREAMABLE_HTTP:
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        mcp.run(transport="sse")
