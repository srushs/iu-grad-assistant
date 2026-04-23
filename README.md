# IU Graduate Programs MCP Server

A lightweight MCP server that provides official webpage URLs, contact/admissions links, and housing resources for **all 15 Indiana University graduate schools**.

Designed to work alongside ChatAIU's knowledge sources as a supplement — the knowledge sources handle content questions (program details, courses, requirements), this server handles structured link data.

---

## Tools

| Tool | Description |
|------|-------------|
| `get_program_links` | Returns the official graduate programs page URL for a school. Supports multi-school comparison queries (e.g. "Compare Luddy and Kelley"). |
| `get_contact_info` | Returns the contact/admissions page URL for a school. |
| `get_housing_links` | Returns IU Bloomington graduate housing links. |

---

## Supported Schools (15)

| School | Key Keywords |
|--------|-------------|
| Hamilton Lugar School of Global and International Studies | Hamilton Lugar, HLS, International, Global |
| Luddy School of Informatics, Computing, and Engineering | Luddy, CS, Data Science, AI, Cybersecurity |
| Kelley School of Business | Kelley, Business, MBA, Finance |
| College of Arts and Sciences | Arts and Sciences, Liberal Arts, Biology, Psychology |
| Eskenazi School of Art, Architecture + Design | Eskenazi, Architecture, Art, Design |
| Jacobs School of Music | Jacobs, Music, Composition |
| Maurer School of Law | Maurer, Law, JD, LLM |
| O'Neill School of Public and Environmental Affairs | O'Neill, MPA, Public Policy, Environmental |
| School of Education | Education, Teaching, Curriculum |
| School of Medicine | Medicine, MD, Biomedical |
| School of Nursing | Nursing, DNP, Nurse Practitioner |
| School of Optometry | Optometry, Vision Science, OD |
| School of Public Health | Public Health, MPH, Epidemiology |
| School of Social Work | Social Work, MSW |
| The Media School | Media, Journalism, Film, Communication |

---

## Setup

```bash
pip install -r requirements.txt
```

## Running

**Development (SSE, default):**
```bash
python server.py
```

**Production (SSE via uvicorn):**
```bash
uvicorn server:app --host 0.0.0.0 --port 10000
```

**Streamable HTTP transport (optional):**
```bash
USE_STREAMABLE_HTTP=1 uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `10000` | Port to listen on |
| `USE_STREAMABLE_HTTP` | `` | Set to `1` to use streamable HTTP instead of SSE |

---

## Project Structure

```
iu-grad-assistant-combined/
├── server.py        # MCP server, tools, middleware, app assembly
├── schools.py       # School data (15 schools, URLs, keywords, housing URLs)
├── matching.py      # Keyword matching logic (word-boundary aware, multi-school)
├── requirements.txt
└── README.md
```

