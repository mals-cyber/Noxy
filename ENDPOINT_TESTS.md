# Noxy Chatbot API - Endpoint Testing Guide

This guide provides comprehensive test cases for all active endpoints in the Noxy API.

## Prerequisites

1. Server must be running: `python -m uvicorn Services.main:app --reload`
2. Database must be configured and accessible
3. Azure OpenAI credentials must be set in `.env`
4. Use `curl`, Postman, or any HTTP client

---

## Test Summary

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/` | GET | Health check | ✓ Active |
| `/chat` | POST | Send message and get response | ✓ Active |
| `/history/{username}` | GET | Retrieve conversation history | ✓ Active |

---

## Test Cases

### 1. Health Check Endpoint

#### 1.1 Basic Health Check

**Endpoint:** `GET /`

**Description:** Verify the API server is running and responsive.

**Request:**
```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "Noxy API is running"
}
```

**Expected Status:** `200 OK`

**Test Checklist:**
- [ ] Returns status 200
- [ ] Response contains "message" field
- [ ] Message value is "Noxy API is running"

---

### 2. Chat Endpoint

#### 2.1 Valid Chat Request with Username

**Endpoint:** `POST /chat`

**Description:** Send a message as a user with username authentication.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "message": "What is the HR policy on vacation days?"
  }'
```

**Expected Response:**
```json
{
  "User": "What is the HR policy on vacation days?",
  "Noxy": "Your response from the chatbot will appear here..."
}
```

**Expected Status:** `200 OK`

**Test Checklist:**
- [ ] Returns status 200
- [ ] Response contains "User" and "Noxy" fields
- [ ] User message is echoed back correctly
- [ ] Noxy response is non-empty
- [ ] Message is saved to database (verify via /history)

**Prerequisites:**
- User "testuser1" must exist in ApplicationUsers table OR endpoint will return error

---

#### 2.2 Valid Chat Request with UserId

**Endpoint:** `POST /chat`

**Description:** Send a message using userId instead of username.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-id-123",
    "message": "How do I apply for a promotion?"
  }'
```

**Expected Response:**
```json
{
  "User": "How do I apply for a promotion?",
  "Noxy": "Your response from the chatbot will appear here..."
}
```

**Expected Status:** `200 OK`

**Test Checklist:**
- [ ] Returns status 200
- [ ] Response contains User and Noxy messages
- [ ] Works with userId parameter
- [ ] Message is saved to database

**Notes:**
- UserId takes priority if both username and userId are provided
- User must exist in the database

---

#### 2.3 Chat Request Without Username or UserId (Error Case)

**Endpoint:** `POST /chat`

**Description:** Verify proper error handling when neither username nor userId is provided.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!"
  }'
```

**Expected Response:**
```
422 Unprocessable Entity (Pydantic validation error)
```

**Expected Status:** `422` (or validation error)

**Test Checklist:**
- [ ] Request is rejected with validation error
- [ ] No message is processed
- [ ] Error response indicates missing parameter

**Notes:**
- This is handled by Pydantic validation in ChatRequest.__init__

---

#### 2.4 Chat Request with Non-existent User

**Endpoint:** `POST /chat`

**Description:** Verify error handling when user doesn't exist in database.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nonexistent_user_xyz",
    "message": "Hello!"
  }'
```

**Expected Response:**
```json
{
  "error": "User not found"
}
```

**Expected Status:** `200 OK` (returns error in JSON)

**Test Checklist:**
- [ ] Returns status 200
- [ ] Response contains "error" field
- [ ] Error message is "User not found"
- [ ] No conversation is created
- [ ] No message is saved

---

#### 2.5 Chat Request with Empty Message

**Endpoint:** `POST /chat`

**Description:** Test behavior with empty message string.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "message": ""
  }'
```

**Expected Response:**
Depends on implementation - chatbot should handle gracefully

**Test Checklist:**
- [ ] Request is processed
- [ ] Observe chatbot response behavior
- [ ] Check if message is saved to database

---

#### 2.6 Chat Request with Very Long Message

**Endpoint:** `POST /chat`

**Description:** Test with large message payload.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "message": "This is a very long message. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
  }'
```

**Expected Response:**
Should process normally

**Test Checklist:**
- [ ] Request is accepted
- [ ] Response is generated
- [ ] Message is saved to database
- [ ] No truncation occurs unexpectedly

---

#### 2.7 Multiple Sequential Messages from Same User

**Endpoint:** `POST /chat`

**Description:** Test conversation history is maintained across messages.

**Requests:**
```bash
# Message 1
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "message": "What is my department?"
  }'

# Message 2 (immediately after)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "message": "Who is my manager?"
  }'
