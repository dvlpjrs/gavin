import os
import requests
from fastapi import FastAPI, Request
from github import GithubIntegration
from codeupdater import (
    check_issue_support,
    run,
)
import shutil
import subprocess


app = FastAPI()
app_id = "955375"
with open(os.path.normpath(os.path.expanduser("./bot_key.pem")), "r") as cert_file:
    app_key = cert_file.read()

# Create an GitHub integration instance
gi = GithubIntegration(
    app_id,
    app_key,
)

installation = gi.get_installations()[0]
g = installation.get_github_for_installation()


def git_command(command, cwd):
    result = subprocess.run(
        command, cwd=cwd, shell=True, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise Exception(f"Git command failed: {result.stderr}")
    return result.stdout


def process_issue(title, body, github_repo, issue_id):
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
    repo = g.get_repo("dvlpjrs/test_issue")
    print(repo)
    issue = repo.get_issue(number=1)
    issue.edit(labels=["Human Action Needed"])


@app.post("/")
async def bot(request: Request):
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
