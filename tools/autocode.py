# Step 1: Import necessary modules and classes
# Fill in any additional imports you might need
from typing import Annotated, Sequence, TypedDict
import functools
import operator
import os
import subprocess
from typing import Optional

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool
from langgraph.graph import StateGraph, END

from gitutils import clone_repo, switch_to_local_repo_path, checkout_source_branch, has_changes, generate_branch_name, create_branch_and_push, create_pull_request

ROOT_DIR = "./"
VALID_FILE_TYPES = {"py", "txt", "md", "cpp", "c", "java", "js", "html", "css", "ts", "json"}

# Step 2: Define tools
# Here, define any tools the agents might use. Example given:
tavily_tool = TavilySearchResults(max_results=5)

# This tool executes code locally, which can be unsafe. Use with caution:
python_repl_tool = PythonREPLTool()

# Step 3: Define the system prompt for the supervisor agent
# Customize the members list as needed.
members = ["Researcher", "Coder", "Reviewer", "QATester", "FileWriter", "CheckoutAgent", "PrAgent"]
system_prompt = (
    f"You are a supervisor tasked with managing a conversation between the"
    f" following workers:  {members}. Given the following user request,"
    f" respond with the worker to act next. Each worker will perform a"
    f" task and respond with their results and status. When finished,"
    f" respond with FINISH."
)

# Step 4: Define options for the supervisor to choose from
options = members + ["FINISH"]

# Step 5: Define the function for OpenAI function calling
# Define what the function should do and its parameters.
function_def = {
    "name": "route",
    "description": "Select the next role.",
    "parameters": {
        "title": "routeSchema",
        "type": "object",
        "properties": {
            "next": {
                "title": "Next",
                "anyOf": [
                    {"enum": options},
                ],
            }
        },
        "required": ["next"],
    },
}
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            f"system",
            f"Given the conversation above, who should act next?"
            f" Or should we FINISH? Select one of: {options}",
        ),
    ]
).partial(options=str(options), members=", ".join(members))

# Step 6: Define the prompt for the supervisor agent
# Customize the prompt if needed.

# Step 7: Initialize the language model
# Choose the model you need, e.g., "gpt-4o"
llm = ChatOpenAI(model="gpt-4o")

# Step 8: Create the supervisor chain
# Define how the supervisor chain will process messages.
supervisor_chain = (
    prompt
    | llm.bind_functions(functions=[function_def], function_call="route")
    | JsonOutputFunctionsParser()
)

# Step 9: Define a typed dictionary for agent state
# The agent state is the input to each node in the graph
class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str

