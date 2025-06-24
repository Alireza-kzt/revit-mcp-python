from typing import Dict, Any, Union
import base64
import httpx
from fastmcp import FastMCP, Image, Context

mcp = FastMCP("AI Design Revit Server")

REVIT_HOST = "localhost"
REVIT_PORT = 48884
BASE_URL = f"http://{REVIT_HOST}:{REVIT_PORT}/revit_mcp"

async def revit_get(endpoint: str, ctx: Context = None, **kwargs) -> Union[Dict, str]:
    return await _revit_call("GET", endpoint, ctx=ctx, **kwargs)

async def revit_post(endpoint: str, data: Dict[str, Any], ctx: Context = None, **kwargs) -> Union[Dict, str]:
    return await _revit_call("POST", endpoint, data=data, ctx=ctx, **kwargs)

async def revit_image(endpoint: str, ctx: Context = None) -> Union[Image, str]:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                image_bytes = base64.b64decode(data["image_data"])
                return Image(data=image_bytes, format="png")
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {e}"

async def _revit_call(method: str, endpoint: str, data: Dict | None = None, ctx: Context = None, timeout: float = 30.0, params: Dict | None = None) -> Union[Dict, str]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = await client.get(url, params=params)
            else:
                response = await client.post(url, json=data, headers={"Content-Type": "application/json"})
            return response.json() if response.status_code == 200 else f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {e}"

from tools import register_tools
register_tools(mcp, revit_get, revit_post, revit_image)

def run():
    mcp.run()
