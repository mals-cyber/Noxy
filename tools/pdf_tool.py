import re
from langchain.tools import tool
from tools.file_matcher import find_best_file_match, generic_bir_cases
from LLM.llm_followup import llm_followup_sentence
from tools.pdf_fetch import fetch_pdf_links


@tool("pdf_file_tool")
def pdf_file_tool(data: dict) -> str:
    """Return requested onboarding PDF file or ask for clarification if needed."""

    q = data.get("query", "").lower()

    request_keywords = ["form", "pdf", "file", "document", "download", "copy"]

    if not any(k in q for k in request_keywords):
        return "No file request detected."

    # enhanced numeric extractor
    bir_form_match = re.search(r"\b\d{3,4}\b", q)

    # generic BIR handling only if no form number
    if any(term in q for term in generic_bir_cases) and not bir_form_match:
        return "It looks like you are requesting a BIR form, but there are multiple types. May I know the specific form number you need?"

    files = fetch_pdf_links()
    if not files:
        return "I’m having trouble retrieving the files right now. Please try again later."

    best = find_best_file_match(q, files)

    # form number exists but unavailable
    if bir_form_match and best is None:
        return "I could not find a matching file. Can you specify the exact form name or number?"

    if best is None:
        return "I could not find a matching file. Can you specify the exact form name or number?"

    followup = llm_followup_sentence(best["name"])

    return f"Here is the file you need: {best['url']}. {followup}"
