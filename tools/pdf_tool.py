from langchain.tools import tool

PDF_MAP = {
    "sss": "SSS E1 FORM.pdf",
    "e1": "SSS E1 FORM.pdf",
    "pagibig": "HDMF.pdf",
    "pag-ibig": "HDMF.pdf",
    "philhealth": "PHILHEALTH.pdf",
    "1904": "BIR FORM 1904.pdf",
    "1905": "BIR FORM 1905.pdf",
    "2316": "BIR FORM 2316.pdf"
}

@tool
def pdf_lookup(query: str) -> str:
    """Returns PDF filename if user requests a form."""
    q = query.lower()
    for key, file in PDF_MAP.items():
        if key in q:
            return f"The correct PDF is {file}."
    return ""
