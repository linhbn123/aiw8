import os
import git
import time
from github import Github
from langchain.tools import tool
from langsmith import traceable

# Initialize local repository path
TIMESTAMP = int(time.time() * 1000)
LOCAL_REPO_PATH = "/tmp/aiw8-" + str(TIMESTAMP)

@tool
@traceable
def generate_branch_name(issue_number: int) -> str:
    """
    Generate a git branch name given a git issue number.
    
    Args:
        issue_number (int): The GitHub issue number.
        
    Returns:
        str: The generated branch name.
    """
    branch_name = f"autocode/github-issue-{issue_number}-{TIMESTAMP}"
    print(f"Generated branch name: {branch_name}")
    return branch_name

@tool
@traceable
def clone_repo():
    """
    Clone the repository to the local repo path if not already cloned.
    """
    repo_url = f"https://{os.getenv('GITHUB_TOKEN')}@github.com/{os.getenv('REPO_PATH')}.git"

    if not os.path.exists(LOCAL_REPO_PATH):
        git.Repo.clone_from(repo_url, LOCAL_REPO_PATH)
        print(f"Cloned repo from {repo_url} to {LOCAL_REPO_PATH}")
    else:
        print(f"Repo already exists at {LOCAL_REPO_PATH}")

@tool
@traceable
def switch_to_local_repo_path():
    """
    Switch to the local repo path.
    """
    try:
        # Change the current working directory to the specified directory
        os.chdir(LOCAL_REPO_PATH)
        print(f"Switched to directory: {LOCAL_REPO_PATH}")
    except Exception as e:
        print(f"Failed to switch to directory: {e}")

@tool
@traceable
def checkout_source_branch():
    """
    Checkout the main branch, pull latest changes, and checkout the specific branch.
    """
    # Initialize the repository object
    repo = git.Repo(LOCAL_REPO_PATH)

    # 1. Checkout the main branch
    repo.git.checkout('main')

    # 2. Pull the latest changes
    repo.git.pull()

    # 3. Checkout the specific branch
    repo.git.checkout(os.getenv('SOURCE_BRANCH'))
    print(f"Active branch: {repo.active_branch.name}")

@tool
@traceable
def create_branch_and_push(branch_name: str, commit_message: str):
    """
    Create a new branch, add all changed files, and push to the remote origin.
    
    Args:
        branch_name (str): The name of the new branch.
        commit_message (str): The commit message.
    """
    try:
        # Initialize the repository object
        repo = git.Repo(LOCAL_REPO_PATH)

        # Create a new branch and checkout
        repo.git.checkout('-b', branch_name)
        print(f"Created and switched to new branch: {branch_name}")

        # Add all changed files
        repo.git.add(A=True)
        print("Added all changed files.")

        # Commit changes
        repo.index.commit(commit_message)
        print(f"Committed changes with message: {commit_message}")

        # Push the branch to remote
        origin = repo.remote(name='origin')
        origin.push(branch_name)
        print(f"Pushed branch {branch_name} to remote origin.")
    except Exception as e:
        print(f"An error occurred: {e}")

@tool
@traceable
def create_pull_request(title: str, body: str):
    """
    Create a pull request targeting the main branch.
    
    Args:
        title (str): The title of the pull request.
        body (str): The body description of the pull request.
    """
    try:
        # Initialize GitHub API with token
        g = Github(os.getenv('GITHUB_TOKEN'))

        # Get the repo path from the environment variables
        repo_path = os.getenv('REPO_PATH')
        
        # Get the repo object
        repo = g.get_repo(repo_path)

        # Get the current branch name
        branch_name = git.Repo(LOCAL_REPO_PATH).active_branch.name

        # Create a pull request
        pr = repo.create_pull(title=title, body=body, head=branch_name, base=os.getenv('SOURCE_BRANCH'))
        print(f"Pull request created: {pr.html_url}")
    except Exception as e:
        print(f"An error occurred: {e}")
