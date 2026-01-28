import pynetbox
import os

# Configuration
NETBOX_URL = "http://localhost:38080"
NETBOX_TOKEN = "MK7knYb9991ZScuKIeACcsVCVifdBvbhIR4wzaaw"

nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

def create_if_not_exists(endpoint, **kwargs):
    try:
        # Check if exists
        search_kwargs = {k: v for k, v in kwargs.items() if k in ['name', 'slug', 'model']}
        if 'slug' not in search_kwargs and 'name' in kwargs:
             search_kwargs['slug'] = kwargs['name'].lower().replace(' ', '-')
        
        existing = endpoint.get(**search_kwargs)
        if existing:
            print(f"Skipping {kwargs.get('name', 'item')}: Already exists")
            return existing
        
        # Create
        created = endpoint.create(kwargs)
        print(f"Created {kwargs.get('name', 'item')}: {created}")
        return created
    except Exception as e:
        print(f"Error creating {kwargs.get('name', 'item')}: {e}")
        return None

def main():
    print("Starting NetBox population...")

    # 1. Site
    site = create_if_not_exists(nb.dcim.sites, name="Data Center A", slug="dc-a", status="active")

    # 2. Manufacturer
    cisco = create_if_not_exists(nb.dcim.manufacturers, name="Cisco", slug="cisco")
    juniper = create_if_not_exists(nb.dcim.manufacturers, name="Juniper", slug="juniper")

    # 3. Device Types
    if cisco:
        create_if_not_exists(nb.dcim.device_types, manufacturer=cisco.id, model="CSR1000v", slug="csr1000v", u_height=1)
    if juniper:
        create_if_not_exists(nb.dcim.device_types, manufacturer=juniper.id, model="vSRX", slug="vsrx", u_height=1)

    # 4. Device Roles
    role_core = create_if_not_exists(nb.dcim.device_roles, name="Core Router", slug="core-router", color="ff0000")
    role_access = create_if_not_exists(nb.dcim.device_roles, name="Access Switch", slug="access-switch", color="00ff00")

    # 5. Devices
    # Need to fetch IDs again to be sure
    dt_csr = nb.dcim.device_types.get(slug="csr1000v")
    role_core = nb.dcim.device_roles.get(slug="core-router")
    site_dc_a = nb.dcim.sites.get(slug="dc-a")

    if dt_csr and role_core and site_dc_a:
        create_if_not_exists(nb.dcim.devices, 
                             name="core-rtr-01", 
                             device_type=dt_csr.id, 
                             role=role_core.id, 
                             site=site_dc_a.id,
                             status="active")

    # 6. IP Prefixes (IPAM)
    print("\n--- Adding IPAM Data ---")
    
    # Create prefixes first
    prefixes = [
        {"prefix": "10.0.0.0/24", "site": site_dc_a.id if site_dc_a else None, "status": "active", "description": "Management Network"},
        {"prefix": "192.168.1.0/24", "site": site_dc_a.id if site_dc_a else None, "status": "active", "description": "User Network"},
        {"prefix": "172.16.0.0/24", "site": site_dc_a.id if site_dc_a else None, "status": "active", "description": "Server Network"},
    ]
    
    for prefix_data in prefixes:
        try:
            existing = nb.ipam.prefixes.get(prefix=prefix_data["prefix"])
            if existing:
                print(f"Skipping prefix {prefix_data['prefix']}: Already exists")
            else:
                created = nb.ipam.prefixes.create(prefix_data)
                print(f"Created prefix: {prefix_data['prefix']}")
        except Exception as e:
            print(f"Error creating prefix {prefix_data['prefix']}: {e}")

    # 7. IP Addresses
    device = nb.dcim.devices.get(name="core-rtr-01")
    
    ip_addresses = [
        {"address": "10.0.0.1/24", "status": "active", "description": "Gateway Management"},
        {"address": "10.0.0.2/24", "status": "active", "description": "Switch-01 Management"},
        {"address": "10.0.0.3/24", "status": "active", "description": "Switch-02 Management"},
        {"address": "192.168.1.1/24", "status": "active", "description": "Gateway User Network"},
        {"address": "192.168.1.100/24", "status": "active", "description": "Workstation-01"},
        {"address": "192.168.1.101/24", "status": "active", "description": "Workstation-02"},
        {"address": "172.16.0.1/24", "status": "active", "description": "Gateway Server Network"},
        {"address": "172.16.0.10/24", "status": "active", "description": "Web Server"},
        {"address": "172.16.0.11/24", "status": "active", "description": "Database Server"},
        {"address": "172.16.0.12/24", "status": "active", "description": "Application Server"},
    ]
    
    for ip_data in ip_addresses:
        try:
            existing = nb.ipam.ip_addresses.get(address=ip_data["address"])
            if existing:
                print(f"Skipping IP {ip_data['address']}: Already exists")
            else:
                created = nb.ipam.ip_addresses.create(ip_data)
                print(f"Created IP: {ip_data['address']} - {ip_data['description']}")
        except Exception as e:
            print(f"Error creating IP {ip_data['address']}: {e}")

    print("\nPopulation complete.")

if __name__ == "__main__":
    main()
