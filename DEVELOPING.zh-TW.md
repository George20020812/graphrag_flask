# 開發手冊 (繁體中文)

## 1. 簡介

本文件提供設定、執行與理解 GraphRAG API 伺服器專案的詳細說明。

本專案的主要目的是為功能強大的 Microsoft GraphRAG 函式庫建立一個穩定、易於使用的 REST API 介面。透過將 GraphRAG 的命令列操作封裝在一個網頁伺服器中，我們使其能被廣泛的應用程式存取，從像 n8n 這樣的自動化平台到客製化的網頁前端。

**核心技術:**
- **Python:** 本專案使用的程式語言。
- **FastAPI:** 一個用於建構 API 的現代、高效能網頁框架。
- **GraphRAG:** 所有索引和查詢邏輯的底層函式庫。
- **Uvicorn:** 執行 FastAPI 應用程式的伺服器。

## 2. 環境設定

請遵循以下步驟來建立本地開發環境。

### 先決條件

-   **Python:** 3.10 或更高版本。
-   **Git:** 用於複製儲存庫。

### 步驟 1: 複製儲存庫

```bash
git clone https://github.com/George20020812/graphrag_api.git
cd graphrag_api
```

### 步驟 2: 設定環境變數

在專案根目錄下建立一個名為 `.env` 的檔案。此檔案用於存放敏感資訊，例如您的 API 金鑰。如果檔案已存在，請確保其包含必要變數。

```env
# .env 檔案範例
GRAPHRAG_API_KEY="YOUR_GEMINI_OR_AZURE_API_KEY"

```
**重要提示:** `api_server.py` 會自動從此檔案讀取金鑰。如果在 API 請求中未提供 `api_key`，則必須在此處設定。

### 步驟 3: 建立虛擬環境

虛擬環境對於隔離專案的相依套件至關重要。

```bash
python -m venv .venv
```

### 步驟 4: 啟用環境

-   **在 Windows 上:**
    ```powershell
    .venv\Scripts\activate
    ```
-   **在 macOS 和 Linux 上:**
    ```bash
    source .venv/bin/activate
    ```

### 步驟 5: 安裝相依套件

```bash
pip install -r requirements.txt
```

## 3. 執行應用程式

在環境設定完成且相依套件安裝後，您就可以執行 API 伺服器。

-   **推薦 (Windows 使用者，含環境設定與路徑檢查):**
    直接在專案根目錄下雙擊 `open_console.bat` 檔案。它會自動啟用虛擬環境並檢查必要檔案，然後開啟一個已設定好環境的命令提示字元視窗。在該視窗中，輸入 `python api_server.py` 即可啟動伺服器。


您應該會看到 Uvicorn 的輸出，表示伺服器正在執行中：

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

要存取互動式 API 文件，請在瀏覽器中開啟 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)。

## 4. 專案結構

-   `api_server.py`: 主要的應用程式檔案。它包含了所有的 FastAPI 邏輯、端點定義，以及對 GraphRAG 函式庫的呼叫。
-   `requirements.txt`: 列出專案所需的所有 Python 套件。
-   `.gitignore`: 指定 Git 應該忽略的檔案和目錄。它被設定為排除虛擬環境、IDE 設定和執行時產生的資料。
-   `api_projects/`: **(執行時目錄)** 這個目錄在您第一次執行伺服器時會自動建立。它儲存了透過 API 建立的每個專案的資料。`api_projects/` 中的每個子資料夾都對應一個 `project_id`，並包含它自己的 `input` 檔案、`settings.yaml`、`.env` 和 `output` (已索引的資料)。此目錄被 `.gitignore` 刻意從 Git 中排除。

## 5. API 工作流程

此 API 被設計為依特定順序使用。以下是預期工作流程的逐步指南。

### 步驟 1: 建立專案

-   **端點:** `POST /create_project`
-   **目的:** 初始化一個新的、隔離的 GraphRAG 專案。
-   **請求內文 (Request Body):**
    ```json
    {
      "text_content": "要索引的初始文本內容 (可選)",
      "llm": "openai",
      "api_key": "您的 API 金鑰 (可選，若 .env 中已設定)",
      "azure_api_base": "Azure 端點 (可選，若 .env 中已設定)",
      "azure_api_version": "Azure API 版本 (可選)",
      "azure_deployment_name": "Azure 部署名稱 (可選)"
    }
    ```
    *   `text_content` 是可選的。如果留空，您可以後續透過 `/upload_txt` 端點上傳檔案。
    *   `llm` 預設為 `"openai"`。若設為 `"azure"`，則必須提供 Azure 相關設定 (可透過請求或 `.env` 檔案)。
    *   `api_key` 是可選的。如果請求中未提供，系統會自動從 `.env` 檔案讀取 `GRAPHRAG_API_KEY`。
-   **回應 (Response):** 一個包含此新專案唯一 `project_id` 的 JSON 物件。
    ```json
    {
      "project_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "message": "Project created successfully."
    }
    ```

### 步驟 2: 上傳資料 (可選)

如果您在建立專案時未提供 `text_content`，或者需要新增更多檔案，請使用此端點。

