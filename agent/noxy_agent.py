from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from openai import BadRequestError
from vector.search import search_vectors
from Services.config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME
from tools.progresstask_tool import pending_tasks_tool
from tools.status_taskprogress import PENDING_TASK_PHRASES, fetch_task_status_groups
from tools.pdf_tool import pdf_file_tool
from tools.general_tool import general_filter_tool
from tools.hr_tool import hr_lookup

llm = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    model=AZURE_DEPLOYMENT_NAME,
    api_version="2024-02-15-preview",
    temperature=0.2
)

SYSTEM_PROMPT = """
You are Noxy, an HR onboarding assistant.
Your purpose is to answer only about these scope.
Your allowed scope:
- HR policies
- employee onboarding
- company information
- government requirements
- IDs and documents
- HR contact info
- basic greetings
- pending requirements

Forbidden:
- Do NOT give directions, routes, navigation, or "how to go there".
- Do NOT book appointments or perform actions.
- Do NOT say you can connect to HR.
- Do NOT invent information.

Rules:
1. If search is empty and query is HR-related, say you cannot find info.
2. Maximum 3 simple sentences per answer.
3. Do not use Mdash or special formatting.
4. There is no supported live HR support. 
5. Use a supportive and helpful tone. Be happy to assist them.

HR CONTACT INFORMATION:
Email: hr.department@n-pax.com
Cebu HR: (032) 123-4567
Manila HR: (02) 987-6543
Hours: Monday–Friday, 8:00 AM – 6:00 PM

When answering multiple questions, address each one clearly and concisely.
"""

llm_with_tools = llm.bind_tools([
    pending_tasks_tool,
    pdf_file_tool,
    hr_lookup,
    general_filter_tool
])

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}")
])

def retrieve_context(query: str):
    """Retrieve context from vector search"""
    hits = search_vectors(query)
    return "\n".join(hits) if hits else ""

def ask_noxy(message: str, user_id: str = None, task_progress=None):
    """
    Enhanced Noxy that handles multiple questions using bound tools.
    """
    q = message.lower()

    try:
        filter_result = general_filter_tool.invoke({"data": {"query": message}})
        if filter_result == "greeting":
            return llm.invoke("The user greeted you. Reply warmly, brief, friendly, "
                             "and within HR onboarding scope.").content
        
        if filter_result == "vague":
            return llm.invoke("The user asked for help but was unclear. "
                             "Ask naturally which HR or onboarding topic they mean. Keep it short.").content
        
        if user_id and any(p in q for p in PENDING_TASK_PHRASES):
            task_groups = fetch_task_status_groups(user_id)
            return pending_tasks_tool.invoke({
                "data": {
                    "pending": task_groups.get("pending", []),
                    "in_progress": task_groups.get("in_progress", []),
                    "completed": task_groups.get("completed", [])
                }
            })
        
        context = retrieve_context(message)
        
        full_prompt = prompt.format(question=message)
        if context:
            full_prompt += f"\n\nRelevant knowledge:\n{context}"
        
        result = llm_with_tools.invoke(full_prompt)
    
    except BadRequestError as e:
        # Handle Azure content filter (jailbreak attempts, policy violations)
        error_message = str(e)
        if 'content_filter' in error_message or 'jailbreak' in error_message:
            return "I'm sorry, I cannot provide that type of response. I'm here to help with HR onboarding topics like policies, documents, and requirements. How can I assist you with your onboarding?"
        else:
            return "I'm sorry, I encountered an error processing your request. Please try rephrasing your question about HR or onboarding topics."
    
    except Exception as e:
        # Catch any other errors
        return "I'm sorry, something went wrong. Please try asking your HR or onboarding question again."
    
    # Check if LLM wants to use tools
    if hasattr(result, 'tool_calls') and result.tool_calls:
        messages = [HumanMessage(content=full_prompt), result]
        
        # Execute each tool call
        for tool_call in result.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call.get('args', {})
            
            try:
                # Handle each tool
                if tool_name == "pending_tasks_tool":
                    if user_id:
                        task_groups = fetch_task_status_groups(user_id)
                        tool_result = pending_tasks_tool.invoke({
                            "data": {
                                "pending": task_groups.get("pending", []),
                                "in_progress": task_groups.get("in_progress", []),
                                "completed": task_groups.get("completed", [])
                            }
                        })
                    else:
                        tool_result = "I need your user information to check your pending tasks. Please make sure you're logged in."
                
                elif tool_name == "pdf_file_tool":
                    tool_result = pdf_file_tool.invoke({"data": {"query": message}})
                
                elif tool_name == "hr_lookup":
                    tool_result = hr_lookup.invoke({"data": {"query": message}})
                
                elif tool_name == "general_filter_tool":
                    tool_result = general_filter_tool.invoke({"data": {"query": message}})
                
                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call['id']
                    )
                )
            
            except Exception as e:
                messages.append(
                    ToolMessage(
                        content=f"Error executing {tool_name}: {str(e)}",
                        tool_call_id=tool_call['id']
                    )
                )
        
        try:
            final_response = llm_with_tools.invoke(messages)
            return final_response.content
        except BadRequestError as e:
            if 'content_filter' in str(e) or 'jailbreak' in str(e):
                return "I'm sorry, I cannot provide that type of response. I'm here to help with HR onboarding topics like policies, documents, and requirements. How can I assist you with your onboarding?"
            else:
                return "I'm sorry, I encountered an error processing your request. Please try rephrasing your question about HR or onboarding topics."
    
    return result.content