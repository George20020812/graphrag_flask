# GraphRAG API Server

This project provides a REST API wrapper around the Microsoft GraphRAG library using FastAPI. It exposes the core indexing and querying functionalities, making it easy to integrate GraphRAG with other applications, such as n8n workflows.

## Features

- **Simple Interface:** A straightforward API for complex GraphRAG operations.
- **Project-Based:** Manages data and indexes in isolated project folders.
- **Integratable:** Designed for easy integration with automation tools and other services.

## Quick Start

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/George20020812/graphrag_flask.git
    cd graphrag_flask
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Environment:**
    -   **Windows:**
        ```bash
        .venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the API Server:**
    ```bash
    python api_server.py
    ```

6.  **Access Interactive Docs:**
    Open your browser and navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to explore and interact with the API endpoints.

## API Endpoints

-   `POST /create_project`: Creates a new project from a block of text and returns a `project_id`.
-   `POST /index/{project_id}`: Triggers the indexing pipeline on the specified project.
-   `POST /query/{project_id}`: Runs a query against the indexed data of the specified project.

For more detailed information on development and workflow, please see the [DEVELOPING.md](DEVELOPING.md) file.
