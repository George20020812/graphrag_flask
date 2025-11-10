import asyncio
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

from fastapi import File, UploadFile
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, root_validator

# 載入環境變數
load_dotenv()

# GraphRAG Core Libraries
from graphrag.config.load_config import load_config
from graphrag.config.enums import IndexingMethod
from graphrag.api import build_index

# GraphRAG CLI for project initialization and querying
from graphrag.cli.initialize import initialize_project_at
from graphrag.cli.query import run_local_search, run_global_search
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- FastAPI 應用程式初始化 ---
app = FastAPI(
    title="GraphRAG API",
    description="GraphRAG 索引和查詢管道的 API 介面",
)

# --- 專案目錄設定 ---
API_PROJECTS_DIR = Path("./api_projects")
API_PROJECTS_DIR.mkdir(exist_ok=True)

# --- API 請求的 Pydantic 模型 ---
class CreateProjectRequest(BaseModel):
    """創建專案的請求模型

    預設行為說明：
    - 如果未提供 `api_key`，會從環境變數 `GRAPHRAG_API_KEY` 讀取
    - 如果 `llm` 為 'azure' 且未提供 Azure 相關設定，會從 AZURE_* 環境變數讀取
    - `text_content` 預設為空字串，允許不提供文本內容
    """
    text_content: str = Field("", description="要索引的文本內容。空值表示不建立輸入檔案。", example="")
    api_key: Optional[str] = Field(None, description="LLM 的 API 金鑰。如未提供則從 GRAPHRAG_API_KEY 環境變數讀取。", example="")
    llm: str = Field("openai", description="LLM 提供者 ('openai' 或 'azure')。")
    # Azure 特定欄位（選填；可從環境變數讀取）
    azure_api_base: Optional[str] = Field(None, description="Azure API 基礎 URL 或端點", example="")
    azure_api_version: Optional[str] = Field(None, description="Azure API 版本", example="")
    azure_deployment_name: Optional[str] = Field(None, description="Azure 部署名稱", example="")

    @root_validator(pre=True)
    def fill_defaults_from_env(cls, values):
        """如果特定值未提供，嘗試從環境變數填入"""

        # 如果請求中未提供 api_key，從環境變數讀取
        if not values.get("api_key"):
            env_key = os.getenv("GRAPHRAG_API_KEY")
            if env_key:
                values["api_key"] = env_key
            else:
                raise ValueError("API key 必須在請求中提供或設定在環境變數 GRAPHRAG_API_KEY 中")

        # 如果使用 Azure，嘗試從環境變數填入 Azure 設定
        llm_val = values.get("llm") or "openai"
        if llm_val == "azure":
            azure_api_base = os.getenv("AZURE_API_BASE")
            azure_api_version = os.getenv("AZURE_API_VERSION")
            azure_deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")
            
            if not all([azure_api_base, azure_api_version, azure_deployment_name]):
                raise ValueError("使用 Azure 時必須提供所有 Azure 設定或在環境變數中設定")
                
            values.setdefault("azure_api_base", azure_api_base)
            values.setdefault("azure_api_version", azure_api_version)
            values.setdefault("azure_deployment_name", azure_deployment_name)

        return values


class QueryRequest(BaseModel):
    query: str
    method: str = Field("global", description="預設查詢方法為 'global'", example="global")


class IndexingConfig(BaseModel):
    """索引過程的配置"""
    method: str = Field("standard", description="要使用的索引方法")
    memory_profile: bool = Field(False, description="啟用記憶體分析")
    dry_run: bool = Field(False, description="執行乾跑測試而不實際執行")
    output_dir: Optional[str] = Field(None, description="覆寫設定檔中的輸出目錄路徑")
    verbose: bool = Field(True, description="啟用詳細日誌輸出")


# --- API Endpoints ---

