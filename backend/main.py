import uuid
from fastapi import FastAPI, HTTPException
from agents.graph import chat
from dto.chat_response import ChatResponse
from dto.chat_request import ChatRequest

app = FastAPI(title="ThesisMate API")

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest) -> ChatResponse:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty.")

    thread_id = req.thread_id or str(uuid.uuid4())
    try:
        return ChatResponse(thread_id=thread_id, **chat(req.message, thread_id))
    except Exception as e:
        print(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")


def main():
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

 
if __name__ == "__main__":
    main()
