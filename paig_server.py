from typing import Any
import random
import string
import re
import httpx
from mcp.server.fastmcp import FastMCP

# ---------- Initialize FastMCP server ----------
mcp = FastMCP("paig-governance-service")

# ---------- Constants ----------
PAIG_BASE_URL = "http://127.0.0.1:4545"  # Local PAIG server


# ---------- Login Helper ----------
async def get_session_cookie() -> str | None:
    """Login to PAIG and return a valid session cookie."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PAIG_BASE_URL}/account-service/api/login",
                json={"username": "admin", "password": "welcome1"},
            )
            response.raise_for_status()
            return response.cookies.get("PRIVACERAPAIGSESSION")
        except Exception as e:
            print("❌ Login failed:", e)
            return None


# ---------- Helper Function ----------
async def make_paig_request(
    method: str,
    endpoint: str,
    cookies: dict[str, str] = None,
    data: dict = None,
    params: dict = None,
) -> dict[str, Any] | None:
    """Make a request to the PAIG Governance API with session cookie automatically included."""
    cookie = await get_session_cookie()
    if not cookie:
        return {"error": "Login failed, no session cookie"}

    cookies = {"PRIVACERAPAIGSESSION": cookie}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method,
                f"{PAIG_BASE_URL}{endpoint}",
                cookies=cookies,
                json=data,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return {"json": response.json() if response.text.strip() else {}}
        except Exception as e:
            return {"error": str(e)}


# ---------- Tools for Applications ----------
@mcp.tool()
async def list_applications(page: int = 0, size: int = 10, status: str = None, name: str = None) -> str:
    """List AI applications with optional filters."""
    params = {"page": page, "size": size}
    if status:
        params["status"] = status
    if name:
        params["name"] = name

    result = await make_paig_request("GET", "/governance-service/api/ai/application", params=params)
    if "error" in result:
        return f"❌ Unable to fetch applications: {result['error']}"

    data = result["json"]
    if not data.get("content"):
        return "ℹ️ No applications found."

    apps = [f'App ID {idx}: {app}' for idx, app in enumerate(data["content"], start=1)]
    return "📂 Applications: " + "; ".join(apps)


@mcp.tool()
async def create_application(app_data: dict) -> str:
    """Create a new AI application."""
    result = await make_paig_request("POST", "/governance-service/api/ai/application", data=app_data)
    if "error" in result:
        return f"❌ Failed to create application: {result['error']}"
    return f'✅ Application "{app_data.get("name")}" created successfully.'


@mcp.tool()
async def update_application_guardrails(guardrail_data: dict) -> str:
    """Update application guardrails."""
    result = await make_paig_request("PUT", "/governance-service/api/ai/application/guardrails", data=guardrail_data)
    if "error" in result:
        return f"❌ Unable to update guardrails: {result['error']}"
    return "✅ Application guardrails updated successfully."


@mcp.tool()
async def get_application_by_id(app_id: str) -> str:
    """Fetch an application by its ID."""
    result = await make_paig_request("GET", f"/governance-service/api/ai/application/{app_id}")
    if "error" in result:
        return f"❌ Unable to fetch application {app_id}: {result['error']}"

    data = result["json"]
    return f'📂 Application {data.get("id")}: {data.get("name")} - {data.get("description", "No description")}'


@mcp.tool()
async def update_application(app_id: str, app_data: dict) -> str:
    """Update an application by ID."""
    result = await make_paig_request("PUT", f"/governance-service/api/ai/application/{app_id}", data=app_data)
    if "error" in result:
        return f"❌ Unable to update application {app_id}: {result['error']}"
    return f"✅ Application {app_id} updated successfully."


@mcp.tool()
async def delete_application(app_id: str) -> str:
    """Delete an application by ID."""
    result = await make_paig_request("DELETE", f"/governance-service/api/ai/application/{app_id}")
    if "error" in result:
        return f"❌ Unable to delete application {app_id}: {result['error']}"
    return f"🗑️ Application {app_id} deleted successfully."


@mcp.tool()
async def set_session_token(token: str) -> str:
    """Set the current PRIVACERAPAIGSESSION token at runtime."""
    global session_cookie
    session_cookie = token.strip()
    return "✅ Session token updated."


# ---------- Natural Language Command Processor ----------
@mcp.tool()
async def process_app_command(prompt: str) -> str:
    """
    Process natural language commands for AI Applications.
    Examples:
    - "List applications"
    - "Get application 42"
    - "Delete application 101"
    - "Create application named FraudDetector"
    - "Update application 42"
    """
    text = prompt.lower()

    if "list applications" in text:
        return await list_applications()

    match = re.search(r'get application (\d+)', text)
    if match:
        return await get_application_by_id(match.group(1))

    match = re.search(r'delete application (\d+)', text)
    if match:
        return await delete_application(match.group(1))

    match = re.search(r'create application named "?([\w\s]+)"?', text)
    if match:
        app_name = match.group(1)
        app_data = {"name": app_name, "description": f"App {app_name} created via NLP"}
        return await create_application(app_data)

    match = re.search(r'update application (\d+)', text)
    if match:
        return f"ℹ️ Use update_application tool with ID {match.group(1)} and provide new data."

    if "update guardrails" in text:
        return f"ℹ️ Use update_application_guardrails with correct guardrail data."

    return "❓ Sorry, I couldn't understand the command."


# ---------- Run MCP ----------
if __name__ == "__main__":
    mcp.run(transport="stdio")
