# Gavin Bot

Gavin Bot is an automated tool designed to process GitHub issues, generate code summaries, and apply fixes to code repositories. It leverages various AI models and tools to analyze, summarize, and modify code based on the issues reported.

## Features

- **Issue Processing**: Automatically processes GitHub issues and determines if they can be fixed programmatically.
- **Code Summarization**: Generates summaries of code files to understand their logic.
- **Automated Fixes**: Applies minimal changes to the code to fix reported issues.
- **Pull Request Creation**: Automatically creates pull requests with the fixes applied.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/gavin.git
    cd gavin
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up environment variables:
    - `GROQ_API_KEY`
    - `OPENAI_API_KEY`
    - `AGENT_OPS_KEY`
    - `JIGSAW_API_KEY`

## Usage

### Running the Bot

To run the bot, use the following command:
```sh
uvicorn src.gavin_bot:app --host 127.0.0.1 --port 3000
```

### Processing Issues

The bot listens for GitHub issue events and processes them automatically. When an issue is opened, the bot will:
1. Check if the issue is supported.
2. Clone the repository.
3. Generate code summaries.
4. Apply fixes to the code.
5. Create a pull request with the fixes.

### Example

To manually process an issue, you can use the `process_issue` function:
```python
from src.gavin_bot import process_issue

process_issue(
    title="Example Issue",
    body="Description of the issue",
    github_repo="yourusername/yourrepo",
    issue_id=1
)
```

## File Structure

- `src/code_updater.py`: Contains functions for listing files, generating code summaries, fixing code, and validating results.
- `src/gavin_bot.py`: Main application file that handles GitHub issue events and processes issues.
- `src/crew_ai.py`: Contains the setup for the Crew AI agent and tasks.
- `src/jigsaw_stack.py`: Contains functions for fetching data from the Jigsaw Stack API.
- `src/utils/prompts.py`: Utility file for storing prompts used in the application.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
