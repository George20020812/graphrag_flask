

import asyncio
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import File, UploadFile
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# The graphrag library will be installed in the environment, so we can import it directly.
from graphrag.cli.initialize import initialize_project_at
from graphrag.cli.index import index_cli
from graphrag.cli.query import run_local_search, run_global_search


# --- FastAPI App Initialization ---
app = FastAPI(
    title="GraphRAG API",
    description="An API to interact with the GraphRAG indexing and querying pipelines.",
)

# --- Project Directory Setup ---
API_PROJECTS_DIR = Path("./api_projects")
API_PROJECTS_DIR.mkdir(exist_ok=True)

# --- Pydantic Models for API Requests ---
class CreateProjectRequest(BaseModel):
    text_content: str
    api_key: str
    llm: str = "openai" # or "azure"
    # Add other Azure-specific fields if needed
    azure_api_base: str | None = None
    azure_api_version: str | None = None
    azure_deployment_name: str | None = None


class QueryRequest(BaseModel):
    query: str
    method: str = "global"




# --- API Endpoints ---

@app.post("/create_project", status_code=201)
async def create_project(request: CreateProjectRequest):
    """
    Creates a new GraphRAG project.
    - Generates a unique project ID.
    - Creates a project directory structure.
    - Writes the provided text content to an input file.
    - Initializes the GraphRAG configuration.
    - Sets the API key.
    """
    project_id = str(uuid.uuid4())
    project_path = API_PROJECTS_DIR / project_id
    try:
        # 1. Create directory structure
        input_path = project_path / "input"
        input_path.mkdir(parents=True, exist_ok=True)

        # 2. Write text content to a file if it exists
        if request.text_content and request.text_content.strip():
            (input_path / "source_text.txt").write_text(request.text_content, encoding="utf-8")

        # 3. Initialize the project (creates settings.yaml and .env)
        initialize_project_at(path=str(project_path), force=True)

        # 4. Configure API Key and LLM settings
        (project_path / ".env").write_text(f"GRAPHRAG_API_KEY={request.api_key}")
        
        # A simple way to update YAML without a full library
        settings_path = project_path / "settings.yaml"
        with open(settings_path, "r") as f:
            settings = f.read()

        if request.llm == "azure":
            # This is a simplified update. A more robust solution would use a YAML library.
            azure_config = f"""
type: azure_openai_chat
api_base: {request.azure_api_base}
api_version: {request.azure_api_version}
deployment_name: {request.azure_deployment_name}
"""
            # Replace the default chat model config
            # This regex is basic and might need adjustment for different settings files
            import re
            settings = re.sub(r"llm:\n  type: openai_chat", "llm:\n" + azure_config, settings, flags=re.MULTILINE)
            
        with open(settings_path, "w") as f:
            f.write(settings)

        return {"project_id": project_id, "message": "Project created successfully."}
    except Exception as e:
        # Clean up if project creation fails
        if project_path.exists():
            shutil.rmtree(project_path)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@app.post("/index/{project_id}")
async def run_indexing(project_id: str):
    """
    Runs the indexing pipeline for a given project_id.
    This is a long-running process.
    """
    project_path = API_PROJECTS_DIR / project_id
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        # Run indexing in a separate thread to avoid blocking the event loop for too long
        # For a real production app, use a task queue like Celery or ARQ.
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: index_cli(root_dir=project_path, verbose=True)
        )
        return {"project_id": project_id, "message": "Indexing process started and completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.post("/query/{project_id}")
async def run_query(project_id: str, request: QueryRequest):
    """
    Runs a query against an indexed project.
    """
    project_path = API_PROJECTS_DIR / project_id
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found.")
    
    # The output directory is needed for the query
    output_path = project_path / "output"
    if not output_path.exists():
        raise HTTPException(status_code=400, detail="Project has not been indexed yet.")

    try:
        # The query functions are async, but the CLI wrappers are sync.
        # We run them in an executor to be safe.
        loop = asyncio.get_event_loop()
        
        search_fn = None
        if request.method == "local":
            search_fn = run_local_search
        elif request.method == "global":
            search_fn = run_global_search
        else:
            raise HTTPException(status_code=400, detail=f"Invalid search method: {request.method}")

        response, context_data = await loop.run_in_executor(
            None,
            lambda: search_fn(
                root_dir=project_path,
                data_dir=None, # Let it use the default from root
                config_filepath=None,
                community_level=2, # Default value from CLI
                response_type="Multiple Paragraphs", # Default value
                streaming=False, # Return the full response
                query=request.query,
                verbose=False,
            ),
        )
        
        # The response object might not be directly JSON serializable.
        # Based on the code, it seems to be a string.
        return {
            "project_id": project_id,
            "query": request.query,
            "method": request.method,
            "response": str(response),
            "context_data": "Context data is available but not serialized in this response.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/upload_txt/{project_id}")
async def upload_txt_files(project_id: str, files: List[UploadFile] = File(...)):
    """
    Uploads text files directly to the project's input directory.
    """
    project_path = API_PROJECTS_DIR / project_id
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found.")

    input_path = project_path / "input"
    if not input_path.exists():
        input_path.mkdir(parents=True, exist_ok=True)

    results = {"successful": [], "failed": []}

    for file in files:
        try:
            # Ensure the filename is safe and unique
            file_name = f"{uuid.uuid4()}_{file.filename}"
            file_path = input_path / file_name
            
            # Write content to the file
            file_path.write_bytes(await file.read())
            
            results["successful"].append(file.filename)
        except Exception as e:
            logging.error(f"Failed to upload {file.filename}: {e}")
            results["failed"].append({"filename": file.filename, "reason": str(e)})
    
    if not results["successful"]:
        raise HTTPException(status_code=400, detail={"message": "No files could be uploaded.", "results": results})

    return {
        "project_id": project_id,
        "message": f"Processed {len(files)} files. {len(results['successful'])} successful, {len(results['failed'])} failed.",
        "results": results
    }


@app.delete("/project/{project_id}")
async def delete_project(project_id: str):
    """
    Deletes a GraphRAG project and all its associated data.
    """
    project_path = API_PROJECTS_DIR / project_id
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        shutil.rmtree(project_path)
        return {"project_id": project_id, "message": "Project deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


@app.get("/projects")
async def list_projects():
    """
    Lists all existing GraphRAG project IDs.
    """
    projects = [d.name for d in API_PROJECTS_DIR.iterdir() if d.is_dir()]
    return {"projects": projects}


if __name__ == "__main__":
    print("Starting GraphRAG API server...")
    print("Access the interactive docs at http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)