@app.post("/create_project", status_code=201)
async def create_project(request: CreateProjectRequest):
    """
    建立新的 GraphRAG 專案。
    - 產生唯一的專案 ID
    - 建立專案目錄結構
    - 將提供的文本內容寫入輸入檔案
    - 初始化 GraphRAG 設定
    - 設置 API 金鑰
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
        initialize_project_at(path=str(project_path), force=True) #舊版本加上", force=True"

        # 4. Configure API Key and LLM settings
        (project_path / ".env").write_text(f"GRAPHRAG_API_KEY={request.api_key}")
        
        # 不使用完整的函式庫來更新 YAML 的簡單方法
        settings_path = project_path / "settings.yaml"
        with open(settings_path, "r") as f:
            settings = f.read()

        if request.llm == "azure":
            # 這是一個簡化的更新。更穩健的解決方案應該使用 YAML 函式庫
            azure_config = f'''
type: azure_openai_chat
api_base: {request.azure_api_base}
api_version: {request.azure_api_version}
deployment_name: {request.azure_deployment_name}
'''
            # 替換預設的聊天模型設定
            # 這個正則表達式很基本，可能需要根據不同的設定檔案進行調整
            import re
            settings = re.sub(r"llm:\n  type: openai_chat", "llm:\n" + azure_config, settings, flags=re.MULTILINE)
            
        with open(settings_path, "w") as f:
            f.write(settings)

        return {"project_id": project_id, "message": "Project created successfully."}
    except Exception as e:
        # 如果專案建立失敗，清理資源
        if project_path.exists():
            shutil.rmtree(project_path)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@app.post("/index/{project_id}")
async def run_indexing(project_id: str, config: IndexingConfig = IndexingConfig()):
    """
    執行指定專案 ID 的索引管道。
    """
    project_path = API_PROJECTS_DIR / project_id
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        # 1. 準備覆寫參數
        # 模仿 index_cli 的行為，將 API 參數轉換為設定覆寫
        cli_overrides = {}
        if config.output_dir:
            cli_overrides["output.base_dir"] = config.output_dir

        # 2. 使用官方提供的 `load_config` 函式載入設定
        graphrag_config = load_config(project_path, cli_overrides)

        # 3. 若請求為 dry_run，僅需確認設定能成功載入即為有效。
        if config.dry_run:
            return {
                "project_id": project_id,
                "message": "Dry run validation successful. Configuration is valid.",
            }

        # 4. 呼叫非同步的 build_index 函式來執行索引管道。
        await build_index(
            config=graphrag_config,
            method=IndexingMethod(config.method),
            memory_profile=config.memory_profile,
            verbose=config.verbose,
        )
        return {"project_id": project_id, "message": "Indexing process completed successfully."}

    except Exception as e:
        logging.error(f"Indexing failed for project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.post("/query/{project_id}")
async def run_query(project_id: str, request: QueryRequest):
    """
    對已索引的專案執行查詢。
    """
    project_path = API_PROJECTS_DIR / project_id
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found.")
    
    # The output directory is needed for the query
    output_path = project_path / "output"
    if not output_path.exists():
        raise HTTPException(status_code=400, detail="Project has not been indexed yet.")

    try:
        # 查詢函數是非同步的，但 CLI 封裝是同步的
        # 為了安全起見，我們在執行器中運行它們
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
                data_dir=None, # 使用根目錄的預設值
                config_filepath=None,
                community_level=2, # 來自 CLI 的預設值
                dynamic_community_selection=True,
                response_type="Multiple Paragraphs", # Default value
                streaming=False, # Return the full response
                query=request.query,
                verbose=False,
            ),
        )
        
        # 回應物件可能無法直接序列化為 JSON
        # 根據程式碼，它似乎是字串類型
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
    直接將文字檔案上傳到專案的輸入目錄。
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
            # 確保檔案名稱安全且唯一
            file_name = f"{uuid.uuid4()}_{file.filename}"
            file_path = input_path / file_name
            
            # 將內容寫入檔案
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
    刪除 GraphRAG 專案及其所有相關資料。
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
    列出所有現有的 GraphRAG 專案 ID。
    """
    projects = [d.name for d in API_PROJECTS_DIR.iterdir() if d.is_dir()]
    return {"projects": projects}


if __name__ == "__main__":
    print("正在啟動 GraphRAG API 伺服器...")
    print("可在 http://127.0.0.1:8000/docs 存取互動式文件")
    uvicorn.run(app, host="127.0.0.1", port=8000)