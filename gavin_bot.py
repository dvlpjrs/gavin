import os
import requests
from fastapi import FastAPI, Request
from github import GithubIntegration
from code_updater import (
    check_issue_support,
    run,
)
import shutil
import subprocess
from decouple import config

app = FastAPI()

app_id = config('GITHUB_APP_ID')
app_key_path = config('GITHUB_APP_KEY_PATH')

with open(os.path.normpath(os.path.expanduser(app_key_path)), "r") as cert_file:
    app_key = cert_file.read()

gi = GithubIntegration(
    app_id,
    app_key,
)

installation = gi.get_installations()[0]
g = installation.get_github_for_installation()

def git_command(command, cwd):
    """
    Run a Git command in the specified directory.

    Args:
        command (str): The Git command to run.
        cwd (str): The directory to run the command in.

    Returns:
        str: The output of the Git command.
    """
    result = subprocess.run(
        command, cwd=cwd, shell=True, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise Exception(f"Git command failed: {result.stderr}")
    return result.stdout

def process_issue(title, body, github_repo, issue_id):
    """
    Process an issue by cloning the repository, checking if the issue is supported,
    running the fix, and creating a pull request.

    Args:
        title (str): The title of the issue.
        body (str): The body of the issue.
        github_repo (str): The name of the GitHub repository.
        issue_id (int): The ID of the issue.
    """
    repo = g.get_repo(github_repo)
    issue = repo.get_issue(number=issue_id)
    issue.edit(labels=["GAVIN PROCESSING"])
    try:
        # Get the issue and process it
        if not check_issue_support(title, body):
            issue.edit(labels=["Human Action Needed"])
            return

        # download repo
        temp_dir = "temp"
        if os.path.exists(temp_dir):
            print("Deleting temp directory")
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        git_command(
            f"git clone https://github.com/{github_repo}.git {temp_dir}", cwd="."
        )
        git_command(f"git checkout -b issue-{issue_id}", cwd=temp_dir)
        git_command(f"git pull origin main", cwd=temp_dir)
        git_command(f"git rebase main", cwd=temp_dir)

        print("Running Fix")
        run(temp_dir, body)
        print("Fix complete")
        branch_name = f"issue-{issue_id}"
        git_command(f"git add .", cwd=temp_dir)
        git_command(f'git commit -m "Fix issue #{issue_id}: {title}"', cwd=temp_dir)
        git_command(f"git push origin {branch_name}", cwd=temp_dir)

        # Create a pull request
        pr = repo.create_pull(
            title=f"Fix issue #{issue_id}: {title}",
            body=f"Automatically created PR to fix issue #{issue_id}",
            head=branch_name,
            base="main",
        )
        issue.edit(labels=["GAVIN PROCESSED"], state="closed")
        print(f"Pull request created: {pr.html_url}")
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(e)
        issue.edit(labels=["Human Action Needed"])

def label_update():
    """
    Update the labels of an issue in a test repository.
    """
    repo = g.get_repo("dvlpjrs/test_issue")
    print(repo)
    issue = repo.get_issue(number=1)
    issue.edit(labels=["Human Action Needed"])

@app.post("/")
async def bot(request: Request):
    """
    Handle incoming requests from GitHub.

    Args:
        request (Request): The incoming request.

    Returns:
        str: A response to the request.
    """
    payload = await request.json()
    if payload["action"] == "opened":
        if "issue" in payload:
            title = payload["issue"]["title"]
            body = payload["issue"]["body"]
            github_repo = payload["repository"]["full_name"]
            issue_id = payload["issue"]["number"]
            process_issue(title, body, github_repo, issue_id)
    return "ok"

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=3000)