import os
from groq import Groq
from decouple import config
import re
import json
from openai import OpenAI
from utils import prompts

# Set environment variables
os.environ["GROQ_API_KEY"] = config("GROQ_API_KEY")
os.environ["OPENAI_API_KEY"] = config("OPENAI_API_KEY")

# Initialize clients
client = Groq()
openai_client = OpenAI()

def list_all_files(directory):
    """List all files in a directory."""
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths

def check_issue_support(title, body):
    """Check if the issue is supported by the bot."""
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": prompts.CHECK_ISSUE_SUPPORT_PROMPT,
            },
            {
                "role": "user",
                "content": f"title: {title}\nbody: {body}",
            },
        ],
    )
    return completion.choices[0].message.content.lower() == "true"

def gen_code_file_summary(file_path):
    """Generate a summary of the code file."""
    with open(file_path, "r") as file:
        lines = file.readlines()
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": prompts.GEN_CODE_FILE_SUMMARY_PROMPT,
            },
            {"role": "user", "content": "\n".join(lines)},
        ],
        max_tokens=1024,
    )
    return f"{file_path} - {completion.choices[0].message.content}"

def get_files_to_modify(issue):
    """Get the files that need to be modified to fix the issue."""
    with open("temp/ai_summary.txt", "r") as file:
        lines = file.read()
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"{prompts.GET_FILES_TO_MODIFY_PROMPT}\nIssue: {issue}",
            },
            {"role": "user", "content": lines},
        ],
        max_tokens=1024,
    )
    return completion.choices[0].message.content.split("\n")

def fix_code(file_paths, issue):
    """Fix the issue in the provided files."""
    prompt = f"The issue faced: {issue}\n"
    for x in file_paths:
        if not os.path.exists(x):
            continue
        prompt += f"Path: {x}\n"
        with open(x, "r") as file:
            prompt += file.read()

    print(prompt)
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": prompts.FIX_CODE_PROMPT,
            },
            {"role": "user", "content": prompt},
        ],
    )
    modified_code = completion.choices[0].message.content
    return json.loads(modified_code)

def update_code(file_paths, code):
    """Update the code in the provided file paths."""
    for x in file_paths:
        with open(x, "w") as file:
            file.write(code)

def validate_result(issue, modified_code):
    """Validate the result of the code modification."""
    prompt = f"issue: {issue}\nmodified_code: {modified_code}\n"
    validate_count = 0
    completion1 = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": prompts.VALIDATE_RESULT_PROMPT,
            },
            {"role": "user", "content": prompt},
        ],
    )
    completion2 = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "system",
                "content": prompts.VALIDATE_RESULT_PROMPT,
            },
            {"role": "user", "content": prompt},
        ],
    )
    completion3 = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": prompts.VALIDATE_RESULT_PROMPT,
            },
            {"role": "user", "content": prompt},
        ],
    )
    if completion1.choices[0].message.content.lower() == "true":
        validate_count += 1
    if completion2.choices[0].message.content.lower() == "true":
        validate_count += 1
    if completion3.choices[0].message.content.lower() == "true":
        validate_count += 1
    print(validate_count)
    return validate_count >= 2

def run(code_dir, issue_body):
    """Run the code updater process."""
    ai_summary = ""
    temp = list_all_files(code_dir)
    for x in temp:
        try:
            ai_summary += gen_code_file_summary(x) + "\n"
        except:
            pass

    os.makedirs("temp", exist_ok=True)
    with open("temp/ai_summary.txt", "w") as file:
        file.write(ai_summary)

    files_to_modify = get_files_to_modify(issue_body)
    new_code = fix_code(files_to_modify, issue_body)
    if not validate_result(issue_body, new_code):
        raise Exception("Code not validated")
    for x in new_code:
        update_code([x["path"]], x["code"])

    # Delete the ai_summary.txt file
    os.remove("temp/ai_summary.txt")