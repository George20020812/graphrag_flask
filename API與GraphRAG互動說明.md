# API 伺服器與 GraphRAG 函式庫的互動說明

## 核心比喻

您可以將這個系統想像成一間餐廳：

- **您 (使用者)**：顧客，提出需求。
- **API 伺服器 (api_server.py)**：服務生，負責點餐、送餐，與廚房溝通。
- **GraphRAG 函式庫**：廚房，擁有真正的技術和工具，負責烹飪。

服務生 (API) 本身不烹飪，它只是將您的請求轉達給廚房 (GraphRAG)，然後將成品回傳給您。

---

## 三個主要步驟

### 1. `POST /create_project` (建立專案)

- **您的操作**：提供一段文字給「服務生」。
- **背後發生什麼**：「服務生」將您的文字送到「廚房」，「廚房」(GraphRAG) 會準備一個專屬的工作區和設定檔。

### 2. `POST /index/{project_id}` (執行索引)

- **您的操作**：告訴「服務生」可以開始處理了。
- **背後發生什麼**：「服務生」通知「廚房」開工。「廚房」(GraphRAG) 會執行最核心的工作：閱讀您的文字、找出關鍵實體、建立知識圖譜，並將結果儲存起來。這是最耗時的步驟。

### 3. `POST /query/{project_id}` (進行查詢)

- **您的操作**：向「服務生」提出一個問題。
- **背後發生什麼**：「服務生」將您的問題轉達給「廚房」。「廚房」(GraphRAG) 在已經建立好的知識圖譜中尋找答案，然後將答案交給「服務生」，最後由「服務生」回傳給您。

---

# 使用 Postman 訪問 API

## 通用步驟：

1.  **啟動 API 伺服器：** 確保您的 API 伺服器正在運行。在 `E:\graphrag\graphrag_api_project` 目錄下雙擊 `start_api.bat`。
2.  **開啟 Postman：** 啟動 Postman 應用程式。
3.  **建立新請求：** 點擊 Postman 左上角的 `+` 號或 `New` 按鈕，選擇 `HTTP Request`。

---

## 1. 建立專案 (`POST /create_project`)

-   **方法 (Method)：** 選擇 `POST`。
-   **URL：** 輸入 `http://127.0.0.1:8000/create_project`。
-   **Headers (標頭)：**
    *   在 `Headers` 標籤下，新增：
        *   `Key`: `Content-Type`
        *   `Value`: `application/json`
-   **Body (請求主體)：**
    *   選擇 `Body` 標籤。
    *   選擇 `raw` 選項，然後從下拉選單中選擇 `JSON`。
    *   輸入以下 JSON 內容 (請將 `YOUR_TEXT_CONTENT` 和 `YOUR_OPENAI_API_KEY` 替換為實際值)：
        ```json
        {
          "text_content": "這是您要索引的長篇文字內容，例如一篇文章、報告或文件。",
          "api_key": "sk-您的OpenAI或AzureOpenAI金鑰",
          "llm": "openai"
        }
        ```
        *   **如果使用 Azure OpenAI：** 請將 `llm` 設為 `"azure"`，並加入 `azure_api_base`, `azure_api_version`, `azure_deployment_name` 欄位。
-   **發送 (Send)：** 點擊 `Send` 按鈕。
-   **預期回應：** 成功會返回 `201 Created` 狀態碼，並在回應中包含一個 `project_id`。**請記下這個 `project_id`，後續操作會用到。**

---

## 2. 索引專案 (`POST /index/{project_id}`)

-   **方法 (Method)：** 選擇 `POST`。
-   **URL：** 輸入 `http://127.0.0.1:8000/index/YOUR_PROJECT_ID` (請將 `YOUR_PROJECT_ID` 替換為您上一步獲得的 `project_id`)。
-   **Headers (標頭)：**
    *   在 `Headers` 標籤下，新增：
        *   `Key`: `Content-Type`
        *   `Value`: `application/json` (即使沒有 Body，也建議設置)
-   **Body (請求主體)：** 留空或選擇 `none`。
-   **發送 (Send)：** 點擊 `Send` 按鈕。
-   **預期回應：** 成功會返回 `200 OK` 狀態碼，並顯示索引完成的訊息。**這個過程可能需要一些時間，請耐心等待。**

---

## 3. 查詢專案 (`POST /query/{project_id}`)

-   **方法 (Method)：** 選擇 `POST`。
-   **URL：** 輸入 `http://127.0.0.1:8000/query/YOUR_PROJECT_ID` (請將 `YOUR_PROJECT_ID` 替換為您之前獲得的 `project_id`)。
-   **Headers (標頭)：**
    *   在 `Headers` 標籤下，新增：
        *   `Key`: `Content-Type`
        *   `Value`: `application/json`
-   **Body (請求主體)：**
    *   選擇 `Body` 標籤。
    *   選擇 `raw` 選項，然後從下拉選單中選擇 `JSON`。
    *   輸入以下 JSON 內容 (請將 `YOUR_QUERY_TEXT` 替換為您的問題)：
        ```json
        {
          "query": "文本中的主要主題是什麼？",
          "method": "global"
        }
        ```
        *   `method` 可以是 `"global"` (廣泛查詢) 或 `"local"` (局部查詢)。
-   **發送 (Send)：** 點擊 `Send` 按鈕。
-   **預期回應：** 成功會返回 `200 OK` 狀態碼，並在回應中包含查詢結果。

---

## 4. 列出所有專案 (`GET /projects`)

-   **方法 (Method)：** 選擇 `GET`。
-   **URL：** 輸入 `http://127.0.0.1:8000/projects`。
-   **Headers (標頭)：** 無需特殊設置。
-   **Body (請求主體)：** 留空或選擇 `none`。
-   **發送 (Send)：** 點擊 `Send` 按鈕。
-   **預期回應：** 成功會返回 `200 OK` 狀態碼，並在回應中包含一個 `projects` 列表，列出所有專案 ID。

---

## 5. 刪除專案 (`DELETE /project/{project_id}`)

-   **方法 (Method)：** 選擇 `DELETE`。
-   **URL：** 輸入 `http://127.0.0.1:8000/project/YOUR_PROJECT_ID` (請將 `YOUR_PROJECT_ID` 替換為您要刪除的專案 ID)。
-   **Headers (標頭)：** 無需特殊設置。
-   **Body (請求主體)：** 留空或選擇 `none`。
-   **發送 (Send)：** 點擊 `Send` 按鈕。
-   **預期回應：** 成功會返回 `200 OK` 狀態碼，並顯示刪除成功的訊息。