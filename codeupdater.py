import os
from groq import Groq
from decouple import config
import re
import json
from openai import OpenAI
from utils import PROMPTS


os.environ["GROQ_API_KEY"] = config("GROQ_API_KEY")
os.environ["OPENAI_API_KEY"] = config("OPENAI_API_KEY")

client = Groq()
openai_client = OpenAI()


def list_all_files(directory):
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


def check_issue_support(title, body):
    # Check if the issue is supported by the bot
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Analyse the user created issue in github and categories it based on its fixable logical (by logical i mean its a bug in code that can be fixed and not eniveriment related or anything with external factor) or not. Only answer it as true or false",
            },
            {
                "role": "user",
                "content": f"""
                title: {title}
                body: {body}
             """,
            },
        ],
    )
    if completion.choices[0].message.content.lower() == "false":
        return False
    return True


def gen_code_file_summary(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Explain the logic of the files in short paragraph no more than 2-4 lines. Only provide the explanation without any other data",
            },
            {"role": "user", "content": "\n".join(lines)},
        ],
        max_tokens=1024,
    )
    return f"{file_path} - {completion.choices[0].message.content}"


def get_files_to_modify(issue):
    # Get the files that need to be modified to fix the issue
    with open("ai_summary.txt", "r") as file:
        lines = file.read()
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"""Based on the issue, please provide me the least amount of files that needs to be modified to fix the issue. Only provide file paths with one file path per line and nothing else 
                Issue: {issue}""",
            },
            {"role": "user", "content": lines},
        ],
        max_tokens=1024,
    )
    return completion.choices[0].message.content.split("\n")


def fix_code(file_paths, issue):
    prompt = f"The issue faced: {issue}\n"
    # Fix the issue in the file
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
                "content": """Fix the user provided code with minimal changes and provide the complete final code to directly replace the old code. Ensure the response is in valid JSON format and contains no explanations.
            example:
            [{"path": "./example/app/app.py", "code": "print('hello world')"}]""",
            },
            {"role": "user", "content": prompt},
        ],
    )
    modified_code = completion.choices[0].message.content
    return json.loads(modified_code)


def update_code(file_paths, code):
    for x in file_paths:
        with open(x, "w") as file:
            file.write(code)


def validate_result(issue, modified_code):
    prompt = f"""
    issue: {issue}
    modified_code: {modified_code}
    """
    validate_count = 0
    completion1 = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """Based on the issue and solution suggested, can you return a true or false based on how accurately the issue is solved or not? Dont include anything else""",
            },
            {"role": "user", "content": prompt},
        ],
    )
    completion2 = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "system",
                "content": """Based on the issue and solution suggested, can you return a true or false based on how accurately the issue is solved or not? Dont include anything else""",
            },
            {"role": "user", "content": prompt},
        ],
    )
    completion3 = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """Based on the issue and solution suggested, can you return a true or false based on how accurately the issue is solved or not? Dont include anything else""",
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
    if validate_count >= 2:
        return True

    return False


def run(code_dir, issue_body):
    ai_summary = ""
    temp = list_all_files(code_dir)
    for x in temp:
        try:
            ai_summary += gen_code_file_summary(x) + "\n"
        except:
            pass

    with open("ai_summary.txt", "w") as file:
        file.write(ai_summary)

    files_to_modify = get_files_to_modify(issue_body)
    new_code = fix_code(files_to_modify, issue_body)
    # if validate_result(issue_body, new_code):
    #     raise Exception("Code not validated")
    for x in new_code:
        update_code([x["path"]], x["code"])