```

**Expected Behavior:**
- [ ] Both messages are saved
- [ ] Second response may reference previous message context
- [ ] Both messages appear in conversation history

**Verification:**
- Use `/history/testuser2` to confirm both messages are stored

---

### 3. History Endpoint

#### 3.1 Get History for User with Existing Conversation

**Endpoint:** `GET /history/{username}`

**Description:** Retrieve chat history for a user with prior messages.

**Request:**
```bash
curl http://localhost:8000/history/testuser1
```

**Expected Response:**
```json
{
  "username": "testuser1",
  "history": [
    {
      "sender": "User",
      "message": "What is the HR policy on vacation days?"
    },
    {
      "sender": "Noxy",
      "message": "Here is the HR policy on vacation days..."
    }
  ]
}
```

**Expected Status:** `200 OK`

**Test Checklist:**
- [ ] Returns status 200
- [ ] Response contains "username" field
- [ ] Response contains "history" array
- [ ] Each history item has "sender" and "message"
- [ ] Messages are in chronological order
- [ ] All previous messages appear

---

#### 3.2 Get History for Non-existent User

**Endpoint:** `GET /history/{username}`

**Description:** Verify error handling for non-existent user.

**Request:**
```bash
curl http://localhost:8000/history/nonexistent_user_xyz
```

**Expected Response:**
```json
{
  "error": "User not found"
}
```

**Expected Status:** `200 OK`

**Test Checklist:**
- [ ] Returns status 200
- [ ] Response contains "error" field
- [ ] Error message is "User not found"

---

#### 3.3 Get History for User with No Conversations

**Endpoint:** `GET /history/{username}`

**Description:** Get history for a user that exists but has no messages.

**Request:**
```bash
# First, you need a user with no conversations
curl http://localhost:8000/history/newuser_with_no_history
```

**Expected Response:**
```json
{
  "history": []
}
```

**Expected Status:** `200 OK`

**Test Checklist:**
- [ ] Returns status 200
- [ ] Response contains "history" field
- [ ] History array is empty
- [ ] No error is raised

---

#### 3.4 History Endpoint with Special Characters in Username

**Endpoint:** `GET /history/{username}`

**Description:** Test with usernames containing special characters.

**Request:**
```bash
curl "http://localhost:8000/history/user%2Btest%40example"
```

**Expected Behavior:**
- [ ] URL encoding is handled correctly
- [ ] User lookup works with special characters
- [ ] Returns appropriate result

---

### 4. Integration Tests

#### 4.1 Complete User Journey

**Scenario:** Create new user, send multiple messages, retrieve history

**Steps:**

1. Send first message:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "journey_user",
    "message": "Hello! I am new here."
  }'
```

2. Send second message:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "journey_user",
    "message": "What should I do first?"
  }'
```

3. Retrieve full history:
```bash
curl http://localhost:8000/history/journey_user
```

**Verification Checklist:**
- [ ] Both messages are saved with correct sender
- [ ] History retrieval shows all 4 entries (2 user, 2 bot)
- [ ] Messages are in correct order
- [ ] Timestamps are reasonable

---

## Test Execution Template

Use this template to document your test results:

```markdown
### Test: [Test Name]
- Status: [PASS/FAIL]
- Endpoint: [Endpoint tested]
- Date: [Date tested]
- Notes: [Any observations or issues]
- Response Time: [How long request took]
```

---

## Database Verification

After running tests, verify data in database:

```sql
-- Check if user was created
SELECT * FROM ApplicationUsers WHERE UserName = 'testuser1';

-- Check conversations
SELECT * FROM Conversations WHERE UserId = 'user-id-here';

-- Check messages
SELECT * FROM ChatMessages WHERE ConvoId = 1;
```

---

## Common Issues and Solutions

### Issue: "User not found" Error
**Solution:** Ensure the user exists in the ApplicationUsers table before testing the chat endpoint.

### Issue: Database Connection Error
**Solution:** Verify SQL Server is running and credentials in `.env` are correct.

### Issue: No Response from Chatbot
**Solution:** Verify Azure OpenAI credentials are set correctly in `.env` and the API key is valid.

### Issue: CORS Errors in Frontend
**Solution:** Verify CORS middleware is configured in main.py for your frontend URL.

---

## Performance Benchmarks

Target response times (for reference):
- Health check: < 10ms
- Chat endpoint: < 2000ms (includes Azure OpenAI latency)
- History endpoint: < 500ms

---

## Notes

- The API currently returns status 200 for most errors. Consider implementing proper HTTP status codes (404, 400, 500) for better API design.
- The download-pdf endpoint has been removed and should not be tested.
- All endpoints support CORS for Vite frontend (localhost:3000 and 5173).
- The chat endpoint uses conversation history from the most recent conversation only.

---

**Last Updated:** 2025-11-14
**Test Version:** 1.0
