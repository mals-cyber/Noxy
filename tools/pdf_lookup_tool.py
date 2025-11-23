from langchain.tools import tool
from tools.fetch_pdflinks import fetch_pdf_links
from tools.file_matcher import find_best_file_match

REQUEST_KEYWORDS = ["form", "pdf", "file", "document", "download", "copy"]


@tool("pdf_lookup", description="""
Use this tool when the user is asking for a downloadable onboarding form,
government document (SSS, Pag-IBIG, PhilHealth, BIR), or PDF copy.
The input must be the user's query text.
""")
def pdf_lookup(query: str) -> str:
    """Exact same logic as the old ask_noxy PDF handler."""
    
    q = query.lower()

    # ✅ same detection behavior
    if not any(k in q for k in REQUEST_KEYWORDS):
        return ""

    # ✅ same fetch logic
    files = fetch_pdf_links()
    if not files:
        return "I’m having trouble retrieving the files right now. Please try again later."

    # ✅ same cosine matching
    best = find_best_file_match(q, files)
    if not best:
        return "I couldn’t find a matching onboarding form for that request."

    return f"Here is the file you need: {best['url']}"
