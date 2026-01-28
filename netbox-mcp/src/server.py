import os
import pynetbox
from mcp.server.fastmcp import FastMCP

# Configuration
NETBOX_URL = os.getenv("NETBOX_URL", "http://netbox:8080")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN", "1234567890123456789012345678901234567890")

# Initialize FastMCP with SSE settings
mcp = FastMCP("netbox-mcp")
nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

@mcp.tool()
def get_device(name: str) -> str:
    """Get device details by name."""
    try:
        device = nb.dcim.devices.get(name=name)
        if device:
            return str(dict(device))
        return "Device not found."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def list_sites() -> str:
    """List all sites."""
    try:
        sites = nb.dcim.sites.all()
        return str([site.name for site in sites])
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_ip_address(address: str) -> str:
    """Get IP address details."""
    try:
        ip = nb.ipam.ip_addresses.get(address=address)
        if ip:
            return str(dict(ip))
        return "IP Address not found."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def list_ip_addresses() -> str:
    """List all IP addresses in NetBox."""
    try:
        ips = nb.ipam.ip_addresses.all()
        result = []
        for ip in ips:
            result.append({
                "address": str(ip.address),
                "description": ip.description or "",
                "status": str(ip.status) if ip.status else "unknown"
            })
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Run with SSE transport on port 8000, bind to all interfaces
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.run(transport="sse")
