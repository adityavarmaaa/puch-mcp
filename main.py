from typing import Annotated
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
import markdownify
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, TextContent
from pydantic import BaseModel
from pathlib import Path
import fitz  # PyMuPDF
from fastapi import FastAPI
import os
import uvicorn
import asyncio

# ✅ Token and phone number
TOKEN = "18d266806344"
MY_NUMBER = "919553332489"

class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None

class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(token=token, client_id="unknown", scopes=[], expires_at=None)
        return None

# ✅ MCP Setup
mcp = FastMCP("My MCP Server", auth=SimpleBearerAuthProvider(TOKEN))

# ✅ Resume tool
@mcp.tool(description=RichToolDescription(
    description="Serve your resume in plain markdown.",
    use_when="Puch (or anyone) asks for your resume.",
    side_effects=None,
).model_dump_json())
async def resume() -> str:
    try:
        pdf_path = Path("CV (4).pdf")
        if not pdf_path.exists():
            return "Resume file not found."

        doc = fitz.open(pdf_path)
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()

        markdown = markdownify.markdownify(full_text, heading_style="ATX")
        return markdown

    except Exception as e:
        return f"Error reading resume: {e}"

@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# ✅ FastAPI App for health check
app = FastAPI()

@app.get("/")
def root():
    return {"status": "Server is live. MCP is running!"}

@app.get("/mcp")
def mcp_health():
    return {"status": "OK"}

# ✅ Run both MCP and FastAPI on port 8080
async def start_all():
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8080)

if __name__ == "__main__":
    asyncio.run(start_all())