# Step 10: Function to create an agent
# Fill in the system prompt and tools for each agent you need to create.
def create_agent(llm: ChatOpenAI, tools: list, system_prompt: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor

# Step 11: Function to create an agent node
# This function processes the state through the agent and returns the result.
def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

# Step 12: Create agents and their corresponding nodes
# Define the specific role and tools for each agent.
research_agent = create_agent(llm, [tavily_tool], "You are a web researcher.")
research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

review_agent = create_agent(llm, [tavily_tool],
                            """You are an senior developer. You excel at code reviews.
                            You give detailed and specific actionable feedback.
                            You aren't rude, but you don't worry about being polite either.
                            Instead you just communicate directly about technical matters.
                            """)
review_node = functools.partial(agent_node, agent=review_agent, name="Reviewer")

test_agent = create_agent(
    llm,
    [python_repl_tool],  # DANGER DANGER runs arbitrary Python code
    "You may generate safe python code to test functions and classes using unittest or pytest.",
)
test_node = functools.partial(agent_node, agent=test_agent, name="QATester")

code_agent = create_agent(
    llm,
    [python_repl_tool],  # ALSO DANGER DANGER
    "You may generate safe python code to analyze data with pandas and generate charts using matplotlib.",
)
code_node = functools.partial(agent_node, agent=code_agent, name="Coder")

@tool
def create_directory(directory: str) -> str:
    """
    Create a new writable directory with the given directory name if it does not exist.
    If the directory exists, it ensures the directory is writable.

    Parameters:
    directory (str): The name of the directory to create.

    Returns:
    str: Success or error message.
    """
    if ".." in directory:
        return f"Cannot make a directory with '..' in path"
    try:
        os.makedirs(directory, exist_ok=True)
        subprocess.run(["chmod", "u+w", directory], check=True)
        return f"Directory successfully '{directory}' created and set as writeable."
    except subprocess.CalledProcessError as e:
        return f"Failed to create or set writable directory '{directory}': {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


@tool
def find_file(filename: str, path: str) -> Optional[str]:
    """
    Recursively searches for a file in the given path.
    Returns string of full path to file, or None if file not found.
    """
    # TODO handle multiple matches
    for root, dirs, files in os.walk(path):
        if filename in files:
            return os.path.join(root, filename)
    return None


@tool
def create_file(filename: str, content: str = "", directory=""):
    """Creates a new file and content in the specified directory."""
    # Validate file type
    try:
        file_stem, file_type = filename.split(".")
        assert file_type in VALID_FILE_TYPES
    except:
        return f"Invalid filename {filename} - must end with a valid file type: {valid_file_types}"
    directory_path = os.path.join(ROOT_DIR, directory)
    file_path = os.path.join(directory_path, filename)
    if not os.path.exists(file_path):
        try:
            with open(file_path, "w")as file:
                file.write(content)
            print(f"File '{filename}' created successfully at: '{file_path}'.")
            return f"File '{filename}' created successfully at: '{file_path}'."
        except Exception as e:
            print(f"Failed to create file '{filename}' at: '{file_path}': {str(e)}")
            return f"Failed to create file '{filename}' at: '{file_path}': {str(e)}"
    else:
        print(f"File '{filename}' already exists at: '{file_path}'.")
        return f"File '{filename}' already exists at: '{file_path}'."


@tool
def update_file(filename: str, content: str, directory: str = ""):
    """Updates, appends, or modifies an existing file with new content."""
    if directory:
        file_path = os.path.join(ROOT_DIR, directory, filename)
    else:
        file_path = find_file(filename, ROOT_DIR)

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "a") as file:
                file.write(content)
            return f"File '{filename}' updated successfully at: '{file_path}'"
        except Exception as e:
            return f"Failed to update file '{filename}' at: '{file_path}' - {str(e)}"
    else:
        return f"File '{filename}' not found at: '{file_path}'"

write_agent = create_agent(
    llm,
    [create_directory, create_file, find_file, update_file],
    "Write the generated code to files.",
)
write_node = functools.partial(agent_node, agent=write_agent, name="FileWriter")

checkout_agent = create_agent(
    llm,
    [clone_repo, switch_to_local_repo_path, checkout_source_branch],
    "You're tasked with preparing the local git repository for other agents to work on it.",
)
checkout_node = functools.partial(agent_node, agent=checkout_agent, name="CheckoutAgent")

pr_agent = create_agent(
    llm,
    [has_changes, generate_branch_name, create_branch_and_push, create_pull_request],
    "You're tasked with checking if there are local changes, and if yes, prepare a pull request targetting main.",
)
pr_node = functools.partial(agent_node, agent=pr_agent, name="PrAgent")

# Step 13: Define the workflow using StateGraph
# Add nodes and their corresponding functions to the workflow.
workflow = StateGraph(AgentState)
workflow.add_node("Reviewer", review_node)
workflow.add_node("Researcher", research_node)
workflow.add_node("Coder", code_node)
workflow.add_node("QATester", test_node)
workflow.add_node("FileWriter", write_node)
workflow.add_node("CheckoutAgent", checkout_node)
workflow.add_node("PrAgent", pr_node)
workflow.add_node("supervisor", supervisor_chain)

# Step 14: Add edges to the workflow
# Ensure that all workers report back to the supervisor.
for member in members:
    workflow.add_edge(member, "supervisor")

# Step 15: Define conditional edges
# The supervisor determines the next step or finishes the process.
conditional_map = {k: k for k in members}
conditional_map["FINISH"] = END
workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)

# Step 16: Set the entry point
workflow.set_entry_point("CheckoutAgent")

# Step 17: Compile the workflow into a graph
# This creates the executable workflow.
graph = workflow.compile()

# Step 18: Create initial state with the prompt
initial_state = AgentState(
    messages=[HumanMessage(content="Prepare the local repository and create a tic-tac-toe game")],
    next="CheckoutAgent"
)

# Step 19: Execute the compiled graph with the initial state
# Since there is no 'run' method, we will iterate until we reach the end state
# state = initial_state
# while state["next"] != END:
#     state = graph.invoke(state)

# Step 20: Print the result
print(graph.invoke(initial_state))
