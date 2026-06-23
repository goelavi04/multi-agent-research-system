# main.py
# FastAPI backend — receives a question, runs the multi-agent pipeline, returns the report

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agents import run_research_pipeline

app = FastAPI()


class ResearchRequest(BaseModel):
    question: str


@app.post("/research")
async def research(request: ResearchRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = run_research_pipeline(request.question)

        return {
            "question": result["question"],
            "report": result["report"],
            "insights": result["insights"],
            "sources": result["raw_results"],
            "activity_log": result["activity_log"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


# Mount static files last to avoid conflicting with API routes
app.mount("/static", StaticFiles(directory="static"), name="static")