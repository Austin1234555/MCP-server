from typing import Any
import random
import string
import re
import httpx
from mcp.server.fastmcp import FastMCP

# ---------- Initialize FastMCP server ----------
mcp = FastMCP("paig-account-service")

# ---------- Constants ----------
PAIG_BASE_URL = "http://127.0.0.1:4545"  # Local PAIG server


# ---------- Helper Functions ----------
def generate_password(length: int = 12) -> str:
    """Generate a random strong password."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(characters) for _ in range(length))


async def make_paig_request(
    method: str,
    endpoint: str,
    cookies: dict[str, str] = None,
    data: dict = None,
    params: dict = None,
) -> dict[str, Any] | None:
    """Make a request to the PAIG API with proper error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method,
                f"{PAIG_BASE_URL}{endpoint}",
                cookies=cookies or {},
                json=data,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json() if response.text.strip() else {}
        except Exception as e:
            return {"error": str(e)}


# ---------- User Tools ----------
@mcp.tool()
async def create_user(session_token: str, user_data: dict) -> str:
    """Create a new user in PAIG and return natural language confirmation."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("POST", "/account-service/api/users", cookies, user_data)
    if "error" in data:
        return f"❌ Failed to create user: {data['error']}"
    return (
        f'✅ User "{user_data["firstName"]} {user_data["lastName"]}" created successfully '
        f'with role {user_data["roles"][0]}. Temporary password sent to {user_data["email"]}.'
    )


@mcp.tool()
async def get_all_users(session_token: str) -> str:
    """Fetch all users from PAIG and return them in natural language."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("GET", "/account-service/api/users", cookies)
    if "error" in data:
        return f"❌ Unable to fetch users: {data['error']}"
    if not data:
        return "ℹ️ No users found."

    users = [f'{u["firstName"]} {u["lastName"]} ({", ".join(u["roles"])})' for u in data]
    return "👥 Users: " + "; ".join(users)


@mcp.tool()
async def user_login(credentials: dict) -> str:
    """Login user and return natural language session info."""
    data = await make_paig_request("POST", "/account-service/api/login", data=credentials)
    if "error" in data:
        return f"❌ Login failed: {data['error']}"
    return f'✅ Login successful for user {credentials.get("username")}. Session token generated.'


@mcp.tool()
async def get_user_by_id(session_token: str, user_id: str) -> str:
    """Fetch user details by ID."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("GET", f"/account-service/api/users/{user_id}", cookies)
    if "error" in data:
        return f"❌ Unable to fetch user with ID {user_id}: {data['error']}"
    return (
        f'👤 User {data["firstName"]} {data["lastName"]} '
        f'has roles {", ".join(data["roles"])}.'
    )


@mcp.tool()
async def update_user(session_token: str, user_id: str, update_data: dict) -> str:
    """Update user details by ID."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("PUT", f"/account-service/api/users/{user_id}", cookies, update_data)
    if "error" in data:
        return f"❌ Unable to update user with ID {user_id}: {data['error']}"
    return f'✅ User with ID {user_id} updated successfully. Roles: {", ".join(update_data["roles"])}'


@mcp.tool()
async def delete_user(session_token: str, user_id: str) -> str:
    """Delete a user by ID."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("DELETE", f"/account-service/api/users/{user_id}", cookies)
    if "error" in data:
        return f"❌ Unable to delete user {user_id}: {data['error']}"
    return f"🗑️ User {user_id} deleted successfully."


@mcp.tool()
async def get_tenant_user(session_token: str) -> str:
    """Fetch tenant user information from PAIG."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("GET", "/account-service/api/users/tenant", cookies)
    if "error" in data:
        return f"❌ Unable to fetch tenant user data: {data['error']}"
    return f'👤 Tenant user: {data.get("firstName")} {data.get("lastName")}'


# ---------- Group Tools ----------
@mcp.tool()
async def get_groups(session_token: str, page: int = 0, size: int = 10) -> str:
    """Fetch groups with pagination."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    params = {"page": page, "size": size}
    data = await make_paig_request("GET", "/account-service/api/groups", cookies=cookies, params=params)
    if "error" in data:
        return f"❌ Unable to fetch groups: {data['error']}"
    if not data:
        return "ℹ️ No groups found."
    groups = [f'{g["name"]} (status: {g.get("status", "unknown")})' for g in data]
    return "👥 Groups: " + "; ".join(groups)


@mcp.tool()
async def create_group(session_token: str, group_data: dict) -> str:
    """Create a new group."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("POST", "/account-service/api/groups", cookies=cookies, data=group_data)
    if "error" in data:
        return f"❌ Failed to create group: {data['error']}"
    return f'✅ Group "{group_data.get("name")}" created successfully.'


@mcp.tool()
async def update_group(session_token: str, group_id: str, update_data: dict) -> str:
    """Update an existing group by ID."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("PUT", f"/account-service/api/groups/{group_id}", cookies=cookies, data=update_data)
    if "error" in data:
        return f"❌ Unable to update group {group_id}: {data['error']}"
    return f"✅ Group {group_id} updated successfully."


@mcp.tool()
async def delete_group(session_token: str, group_id: str) -> str:
    """Delete a group by ID."""
    cookies = {"PRIVACERAPAIGSESSION": session_token}
    data = await make_paig_request("DELETE", f"/account-service/api/groups/{group_id}", cookies=cookies)
    if "error" in data:
        return f"❌ Unable to delete group {group_id}: {data['error']}"
    return f"🗑️ Group {group_id} deleted successfully."


# ---------- Natural Language Command Processor ----------
@mcp.tool()
async def process_command(session_token: str, prompt: str) -> str:
    """
    Accepts a natural language command and routes it to the correct action.
    Example: "Create user Dwayne Johnson with role USER"
    """
    text = prompt.lower()

    # Create user
    match = re.search(r'create user "?([\w\s]+)"? with role (\w+)', prompt, re.IGNORECASE)
    if match:
        full_name, role = match.groups()
        role = role.upper()

        first, last = (full_name.split(" ", 1) + ["Unknown"])[:2]
        username = f"{first.lower()}.{last.lower()}"
        password = generate_password()

        user_data = {
            "firstName": first,
            "lastName": last,
            "username": username,
            "password": password,
            "roles": [role],
            "email": f"{username}@example.com",
        }
        return await create_user(session_token, user_data)

    if "get all users" in text:
        return await get_all_users(session_token)

    if "delete user" in text:
        user_id = text.replace("delete user", "").strip()
        return await delete_user(session_token, user_id)

    match = re.search(r'update user (\d+) with role (\w+)', prompt, re.IGNORECASE)
    if match:
        user_id, role = match.groups()
        return await update_user(session_token, user_id, {"roles": [role.upper()]})

    return "❓ Sorry, I couldn't understand the command."


# ---------- Run MCP ----------
if __name__ == "__main__":
    mcp.run(transport="stdio")