-   **端點:** `POST /upload_txt/{project_id}`
-   **目的:** 將一個或多個 `.txt` 檔案上傳到專案的 `input` 目錄。
-   **URL 參數:** 將 `{project_id}` 替換為從步驟 1 取得的 ID。
-   **請求:** 使用 `multipart/form-data` 格式上傳檔案。
-   **回應:**
    ```json
    {
      "project_id": "...",
      "message": "Processed 2 files. 2 successful, 0 failed.",
      "results": { "successful": ["file1.txt", "file2.txt"], "failed": [] }
    }
    ```

### 步驟 3: 索引專案

-   **端點:** `POST /index/{project_id}`
-   **目的:** 在您建立專案時提供的資料上執行 GraphRAG 索引流程。
-   **URL 參數:** 將 `{project_id}` 替換為您從上一步收到的 ID。
-   **注意:** 這是一個耗時且資源密集的操作。API 會等待其完成後才發送回應。對於正式的生產環境，請考慮修改伺服器以將其作為背景任務執行 (例如，使用 Celery 或 FastAPI 的 `BackgroundTasks`)。

### 步驟 4: 查詢專案

-   **端點:** `POST /query/{project_id}`
-   **目的:** 從您已索引的資料中提問並提取見解。
-   **URL 參數:** 使用相同的 `project_id`。
-   **請求內文 (Request Body):**
    ```json
    {
      "query": "文本中的主要主題是什麼？",
      "method": "global"
    }
    ```
    *   對於廣泛、高層次的問題，`method` 可以是 `"global"`；對於具體、詳細的問題，可以是 `"local"`。
-   **回應 (Response):** 一個包含由 GraphRAG 引擎生成答案的 JSON 物件。

### 步驟 5: 管理專案

-   **端點:** `DELETE /project/{project_id}`
-   **目的:** 刪除指定的 GraphRAG 專案及其所有相關資料。
-   **URL 參數:** 將 `{project_id}` 替換為您要刪除的專案 ID。
-   **回應 (Response):**
    ```json
    {
      "project_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "message": "Project deleted successfully."
    }
    ```

-   **端點:** `GET /projects`
-   **目的:** 列出所有目前存在的 GraphRAG 專案 ID。
-   **回應 (Response):** 一個包含所有專案 ID 列表的 JSON 物件。
    ```json
    {
      "projects": ["project_id_1", "project_id_2", "project_id_3"]
    }
    ```

## 6. `run_indexing` API 參數詳解

當您呼叫 `POST /index/{project_id}` 端點時，您可以選擇性地在請求的 JSON 內文中提供一個物件來覆寫 `graphrag` 索引流程的預設行為。以下是每個可用參數的詳細說明。

### 1. `method: str`
*   **功能說明**：控制索引的模式。
*   **預設值**：`"standard"`
*   **使用情境**：
    *   `"standard"`：從頭開始建立一個全新的索引。這是最常見的模式。

### 2. `memory_profile: bool`
*   **功能說明**：是否啟用記憶體分析。
*   **預設值**：`False`
*   **使用情境**：開發者工具。若索引過程佔用過多記憶體，設為 `True` 可產生記憶體用量報告以供效能分析。

### 3. `dry_run: bool`
*   **功能說明**：執行乾跑測試 (Dry Run)，模擬執行但不寫入檔案或呼叫 LLM。
*   **預設值**：`False`
*   **使用情境**：在正式執行前用來預覽執行計畫及檢查設定是否有效。

### 4. `output_dir: Optional[str]`
*   **功能說明**：指定最終索引結果的輸出目錄。
*   **預設值**：`None` (輸出到專案根目錄下的 `output` 資料夾)
*   **使用情境**：當您希望將索引檔案存放到一個與原始專案分離的集中位置時使用。

### 5. `verbose: bool`
*   **功能說明**：是否啟用詳細日誌輸出。
*   **預設值**：`True`
*   **使用情境**：設為 `True` 時，索引過程會印出詳細的執行步驟，方便追蹤進度和排查問題。

## 7. 客製化與擴充

-   **查詢參數:** 您可以直接在 `api_server.py` 的 `run_query` 函式中更改預設的查詢設定 (例如 `community_level`, `response_type`)。
-   **GraphRAG 設定:** 索引流程的核心行為 (如分塊、實體提取等) 是由為每個專案建立的 `settings.yaml` 檔案控制的。要客製化它，您可以在 `api_server.py` 的 `create_project` 端點中修改 `initialize_project_at` 函式的產出。
-   **新增端點:** 您可以透過在 `api_server.py` 中使用 `@app` 裝飾器定義新函式來新增功能 (例如 `@app.get("/my-new-endpoint")`)。

## 8. 疑難排解

-   **`/index` 或 `/query` 出現 `404 Not Found`:** 這幾乎總是意味著 URL 中的 `project_id` 不正確或不存在。
-   **`400 Project has not been indexed yet`:** 您在成功完成 `/index` 步驟之前就對專案呼叫了 `/query`。
-   **相依套件錯誤:** 確認您的虛擬環境已被啟用，並且您已經執行了 `pip install -r requirements.txt`。
-   **驗證錯誤:** 再次檢查您提供的 `api_key` 是否正確，以及它是否具有您嘗試使用的 LLM 所需的權限。