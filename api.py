import os
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from src.resume_builder.crew import ResumeBuilderCrew

load_dotenv()

app = FastAPI(
    title="Resume Builder API",
    description="An API to generate a tailored resume by providing job details and professional links.",
    version="1.0.0"
)

class CrewInputs(BaseModel):
    job_description: str = Field(..., description="The detailed job description for the target role.")
    linkedin_url: str = Field(..., description="The URL of the user's LinkedIn profile.")
    github_url: str = Field(..., description="The URL of the user's GitHub profile.")
    personal_blog_url: str | None = Field(None, description="Optional: The URL of the user's personal blog or portfolio.")

@app.post("/generate-resume")
def generate_resume(
    payload: CrewInputs
):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(
            status_code=500, 
            detail="GROQ_API_KEY environment variable is not set. The API cannot function without it."
        )
    
    try:
        inputs = payload.model_dump()
        resume_crew = ResumeBuilderCrew()
        result = resume_crew.crew().kickoff(inputs=inputs)
        return {"resume": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during crew execution: {str(e)}")
        
@app.get("/")
def read_root():
    return {"status": "Resume Builder API is online and ready."}