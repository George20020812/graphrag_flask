# Development Guide

## 1. Introduction

This document provides detailed instructions for setting up, running, and understanding the GraphRAG API Server project.

The primary purpose of this project is to create a stable, easy-to-use REST API interface for the powerful functionalities of the Microsoft GraphRAG library. By wrapping GraphRAG's command-line operations in a web server, we make it accessible to a wide range of applications, from automation platforms like n8n to custom web frontends.

**Core Technologies:**
- **Python:** The programming language used.
- **FastAPI:** A modern, high-performance web framework for building APIs.
- **GraphRAG:** The underlying library for all indexing and querying logic.
- **Uvicorn:** The server that runs the FastAPI application.

## 2. Environment Setup

Follow these steps to create a local development environment.

### Prerequisites

-   **Python:** Version 3.10 or higher.
-   **Git:** For cloning the repository.

### Step 1: Clone the Repository

```bash
git clone https://github.com/George20020812/graphrag_flask.git
cd graphrag_flask
```

### Step 2: Create a Virtual Environment

A virtual environment is crucial for isolating project dependencies and avoiding conflicts with other Python projects on your system.

```bash
# This command creates a directory named .venv for the environment
python -m venv .venv
```

### Step 3: Activate the Environment

You must activate the environment in your terminal session before installing dependencies or running the app.

-   **On Windows:**
    ```powershell
    .venv\Scripts\activate
    ```
-   **On macOS and Linux:**
    ```bash
    source .venv/bin/activate
    ```

Your terminal prompt should change to indicate that the virtual environment is active.

### Step 4: Install Dependencies

The `requirements.txt` file contains all the Python packages needed for this project.

```bash
# Ensure your virtual environment is active
pip install -r requirements.txt
```

## 3. Running the Application

With the environment set up and dependencies installed, you can run the API server.

```bash
python api_server.py
```

You should see output from Uvicorn indicating the server is running:

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

To access the interactive API documentation, open your browser to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## 4. Project Structure

-   `api_server.py`: The main application file. It contains all the FastAPI logic, endpoint definitions, and calls to the GraphRAG library.
-   `requirements.txt`: A list of all Python packages required for the project.
-   `.gitignore`: Specifies files and directories that Git should ignore. This is configured to exclude virtual environments, IDE settings, and runtime data.
-   `api_projects/`: **(Runtime Directory)** This directory is created automatically when you first run the server. It stores the data for each project created via the API. Each subfolder within `api_projects/` corresponds to a `project_id` and contains its own `input` files, `settings.yaml`, `.env`, and `output` (the indexed data). This directory is intentionally excluded from Git by `.gitignore`.

## 5. API Workflow

This API is designed to be used in a specific sequence. Here is a step-by-step guide to the intended workflow.

### Step 1: Create a Project

-   **Endpoint:** `POST /create_project`
-   **Purpose:** To initialize a new, isolated GraphRAG project.
-   **Request Body:**
    ```json
    {
      "text_content": "Your long block of text to be indexed...",
      "api_key": "Your OpenAI or Azure OpenAI API Key",
      "llm": "openai",
      "azure_api_base": "https://your-instance.openai.azure.com",
      "azure_api_version": "2024-02-15-preview",
      "azure_deployment_name": "your-deployment"
    }
    ```
    *   `text_content` and `api_key` are required.
    *   Azure-related fields are only needed if `llm` is set to `"azure"`.
-   **Response:** A JSON object containing the unique `project_id` for this new project.
    ```json
    {
      "project_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "message": "Project created successfully."
    }
    ```

### Step 2: Index the Project

-   **Endpoint:** `POST /index/{project_id}`
-   **Purpose:** To run the GraphRAG indexing pipeline on the data you provided during project creation.
-   **URL Parameter:** Replace `{project_id}` with the ID you received from Step 1.
-   **Note:** This is a long-running, resource-intensive process. The API will wait for it to complete before sending a response. For production use, consider modifying the server to run this as a background task (e.g., using Celery or FastAPI's `BackgroundTasks`).

### Step 3: Query the Project

-   **Endpoint:** `POST /query/{project_id}`
-   **Purpose:** To ask questions and extract insights from your indexed data.
-   **URL Parameter:** Use the same `project_id`.
-   **Request Body:**
    ```json
    {
      "query": "What are the main themes in the text?",
      "method": "global"
    }
    ```
    *   `method` can be `"global"` for broad, high-level questions or `"local"` for specific, detailed questions.
-   **Response:** A JSON object containing the answer generated by the GraphRAG engine.

## 6. Customization and Extension

-   **Query Parameters:** You can change the default query settings (e.g., `community_level`, `response_type`) directly within the `run_query` function in `api_server.py`.
-   **GraphRAG Configuration:** The core behavior of the indexing pipeline (chunking, entity extraction, etc.) is controlled by the `settings.yaml` file created for each project. To customize it, you can modify the `initialize_project_at` function's outputs within the `create_project` endpoint in `api_server.py`.
-   **Adding New Endpoints:** You can add new functionalities by defining new functions in `api_server.py` with the `@app` decorator (e.g., `@app.get("/my-new-endpoint")`).

## 7. Troubleshooting

-   **`404 Not Found` for `/index` or `/query`:** This almost always means the `project_id` in the URL is incorrect or does not exist.
-   **`400 Project has not been indexed yet`:** You have called `/query` on a project before successfully completing the `/index` step.
-   **Dependency Errors:** Ensure your virtual environment is active and that you have run `pip install -r requirements.txt`.
-   **Authentication Errors:** Double-check that the `api_key` you provided is correct and has the necessary permissions for the LLM you are trying to use.
