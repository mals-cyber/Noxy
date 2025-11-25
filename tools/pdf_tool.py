import re
from langchain.tools import tool
from tools.file_matcher import find_best_file_match, generic_bir_cases
from LLM.llm_followup import llm_followup_sentence
from tools.pdf_fetch import fetch_pdf_links


@tool("pdf_file_tool")
def pdf_file_tool(data: dict) -> str:
    """Return requested onboarding PDF file(s) or ask for clarification if needed."""

    q = data.get("query", "").lower()

    request_keywords = ["form", "pdf", "file", "download", "copy"]

    if not any(k in q for k in request_keywords):
        return "No file request detected."

    # Detect multiple file requests using "and", commas, or multiple keywords
    file_keywords = [
        "pag-ibig", "pagibig", "hdmf",
        "sss", "social security",
        "philhealth", "phil health",
        "tin", "tax identification",
        "nbi", "clearance",
        "bir"
    ]
    
    # Count how many different files are mentioned
    mentioned_files = [kw for kw in file_keywords if kw in q]
    
    # Also check for multiple BIR forms
    bir_form_matches = re.findall(r"\b\d{3,4}\b", q)
    
    # Check for "and" or comma separators suggesting multiple requests
    has_multiple_separators = " and " in q or "," in q
    
    is_multiple_request = (
        len(mentioned_files) > 1 or 
        len(bir_form_matches) > 1 or 
        has_multiple_separators
    )

    # Generic BIR handling only if no form number
    bir_form_match = re.search(r"\b\d{3,4}\b", q)
    if any(term in q for term in generic_bir_cases) and not bir_form_match:
        return "It looks like you are requesting a BIR form, but there are multiple types. May I know the specific form number you need?"

    files = fetch_pdf_links()
    if not files:
        return "I'm having trouble retrieving the files right now. Please try again later."

    # If multiple files requested, process each separately
    if is_multiple_request:
        # Split query into parts (by 'and' or comma)
        parts = re.split(r'\s+and\s+|,\s*', q)
        
        results = []
        found_files = []
        not_found = []
        
        for part in parts:
            part = part.strip()
            if not part or len(part) < 3:  # Skip very short parts
                continue
                
            best = find_best_file_match(part, files)
            
            if best:
                # Avoid duplicates
                if best['url'] not in [f['url'] for f in found_files]:
                    found_files.append(best)
            else:
                # Track what wasn't found
                not_found.append(part)
        
        # Build response
        if found_files:
            for file in found_files:
                followup = llm_followup_sentence(file["name"])
                results.append(f"• {file['name']}: {file['url']}. {followup}")
        
        if not_found:
            not_found_text = ", ".join(not_found)
            results.append(f"I could not find files for: {not_found_text}. Please contact HR for assistance.")
        
        if not results:
            return "I could not find any matching files. Can you specify the exact form names or numbers?"
        
        return "\n".join(results)

    # Single file request (original logic)
    best = find_best_file_match(q, files)

    # Form number exists but unavailable
    if bir_form_match and best is None:
        return "I could not find a matching file. Can you specify the exact form name or number?"

    if best is None:
        return "I could not find a matching file. Can you specify the exact form name or number?"

    followup = llm_followup_sentence(best["name"])

    return f"Here is the file you need: {best['url']}. {followup}"