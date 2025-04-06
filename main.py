from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import re
import os
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI(title="SHL Assessment Recommendation System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)

# Load assessment data for direct access
assessments_df = pd.read_csv("shl_assessments_with_skills.csv")

# Initialize LLM with specific temperature for better deterministic results
model = OllamaLLM(model="llama3.2", temperature=0.2)

# Create improved prompt template with clear structure
# Create improved prompt template with clear structure
template = """
You are an expert consultant who specializes in recommending SHL assessments for hiring managers.

Given the job description or query, analyze it to understand the skills, experience level, and requirements needed.
Then recommend the most appropriate SHL assessments from the following options:

{assessments}

Based on the query: {query}

IMPORTANT: You must respond with a valid JSON object containing an array of recommendations.
The JSON must have this exact structure:
{{
    "recommendations": [
        {{
            "name": "Assessment Name",
            "url": "Assessment URL",
            "remote_testing": "Yes or No",
            "adaptive_support": "Yes or No",
            "duration": "Duration in minutes",
            "type": "Assessment Type",
            "explanation": "Brief explanation of why this assessment is recommended"
        }},
        ... additional recommendations (max 10 total) ...
    ]
}}

Consider time constraints mentioned in the query, technical skills required, and the role level.
Sort the assessments from most relevant to least relevant.
Limit the recommendations to a maximum of 10, minimum of 1.
Your response MUST be a valid, parseable JSON object exactly as specified above.
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

def extract_text_from_url(url):
    """Extract text content from a job description URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
        else:
            return f"Failed to retrieve content from URL: {response.status_code}"
    except Exception as e:
        return f"Error processing URL: {str(e)}"

def recommend_assessments(query_text):
    """Get assessment recommendations based on query text"""
    if not query_text.strip():
        return {"error": "Query text is empty"}
    
    # Retrieve relevant assessments
    assessments = retriever.invoke(query_text)
    
    # Convert assessments to a string representation for the prompt
    assessment_str = ""
    for doc in assessments:
        assessment_str += doc.page_content + "\n\n"
    
    # Generate recommendations with LLM
    result = chain.invoke({"assessments": assessment_str, "query": query_text})
    
    # Process the result to ensure JSON format
    try:
        # Try to extract JSON content if surrounded by markdown code blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", result)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If not in code blocks, try to find anything that looks like JSON
            json_match = re.search(r"(\{[\s\S]*\})", result)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result
        
        # Clean up any non-JSON text before or after the JSON object
        json_str = re.sub(r'^[^{]*', '', json_str)
        json_str = re.sub(r'[^}]*$', '', json_str)
        
        # Parse JSON string to dict
        recommendations = json.loads(json_str)
        
        # If LLM didn't return recommendations in the expected format, create a fallback
        if "recommendations" not in recommendations:
            # Create fallback recommendations from vector results
            fallback_recs = []
            for doc in assessments[:10]:  # Limit to top 10
                metadata = doc.metadata
                fallback_recs.append({
                    "name": metadata.get("name", "Unknown Assessment"),
                    "url": metadata.get("url", "#"),
                    "remote_testing": metadata.get("remote_testing", "No"),
                    "adaptive_support": metadata.get("adaptive_support", "No"),
                    "duration": metadata.get("duration", "Unknown"),
                    "type": metadata.get("type", "Unknown"),
                    "explanation": f"This assessment matches your query for skills in {metadata.get('skills', 'various areas')}."
                })
            return {"recommendations": fallback_recs}
        
        return recommendations
        
    except Exception as e:
        # If JSON parsing fails, create a fallback response from the retrieved documents
        fallback_recs = []
        for doc in assessments[:10]:  # Limit to top 10
            metadata = doc.metadata
            fallback_recs.append({
                "name": metadata.get("name", "Unknown Assessment"),
                "url": metadata.get("url", "#"),
                "remote_testing": metadata.get("remote_testing", "No"),
                "adaptive_support": metadata.get("adaptive_support", "No"),
                "duration": metadata.get("duration", "Unknown"),
                "type": metadata.get("type", "Unknown"),
                "explanation": f"This assessment matches your query for skills in {metadata.get('skills', 'various areas')}."
            })
        return {"recommendations": fallback_recs}

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/recommend")
async def api_recommend(query: str = Query(None), url: str = Query(None)):
    """API endpoint for recommendations"""
    if url:
        # Extract text from URL
        text = extract_text_from_url(url)
        return recommend_assessments(text)
    elif query:
        # Use the provided query directly
        return recommend_assessments(query)
    else:
        return JSONResponse(content={"error": "No query or URL provided"}, status_code=400)

# Direct database access endpoint for testing
@app.get("/api/assessments")
async def get_all_assessments():
    """Return all assessments in the database for testing"""
    assessments_list = assessments_df.to_dict(orient="records")
    return {"assessments": assessments_list}

# CLI interface
def cli_interface():
    while True:
        print("\n\n-------------------------------")
        print("SHL Assessment Recommendation System")
        print("1. Enter query text")
        print("2. Enter job description URL")
        print("q. Quit")
        choice = input("Choose an option: ")
        
        if choice == "q":
            break
        elif choice == "1":
            query = input("Enter your query: ")
            print("\nProcessing...\n")
            result = recommend_assessments(query)
            
            # Pretty print recommendations
            if "recommendations" in result and result["recommendations"]:
                print("\n=== RECOMMENDED ASSESSMENTS ===\n")
                for i, rec in enumerate(result["recommendations"], 1):
                    print(f"{i}. {rec['name']} ({rec['type']})")
                    print(f"   Duration: {rec['duration']}")
                    print(f"   Remote Testing: {rec['remote_testing']}")
                    print(f"   Adaptive Support: {rec['adaptive_support']}")
                    print(f"   URL: {rec['url']}")
                    print(f"   Why: {rec['explanation']}")
                    print()
            else:
                print("No matching assessments found or an error occurred.")
                print(result)
        elif choice == "2":
            url = input("Enter job description URL: ")
            print("\nExtracting text from URL...\n")
            text = extract_text_from_url(url)
            print("\nProcessing...\n")
            result = recommend_assessments(text)
            
            # Pretty print recommendations
            if "recommendations" in result and result["recommendations"]:
                print("\n=== RECOMMENDED ASSESSMENTS ===\n")
                for i, rec in enumerate(result["recommendations"], 1):
                    print(f"{i}. {rec['name']} ({rec['type']})")
                    print(f"   Duration: {rec['duration']}")
                    print(f"   Remote Testing: {rec['remote_testing']}")
                    print(f"   Adaptive Support: {rec['adaptive_support']}")
                    print(f"   URL: {rec['url']}")
                    print(f"   Why: {rec['explanation']}")
                    print()
            else:
                print("No matching assessments found or an error occurred.")
                print(result)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        cli_interface()
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)