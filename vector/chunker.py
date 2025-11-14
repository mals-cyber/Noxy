from langchain_text_splitters import RecursiveCharacterTextSplitter

def expand_bullet_points(text: str):
    lines = text.split("\n")
    expanded = []
    
    for line in lines:
        if line.strip().startswith("- "):
            expanded.append(line[2:] + " is required as part of onboarding.")
        else:
            expanded.append(line)

    return "\n".join(expanded)


def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return splitter.split_documents(documents)
