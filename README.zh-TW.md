# GraphRAG API 伺服器 (繁體中文)

本專案使用 FastAPI 為 Microsoft GraphRAG 函式庫提供一個 REST API 封裝。它公開了核心的索引和查詢功能，使其能輕鬆地與 n8n 等其他應用程式整合。

## 功能

- **簡單介面:** 為複雜的 GraphRAG 操作提供直接的 API。
- **專案導向:** 在隔離的專案資料夾中管理資料和索引。
- **易於整合:** 為與自動化工具和其他服務輕鬆整合而設計。

## 快速入門

1.  **複製儲存庫:**
    ```bash
    git clone https://github.com/George20020812/graphrag_flask.git
    cd graphrag_flask
    ```

2.  **建立虛擬環境:**
    ```bash
    python -m venv .venv
    ```

3.  **啟用環境:**
    -   **Windows:**
        ```bash
        .venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  **安裝相依套件:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **執行 API 伺服器:**
    -   **Windows 使用者:**
        直接在專案根目錄下雙擊 `start_api.bat` 檔案。
    -   **其他使用者 (或手動執行):**
        ```bash
        python api_server.py
        ```

6.  **存取互動式文件:**
    在您的瀏覽器中開啟 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 來探索並與 API 端點互動。

## API 端點

-   `POST /create_project`: 從一段文字建立一個新專案，並返回一個 `project_id`。
-   `POST /index/{project_id}`: 對指定的專案觸發索引流程。
-   `POST /query/{project_id}`: 對指定專案的已索引資料執行查詢。

更多詳細的開發與工作流程資訊，請參閱 [DEVELOPING.zh-TW.md](DEVELOPING.zh-TW.md) 檔案。
