# Noxy 
**This project is currently in active development and may receive updates and new features.**

---
## Quick Start 

### Prerequisites 
- Python 3.10 or higher
- SQL Server installed (or any DB supported by SQLAlchemy)
- Docker Desktop or Docker Engine
- Azure OpenAI credentials

### Start SQL Server Container (Required Before Setup)
```bash
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=Strong_Password123!" -p 1433:1433 --name sqlserver -d mcr.microsoft.com/mssql/server:2022-latest
```

## Setup Instructions

### 1. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate environment (Windows)
.\venv\Scripts\activate
```
### 2. Install Dependencies
```bash
#Install all required libraries in one go by running
pip install -r requirements.txt
```
### 3. Create .env file
```bash
# 1. Add Azure OpenAi Credentials
AZURE_OPENAI_API_KEY=<apikey>
AZURE_OPENAI_ENDPOINT=<endpoint>
AZURE_OPENAI_DEPLOYMENT_NAME=<deploymentname>

#These variables are defined directly in Python using the os.environ method:
load_dotenv()
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
```
```bash
# 2. Add SQL Server connection
SQL_SERVER=localhost,1433
SQL_DB=NoxyChatbotDB
SQL_USER=sa
SQL_PASS=Strong_Password123!
```
### 4. Test SQL Server Connection
```bash
#Verify that SQL Server is running and accessible
python test_db.py
```
### 5. Set up Database Migrations
```bash
# Use the migrations from the ASP.NET backend instead of FastAPI migrations
# The database schema is managed and migrated through the ASP.NET backend (Entity Framework Core)
# Ensure the ASP.NET backend has been run to apply all necessary migrations to SQL Server
```
## Run FastAPI Server
```bash
# Start the Application
python -m uvicorn Services.main:app --reload
```
+ Uvicorn running on http://127.0.0.1:8000
+ Application startup complete

## Access the API
| URL | Description |
|-----|-------------|
| http://localhost:8000/ | Root endpoint – returns `{"message":"Noxy API is running"}` |
| http://localhost:8000/docs | interact with API |
| http://localhost:8000/redoc | ReDoc – auto-generated API documentation |

## Chat Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| POST | /chat | Send a message to Noxy (conversation is saved) |
| GET | /history/{username} | Retrieve full conversation history |

**For detailed endpoint documentation, see [API_ENDPOINTS.md](./Documentation/API_ENDPOINTS.md)**


## Technologies Used
- **Python 3.10+** – Main language for backend logic  
- **FastAPI** – API framework for handling chat requests and routing  
- **Uvicorn** – ASGI server running the FastAPI application  
- **SQL Server** – Stores users, chats, and history  
- **SQLAlchemy** – ORM used for database models and queries  
- **Alembic** – Handles database schema migrations  
- **Docker** – Runs SQL Server and keeps environments consistent  
- **Azure OpenAI** – Generates chat responses using deployed models  
- **python-dotenv** – Loads `.env` credentials securely
- **LangChain** – Framework used to connect LLMs, tools, and retrieval pipelines
- **ChromaDB (Vector Database)** – Used for semantic search and document embeddings
- **MCP (Model Context Protocol)** – *In progress*: enables extended model capabilities




## License

This project is part of the NPAX platform. See LICENSE for details.


