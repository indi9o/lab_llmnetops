#!/bin/bash
echo "Connecting to LLM Client..."
echo "Type 'quit' or 'exit' to stop the chat."
echo "Press Ctrl+P, Ctrl+Q to detach without stopping."
docker attach lab_llmnetops_1-llm-client-1
