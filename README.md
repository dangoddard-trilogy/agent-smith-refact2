# README

## Overview

This project is designed to process source code files listed in a CSV file, analyze them using various language models (LLMs), and generate a report on the necessary changes required to upgrade dependencies. The results are written to an output CSV file.

## Prerequisites

- Python 3.6+
- Required Python packages: `pandas`, `python-dotenv`, `langchain_groq`, `langchain_core`, `groq`
- An API key from [groq.com](https://groq.com)

## Setup

1. **Clone the repository:**
    ```sh
    git clone https://github.com/your_username/your_repo_name.git
    cd your_repo_name
    ```

2. **Install the required packages:**
    ```sh
    pip install pandas python-dotenv langchain_groq langchain_core groq
    ```

3. **Set up environment variables:**
    - Create a `.env` file in the root directory.
    - Add your Groq API key to the `.env` file:
        ```
        GROQ_API_KEY=your_groq_api_key
        ```

4. **Update the source code base path:**
    - Modify the `SOURCE_CODE_BASE_PATH` variable in `app/main.py` to point to the base directory of your source code files.

## Usage

1. **Prepare your CSV file:**
    - The CSV file should contain the following columns:
        - `file_path`: Relative path to the source code file.
        - `line_content`: Content of the line that may have changed.
        - `old groupId`, `old artifactId`, `old versionId`: Old dependency details.
        - `target groupId`, `target artifactId`, `target versionId`: New dependency details.

2. **Run the script:**
    ```sh
    python app/main.py <csv_filename>
    ```
    - Replace `<csv_filename>` with the path to your CSV file.

3. **Output:**
    - The script will generate an output CSV file with the same name as the input file, appended with `_out.csv`.
    - The output CSV will contain the following columns:
        - `file_path`, `line_content`, `old_groupid`, `old_artifactid`, `old_versionid`, `target_groupid`, `target_artifactid`, `target_versionid`, `change_type`, `change_description`, `explanation`

## Functions

### `read_csv(csv_filename)`
Reads the input CSV file and returns a list of dictionaries containing file paths and their respective data.

### `write_csv_header(out_csv_filename)`
Writes the header row to the output CSV file.

### `generate_instruction(file_content)`
Generates an instruction string for the LLM based on the file content.

### `process_file_content(file_content, llms)`
Processes a single file content using the LLMs and returns the response.

### `process_file_contents(file_contents, llms, out_csv_filename)`
Processes multiple file contents and writes the results to the output CSV file.

## Error Handling

- The script handles file not found errors and rate limit errors from the Groq API.
- If an error occurs while reading the CSV or writing to the output CSV, it will print an error message.

## License

This project is licensed under the MIT License.

