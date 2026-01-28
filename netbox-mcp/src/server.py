import os
import json
import logging
import pynetbox
from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
def list_devices() -> str:
    """List all devices in NetBox."""
    logger.info("list_devices called")
    try:
        logger.debug("Fetching devices from NetBox...")
        devices = nb.dcim.devices.all()
        result = []
        for device in devices:
            result.append({
                "name": device.name,
                "device_type": str(device.device_type) if device.device_type else "",
                "role": str(device.role) if device.role else "",
                "site": str(device.site) if device.site else "",
                "status": str(device.status) if device.status else "unknown"
            })
        logger.info(f"Found {len(result)} devices")
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error in list_devices: {e}")
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
    logger.info("list_ip_addresses called")
    try:
        logger.debug("Fetching IP addresses from NetBox...")
        ips = nb.ipam.ip_addresses.all()
        result = []
        for ip in ips:
            result.append({
                "address": str(ip.address),
                "description": ip.description or "",
                "status": str(ip.status) if ip.status else "unknown"
            })
        logger.info(f"Found {len(result)} IP addresses")
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error in list_ip_addresses: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Run with SSE transport on port 8000, bind to all interfaces
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.run(transport="sse")
