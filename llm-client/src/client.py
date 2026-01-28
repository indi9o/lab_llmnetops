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
You have access to the following tools to query NetBox:
- list_sites: Lists all sites in NetBox
- get_device: Gets details of a specific device by name
- get_ip_address: Gets details of a specific IP address (requires exact address like "10.0.0.1")
- list_ip_addresses: Lists all IP addresses in NetBox

When the user asks to LIST or show ALL IP addresses, use list_ip_addresses.
When the user asks about a SPECIFIC IP address, use get_ip_address with the exact address.
When the user asks about sites or devices, use the appropriate tool.

You MUST use the appropriate tool to get the information from NetBox.
Do NOT make up information - always use the tools to get real data."""

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
                print(f"Assistant: {message['content']}")

        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    try:
        run_chat_loop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
