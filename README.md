# AI CSV Query and Manipulation Agent

A Streamlit app for natural language processing and AI-assisted code generation on your CSV/Excel datasets! With support for chemistry, science, healthcare, or any tabular data.
Click the badge below to launch a free, temporary workspace and try the app online (no local setup needed):

[[Open in Streamlit]](https://ai-csv-querry-agent-khhv88pepu3mnresse6gfq.streamlit.app/)
## Features

- Upload your own CSV or Excel files
- Ask questions or give commands in plain English (e.g., "plot graph of T_comb (K) against Metal Percent")
- See LLM-generated code, reviewed for safety and run directly against your data
- Download updated data at any time

## Requirements

- Python 3.8 or newer (recommended)
- See `requirements.txt` for Python dependencies

## Installation

1. Clone this repository or download the code.

2. Install dependencies (ideally in a fresh virtual environment):

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up your Groq API key:**

   - Edit or create the file `.streamlit/secrets.toml` in your project root:
     ```
     GROQ_API_KEY = "<your-groq-api-key-here>"
     ```

## Usage

1. Run the app:

    ```bash
    streamlit run main.py
    ```

2. In your browser, you will be able to:
    - Upload CSV or Excel files
    - Ask questions or instruct the agent (plot, summarize, add columns, etc.)
    - Review generated (and cleaned) code
    - See results or download improved data

## Tips

- The agent is context-aware: it will only use the columns present in your file!
- Avoid ambiguous queries for best results. Example good queries:
    - Make new empty column named 'Vector'
    - Plot graph of T_comb (K) against Metal Percent
    - Show mean of column X grouped by column Y
- All generated code is checked for safety before running.

## Security

Guardrails are in place to block unsafe code, but always review generated code before running in highly sensitive environments.

## License

MIT License
