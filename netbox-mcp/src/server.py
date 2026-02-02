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

@mcp.tool()
def list_prefixes() -> str:
    """List all IP prefixes/subnets in NetBox with utilization info."""
    logger.info("list_prefixes called")
    try:
        logger.debug("Fetching prefixes from NetBox...")
        prefixes = nb.ipam.prefixes.all()
        result = []
        for prefix in prefixes:
            # Get IP count in this prefix
            try:
                ip_count = nb.ipam.ip_addresses.count(parent=str(prefix.prefix))
            except:
                ip_count = 0
            
            # Safely get site attribute
            site_name = ""
            try:
                if hasattr(prefix, 'site') and prefix.site:
                    site_name = str(prefix.site)
            except:
                pass
                
            result.append({
                "prefix": str(prefix.prefix),
                "description": prefix.description or "",
                "status": str(prefix.status) if prefix.status else "unknown",
                "site": site_name,
                "ip_count": ip_count
            })
        logger.info(f"Found {len(result)} prefixes")
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error in list_prefixes: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_prefix(prefix: str) -> str:
    """Get details of a specific IP prefix/subnet."""
    try:
        p = nb.ipam.prefixes.get(prefix=prefix)
        if p:
            try:
                ip_count = nb.ipam.ip_addresses.count(parent=str(p.prefix))
            except:
                ip_count = 0
            
            site_name = ""
            try:
                if hasattr(p, 'site') and p.site:
                    site_name = str(p.site)
            except:
                pass
                
            return json.dumps({
                "prefix": str(p.prefix),
                "description": p.description or "",
                "status": str(p.status) if p.status else "unknown",
                "site": site_name,
                "ip_count": ip_count
            })
        return "Prefix not found."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def list_vlans() -> str:
    """List all VLANs in NetBox."""
    logger.info("list_vlans called")
    try:
        logger.debug("Fetching VLANs from NetBox...")
        vlans = nb.ipam.vlans.all()
        result = []
        for vlan in vlans:
            result.append({
                "vid": vlan.vid,
                "name": vlan.name,
                "description": vlan.description or "",
                "status": str(vlan.status) if vlan.status else "unknown"
            })
        logger.info(f"Found {len(result)} VLANs")
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error in list_vlans: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def generate_topology() -> str:
    """Generate comprehensive network topology data for documentation and diagram generation.
    Returns devices grouped by role, network segments, and interconnection summary."""
    logger.info("generate_topology called")
    try:
        # Fetch all devices
        devices = nb.dcim.devices.all()
        devices_by_role = {}
        all_devices = []
        
        for device in devices:
            role_name = str(device.role) if device.role else "Unknown"
            if role_name not in devices_by_role:
                devices_by_role[role_name] = []
            
            device_info = {
                "name": device.name,
                "device_type": str(device.device_type) if device.device_type else "",
                "role": role_name,
                "site": str(device.site) if device.site else "",
                "status": str(device.status) if device.status else "unknown"
            }
            devices_by_role[role_name].append(device_info)
            all_devices.append(device_info)
        
        # Fetch all prefixes for network segments
        prefixes = nb.ipam.prefixes.all()
        network_segments = []
        for prefix in prefixes:
            try:
                ip_count = nb.ipam.ip_addresses.count(parent=str(prefix.prefix))
            except:
                ip_count = 0
            network_segments.append({
                "prefix": str(prefix.prefix),
                "description": prefix.description or "",
                "status": str(prefix.status) if prefix.status else "unknown",
                "ip_count": ip_count
            })
        
        # Fetch VLANs
        vlans = nb.ipam.vlans.all()
        vlan_list = []
        for vlan in vlans:
            vlan_list.append({
                "vid": vlan.vid,
                "name": vlan.name,
                "description": vlan.description or ""
            })
        
        # Build topology summary
        result = {
            "summary": {
                "total_devices": len(all_devices),
                "total_prefixes": len(network_segments),
                "total_vlans": len(vlan_list),
                "device_roles": list(devices_by_role.keys())
            },
            "devices_by_role": devices_by_role,
            "network_segments": network_segments,
            "vlans": vlan_list,
            "topology_layers": {
                "perimeter": [d for d in all_devices if "firewall" in d["role"].lower() and "perimeter" in d["name"].lower()],
                "core": [d for d in all_devices if "router" in d["role"].lower() or "core" in d["role"].lower()],
                "distribution": [d for d in all_devices if "distribution" in d["role"].lower()],
                "access": [d for d in all_devices if "access" in d["role"].lower()],
                "security": [d for d in all_devices if "firewall" in d["role"].lower() and "internal" in d["name"].lower()]
            }
        }
        
        # Generate Professional Mermaid diagram (clean syntax)
        mermaid_lines = [
            "```mermaid",
            "graph TB",
            "    %% Styling",
            "    classDef internet fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
            "    classDef firewall fill:#ffebee,stroke:#c62828,stroke-width:2px",
            "    classDef router fill:#fff3e0,stroke:#ef6c00,stroke-width:2px",
            "    classDef switch fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px",
            "    classDef network fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px",
            "",
            "    %% Internet Cloud",
            '    INET(("Internet"))',
            ""
        ]
        
        # Perimeter layer
        perimeter = result["topology_layers"]["perimeter"]
        if perimeter:
            mermaid_lines.append('    subgraph Perimeter["Perimeter Zone"]')
            mermaid_lines.append('        direction TB')
            for i, d in enumerate(perimeter):
                dt = d["device_type"].split()[-1] if d["device_type"] else ""
                mermaid_lines.append(f'        FW{i+1}[["{d["name"]}<br/>{dt}"]]')
            mermaid_lines.append('    end')
            mermaid_lines.append('    INET --> FW1')
        
        # Core layer
        core = result["topology_layers"]["core"]
        if core:
            mermaid_lines.append('')
            mermaid_lines.append('    subgraph Core["Core Layer"]')
            mermaid_lines.append('        direction LR')
            for i, d in enumerate(core):
                dt = d["device_type"].split()[-1] if d["device_type"] else ""
                mermaid_lines.append(f'        CR{i+1}[("{d["name"]}<br/>{dt}")]')
            mermaid_lines.append('    end')
        
        # Distribution layer
        dist = result["topology_layers"]["distribution"]
        if dist:
            mermaid_lines.append('')
            mermaid_lines.append('    subgraph Distribution["Distribution Layer"]')
            mermaid_lines.append('        direction LR')
            for i, d in enumerate(dist):
                dt = d["device_type"].split()[-1] if d["device_type"] else ""
                mermaid_lines.append(f'        DS{i+1}[["{d["name"]}<br/>{dt}"]]')
            mermaid_lines.append('    end')
        
        # Internal Security
        security = result["topology_layers"]["security"]
        if security:
            mermaid_lines.append('')
            mermaid_lines.append('    subgraph InternalSec["Internal Security"]')
            for i, d in enumerate(security):
                dt = d["device_type"].split()[-1] if d["device_type"] else ""
                mermaid_lines.append(f'        SEC{i+1}[["{d["name"]}<br/>{dt}"]]')
            mermaid_lines.append('    end')
        
        # Access layer
        access = result["topology_layers"]["access"]
        if access:
            mermaid_lines.append('')
            mermaid_lines.append('    subgraph Access["Access Layer"]')
            mermaid_lines.append('        direction LR')
            for i, d in enumerate(access):
                dt = d["device_type"].split()[-1] if d["device_type"] else ""
                mermaid_lines.append(f'        AS{i+1}["{d["name"]}<br/>{dt}"]')
            mermaid_lines.append('    end')
        
        # Network Segments
        segments = result["network_segments"]
        if segments:
            mermaid_lines.append('')
            mermaid_lines.append('    subgraph Networks["Network Segments"]')
            mermaid_lines.append('        direction LR')
            for i, seg in enumerate(segments):
                desc = seg["description"] or f"Segment {i+1}"
                mermaid_lines.append(f'        NET{i+1}["{seg["prefix"]}<br/>{desc}"]')
            mermaid_lines.append('    end')
        
        # Connections (clean syntax without pipe issues)
        mermaid_lines.append('')
        mermaid_lines.append('    %% Connections')
        
        if perimeter and core:
            for i in range(len(core)):
                mermaid_lines.append(f'    FW1 -- trunk --> CR{i+1}')
        
        if len(core) > 1:
            mermaid_lines.append('    CR1 <-- iBGP --> CR2')
        
        if core and dist:
            mermaid_lines.append('    CR1 -- L3 --> DS1')
            if len(core) > 1 and len(dist) > 1:
                mermaid_lines.append('    CR2 -- L3 --> DS2')
        
        if len(dist) > 1:
            mermaid_lines.append('    DS1 <-- vPC --> DS2')
        
        if dist and security:
            mermaid_lines.append('    DS1 --> SEC1')
            mermaid_lines.append('    DS2 --> SEC1')
        
        if security and access:
            for i in range(len(access)):
                mermaid_lines.append(f'    SEC1 --> AS{i+1}')
        elif dist and access:
            for i in range(len(access)):
                mermaid_lines.append(f'    DS1 --> AS{i+1}')
                if len(dist) > 1:
                    mermaid_lines.append(f'    DS2 --> AS{i+1}')
        
        if access and segments:
            for i in range(len(segments)):
                as_idx = i % len(access) + 1
                mermaid_lines.append(f'    AS{as_idx} -.-> NET{i+1}')
        
        # Apply styles
        mermaid_lines.append('')
        mermaid_lines.append('    %% Apply Styles')
        mermaid_lines.append('    class INET internet')
        if perimeter:
            mermaid_lines.append('    class FW1 firewall')
        if security:
            mermaid_lines.append('    class SEC1 firewall')
        if core:
            mermaid_lines.append('    class ' + ','.join([f'CR{i+1}' for i in range(len(core))]) + ' router')
        if dist:
            mermaid_lines.append('    class ' + ','.join([f'DS{i+1}' for i in range(len(dist))]) + ' switch')
        if access:
            mermaid_lines.append('    class ' + ','.join([f'AS{i+1}' for i in range(len(access))]) + ' switch')
        if segments:
            mermaid_lines.append('    class ' + ','.join([f'NET{i+1}' for i in range(len(segments))]) + ' network')
        
        mermaid_lines.append("```")
        
        result["mermaid_diagram"] = "\n".join(mermaid_lines)
        
        logger.info(f"Generated topology with {len(all_devices)} devices")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in generate_topology: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Run with SSE transport on port 8000, bind to all interfaces
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.run(transport="sse")
