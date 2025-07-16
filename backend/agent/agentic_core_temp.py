from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import Tool, StructuredTool
from datetime import date
import os


from api.tools import (
    get_leave_balance,
    apply_for_leave,
    check_leave_status,
    LeaveBalanceInput,
    ApplyLeaveInput,
    CheckStatusInput,
)

def setup_agent():
    llm = ChatOpenAI(
        model=os.environ.get("OPENROUTER_MODEL"),
        openai_api_base=os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
        openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
        temperature=0.0,
        streaming=False,
    )

    tools = [
        StructuredTool.from_function(
            name="get_leave_balance",
            func=get_leave_balance,
            description="Fetch available leave balances (casual, sick, earned) for a user using their user ID.",
            args_schema=LeaveBalanceInput,
            return_direct=True
        ),
        StructuredTool.from_function(
            name="apply_for_leave",
            func=apply_for_leave,
            description="Apply for a leave by specifying user ID, leave type, number of days, start date, and reason.",
            args_schema=ApplyLeaveInput,
            return_direct=True
        ),
        StructuredTool.from_function(
            name="check_leave_status",
            func=check_leave_status,
            description="Check the leave request history and status for a user using their user ID.",
            args_schema=CheckStatusInput,
            return_direct=True
        )
    ]

    today = date.today().isoformat()
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""
            You are a tool-using agent for leave management. You MUST always call one of the available tools to respond to the user query.

            **Important Rules:**
            1. You will receive a user query like: "User 'user002' requested the following: 'Get my current leave balance.'"
            2. Parse the user_id and query from this input string.
            3. Decide which of the provided tools is best suited to fulfill the request.
            4. You MUST call the tool and return only its direct output.
            5. NEVER generate responses on your own. Only return what the tool provides.

            Today is {today}.
        """),
        ("human", "User ID: {user_id}\nQuery: {query}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )

    print("###########    LangChain agent initialized.    ###########")
    return agent_executor

