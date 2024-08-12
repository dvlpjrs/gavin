# prompts.py

CHECK_ISSUE_SUPPORT_PROMPT = """
Analyse the user created issue in github and categories it based on its fixable logical (by logical i mean its a bug in code that can be fixed and not eniveriment related or anything with external factor) or not. Only answer it as true or false
"""

GEN_CODE_FILE_SUMMARY_PROMPT = """
Explain the logic of the files in short paragraph no more than 2-4 lines. Only provide the explanation without any other data
"""

GET_FILES_TO_MODIFY_PROMPT = """
Based on the issue, please provide me the least amount of files that needs to be modified to fix the issue. Only provide file paths with one file path per line and nothing else
"""

FIX_CODE_PROMPT = """
Fix the user provided code with minimal changes and provide the complete final code to directly replace the old code. Ensure the response is in valid JSON format and contains no explanations.
example:
[{"path": "./example/app/app.py", "code": "print('hello world')"}]
"""

VALIDATE_RESULT_PROMPT = """
Based on the issue and solution suggested, can you return a true or false based on how accurately the issue is solved or not? Dont include anything else
"""
