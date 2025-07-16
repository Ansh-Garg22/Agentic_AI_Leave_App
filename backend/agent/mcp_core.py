import os
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp import MCPToolkit
import asyncio

from api.mcp_tool import read_json_db, USERS_DB_PATH

load_dotenv()


async def setup_agent():
    llm = ChatOpenAI(
        model=os.environ.get("OPENROUTER_MODEL"),
        openai_api_base=os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
        openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
        temperature=0.0,
        streaming=False,
    )

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_tool.py"]
    )

    async with stdio_client(server_params) as (reader, writer):
        mcp_toolkit = await MCPToolkit.from_client(reader, writer)
        tools = mcp_toolkit.get_tools()

    today = date.today().isoformat()

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""
            You are a highly capable leave management assistant. Today is {today}.
            You MUST use the provided tools to answer the user's query and ALWAYS return the direct output of the tool.

            **CRITICAL RULES:**
            1. You will be given a `user_id`, the user's `role` ('employee' or 'manager'), and a `query`.
            2. You MUST respect the user's role. Employee tools are for everyone. Manager tools are ONLY for users with the 'manager' role.
            3. If a non-manager tries to use a manager tool, you must refuse and explain why. However, the tools have built-in checks, so you should prefer calling the tool and letting it return the access error.
            4. Parse the user's query to determine the correct tool and its parameters.
            5. IMPORTANT **For managers**, when they want to see pending requests, use `get_all_pending_requests`. When they want to approve or reject, you MUST extract the `request_id` and the `action` ('approved' or 'rejected') from the query and use the `manage_leave_request` tool. The manager's own `user_id` must be passed as `manager_id`.

            **Example Manager Query:**
            - "Approve request req_123456" -> Call `manage_leave_request` with `manager_id`=<manager's_id>, `request_id`='req_123456', `action`='approved'.
            - "Show me who needs leave approval" -> Call `get_all_pending_requests` with `manager_id`=<manager's_id>.
        """),
        ("human", "User ID: {user_id}\nUser Role: {role}\nQuery: {query}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )

    print("########### LangChain agent with MCP tools initialized. ###########")
    return agent_executor
