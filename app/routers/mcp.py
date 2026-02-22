from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.mcp.tools import MCPTools

router = APIRouter()
mcp_tools = MCPTools()


class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: dict


class MCPToolsResponse(BaseModel):
    tools: list[dict]


@router.get("/tools", response_model=MCPToolsResponse)
async def list_tools():
    return {"tools": mcp_tools.list_tools()}


@router.post("/call")
async def call_tool(request: ToolCallRequest):
    try:
        result = await mcp_tools.execute_tool(request.tool_name, request.parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
