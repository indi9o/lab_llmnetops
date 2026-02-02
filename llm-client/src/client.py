import asyncio
import os
import sys
import ollama
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://netbox-mcp:8000/sse")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")

async def get_available_tools():
    """Connect to MCP and get available tools."""
    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            return tools.tools

async def call_mcp_tool(function_name: str, arguments: dict):
    """Connect to MCP and execute a tool."""
    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(function_name, arguments)
            return result

def run_chat_loop():
    print(f"Connecting to MCP Server at {MCP_SERVER_URL}...", flush=True)
    
    # Get available tools
    try:
        tools = asyncio.run(get_available_tools())
        print(f"Connected! Available tools: {[t.name for t in tools]}", flush=True)
    except Exception as e:
        print(f"Failed to connect to MCP Server: {e}")
        return
    
    # Prepare tools for Ollama
    ollama_tools = []
    for tool in tools:
        ollama_tools.append({
            'type': 'function',
            'function': {
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.inputSchema
            }
        })

    # Setup Ollama client
    client = ollama.Client(host=OLLAMA_HOST)
    
    # Memory with system prompt
    system_prompt = """You are a network operations assistant with access to NetBox, a network infrastructure management tool.

AVAILABLE TOOLS:
- list_sites: Lists all sites in NetBox
- list_devices: Lists all devices in NetBox
- get_device: Gets details of a specific device by name
- get_ip_address: Gets details of a specific IP address (requires exact address like "10.0.0.1")
- list_ip_addresses: Lists all IP addresses in NetBox
- list_prefixes: Lists all IP prefixes/subnets with utilization info
- get_prefix: Gets details of a specific prefix (e.g., "10.0.0.0/24")
- list_vlans: Lists all VLANs in NetBox
- generate_topology: Generates comprehensive network topology data including devices by role, network segments, VLANs, and layer groupings for documentation and diagram generation

TOOL USAGE RULES:
- When the user asks to LIST or show ALL devices, use list_devices.
- When the user asks about a SPECIFIC device by name, use get_device with the device name.
- When the user asks to LIST or show ALL IP addresses, use list_ip_addresses.
- When the user asks about a SPECIFIC IP address, use get_ip_address with the exact address.
- When the user asks about sites, use list_sites.
- When the user asks about subnets, prefixes, or network segments, use list_prefixes or get_prefix.
- When the user asks about VLANs, use list_vlans.
- When the user asks for COMPLETE documentation, topology diagram, or network architecture, use generate_topology to get all data at once.

TOPOLOGY DIAGRAM GENERATION - MANDATORY:
When the user asks for topology diagram or documentation, you MUST include a Mermaid diagram in your response.
Use this EXACT format based on the topology_layers from generate_topology output:

```mermaid
graph TB
    subgraph Perimeter["🔒 Perimeter Layer"]
        FW1[fw-perimeter-01<br/>ASA 5506-X]
    end
    
    subgraph Core["🏢 Core Layer"]
        CR1[core-rtr-01<br/>CSR1000v]
        CR2[core-rtr-02<br/>CSR1000v]
    end
    
    subgraph Distribution["📡 Distribution Layer"]
        DS1[dist-sw-01<br/>Catalyst 9300]
        DS2[dist-sw-02<br/>Catalyst 9300]
    end
    
    subgraph Access["💻 Access Layer"]
        AS1[access-sw-01<br/>EX4300]
        AS2[access-sw-02<br/>EX4300]
        AS3[access-sw-03<br/>EX4300]
    end
    
    FW1 --> CR1 & CR2
    CR1 <--> CR2
    CR1 --> DS1
    CR2 --> DS2
    DS1 <--> DS2
    DS1 & DS2 --> AS1 & AS2 & AS3
```

ALWAYS include the Mermaid code block with ```mermaid when generating topology documentation.

STRICT RULES - YOU MUST FOLLOW THESE:
1. ALWAYS use the appropriate tool to get information from NetBox. NEVER answer without querying NetBox first.
2. ONLY state facts that are directly returned from NetBox tools. Do NOT add, infer, or embellish any information.
3. If the tool returns an error or no data, say "Data tidak ditemukan di NetBox" - do NOT guess or make up data.
4. Do NOT make assumptions about network topology, configurations, or relationships that are not explicitly in the data.
5. Present the data exactly as returned, formatted clearly for the user.
6. If asked about something not available in NetBox tools, clearly state "Informasi tersebut tidak tersedia melalui tools yang ada."

RESPONSE FORMAT:
- Always respond in Bahasa Indonesia (Indonesian language).
- Be concise and factual.
- When generating documentation, include: diagram, penjelasan arsitektur, tabel network segmentation, dan device inventory.
- List data in a clear, structured format when appropriate."""

    messages = [{'role': 'system', 'content': system_prompt}]
    print("\n--- Start Chatting (type 'quit' to exit) ---")

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ['quit', 'exit']:
                break
            
            messages.append({'role': 'user', 'content': user_input})
            
            # Call Ollama
            response = client.chat(
                model=MODEL_NAME,
                messages=messages,
                tools=ollama_tools,
            )
            
            # Check for tool calls
            message = response['message']
            messages.append(message)

            if message.get('tool_calls'):
                print("  (Calling NetBox...)")
                for tool_call in message['tool_calls']:
                    function_name = tool_call['function']['name']
                    arguments = tool_call['function']['arguments']
                    
                    # Execute tool on MCP (with fresh connection)
                    try:
                        result = asyncio.run(call_mcp_tool(function_name, arguments))
                        tool_result = str(result.content)
                    except Exception as e:
                        tool_result = f"Error calling tool: {e}"
                    
                    # Add result to history
                    messages.append({
                        'role': 'tool',
                        'content': tool_result,
                        'name': function_name
                    })
                
                # Get final response after tool execution
                final_response = client.chat(
                    model=MODEL_NAME,
                    messages=messages,
                )
                print(f"Assistant: {final_response['message']['content']}")
                messages.append(final_response['message'])
            else:
                # Fallback: Check if the response contains a JSON tool call
                content = message.get('content', '')
                import re
                json_match = re.search(r'\{["\']name["\']:\s*["\']([\w_]+)["\']', content, re.DOTALL)
                
                if json_match:
                    try:
                        function_name = json_match.group(1)
                        
                        # Try to extract parameters, but handle malformed JSON
                        import json as json_lib
                        arguments = {}
                        
                        # Try to parse valid JSON first
                        try:
                            json_str = re.search(r'\{.*\}', content, re.DOTALL)
                            if json_str:
                                # Clean up malformed values like "<nil>"
                                cleaned = re.sub(r':\s*"<nil>"', ': null', json_str.group())
                                cleaned = re.sub(r':\s*<nil>', ': null', cleaned)
                                tool_call_data = json_lib.loads(cleaned)
                                arguments = tool_call_data.get('parameters', {})
                        except:
                            pass
                        
                        # Remove None or invalid arguments
                        arguments = {k: v for k, v in arguments.items() if v is not None and v != "null"}
                        
                        print(f"  (Detected tool call: {function_name})")
                        print("  (Calling NetBox...)")
                        
                        # Execute tool
                        try:
                            result = asyncio.run(call_mcp_tool(function_name, arguments))
                            tool_result = str(result.content)
                        except Exception as e:
                            tool_result = f"Error calling tool: {e}"
                        
                        # Add to messages and get final response
                        messages.append({
                            'role': 'tool',
                            'content': tool_result,
                            'name': function_name
                        })
                        
                        final_response = client.chat(
                            model=MODEL_NAME,
                            messages=messages,
                        )
                        print(f"Assistant: {final_response['message']['content']}")
                        messages.append(final_response['message'])
                    except Exception as e:
                        print(f"Assistant: {content}")
                else:
                    print(f"Assistant: {content}")

        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    try:
        run_chat_loop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
