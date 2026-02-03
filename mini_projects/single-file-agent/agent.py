import os
import json
from openai import OpenAI
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

import logging
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)


MODEL = "gpt-5-nano"


class Tool(BaseModel):
    name: str = Field("Name of the tool")
    description: str = Field("A quick description of what the tool is, and what it does?")
    input_schema: Dict[str, Any] = Field("The schema of the input that the tool requires to operate")


class AIAgent:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.messages: List[Dict[str, Any]] = []
        self.messages.append(
            {
                "role": "system",
                "content": "You are a helpful coding assistant operating in a terminal environment. Output only plain text without markdown formatting, as your responses appear directly in the terminal. Be concise but thorough, providing clear and practical advice with a friendly tone. Don't use any asterisk characters in your responses."
            }
        )
        self.tools: List[Tool] = []
        self._setup_tools()
        print("Agent initialized.")
        print("Number of tools: ", len(self.tools))

    def _setup_tools(self):
        self.tools = [
            Tool(
                name="read_file",
                description="Read the content of file at the specified path",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path of the file to read",
                        },
                    },
                    "required": ["path"],
                }
            ),
            Tool(
                name="list_files",
                description="List all the files and directories in the specified path",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path of the directory whose files to list (default is current directory with value '.')",
                        },
                    },
                    "required": [],
                }
            ),
            Tool(
                name="edit_file",
                description="Edit the content of file at the specified path by replacing old_text with new_text. Creates the file if it doesn't exists",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path of the file to edit",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "The text to search for and replace (new file will be created if it's empty)",
                        },
                        "new_text": {
                            "type": "string",
                            "description": "The text to replace old_text with",
                        }
                    },
                    "required": ["new_text"],
                }
            )
        ]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:

        logging.info(f"Executing tool: {tool_name} with input: {tool_input}")
        try:
            if tool_name == "read_file":
                return self._read_file(path=tool_input["path"])
            elif tool_name == "list_files":
                return self._list_files(path=tool_input.get("path", "."))
            elif tool_name == "edit_file":
                return self._edit_file(
                    path=tool_input["path"],
                    old_text=tool_input.get("old_text", ""),
                    new_text=tool_input["new_text"]
                )
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def _read_file(self, path: str) -> str:
        try:
            with open(path, "r") as f:
                content = f.read()

            return f"File content of {path}: \n{content}"
        except FileNotFoundError:
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _list_files(self, path: str) -> str:
        try:
            if not (os.path.exists(path)) or not (os.path.isdir(path)):
                return f"[Error] Directory does not exist or is not a directory: {path}"

            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"[DIR] {item}/")
                    # items.extend(list_files(item_path))
                else:
                    items.append(f"[FILE] {item}")
            if len(items) == 0:
                return f"Empty directory: {path}"

            return f"Content of {path}:\n{'\n'.join(items)}"

        except Exception as e:
            return f"Error listing files: {str(e)}"

    def _edit_file(self, path: str, old_text: str, new_text: str) -> str:
        try:
            if os.path.exists(path) and old_text:
                with open(path, "r") as f:
                    content = f.read()

                if old_text not in content:
                    return f"Text not found in {path}: \n'{old_text}'"

                content = content.replace(old_text, new_text)

                with open(path, "w") as f:
                    f.write(content)

                return f"Text updated successfully: {path}"

            else:
                dir_name = os.path.dirname(path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)

                with open(path, "w") as f:
                    f.write(new_text)

                return f"Successfully created: {path}"

        except Exception as e:
            return f"Error editing file: {str(e)}"

    def chat(self, user_input: str) -> str:
        logging.info(f"User input: {user_input}")

        self.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                    "strict": True,
                }
            }
            for tool in self.tools
        ]

        while True:
            try:
                completion = self.client.chat.completions.create(
                    model=MODEL,
                    messages=self.messages,
                    tools=tool_schemas
                )

                response = completion.choices[0].message
                self.messages.append(response)

                # assistant_messages = {
                #     "role": "assistant",
                #     "content": [],
                # }
                logging.info(f"LLM Response: \n{response}")
                if not response.tool_calls:
                    return response.content

                for tool_call in response.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    tool_call_id = tool_call.id

                    result = self._execute_tool(tool_name=name, tool_input=args)
                    logging.info(f"Tool Result: \n{result[:500]}\n...")

                    # Feed tool result back to the LLM
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(result)
                    })
            except Exception as e:
                return f"[Error]: {str(e)}"


if __name__ == "__main__":
    agent = AIAgent(os.getenv("OPENAI_API_KEY"))

    print("AI Code Assistant")
    print("================")
    print("A conversational AI agent that can read, list, and edit files.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            print("\nAssistant: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print()

