# Imports
import sys
import os
import csv
import pandas as pd
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
import groq

# Load environment variables
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY") # go to groq.com and create an account, then create an API key and configure as environment variable
SOURCE_CODE_BASE_PATH = "E:\\onprem9\\" # include trailing slash

# Define LLMs and model names
llms = [
    ChatGroq(model="llama3-8b-8192", api_key=GROQ_KEY), 
    ChatGroq(model="mixtral-8x7b-32768", api_key=GROQ_KEY),
    ChatGroq(model="llama3-70b-8192", api_key=GROQ_KEY), 
    ChatGroq(model="gemma-7b-it", api_key=GROQ_KEY) 
]

model_names = [
    "llama3-8b-8192", 
    "mixtral-8x7b-32768", 
    "llama3-70b-8192", 
    "gemma-7b-it"
]

# Function to read CSV file
def read_csv(csv_filename):
    data_array = []
    try:
        df = pd.read_csv(csv_filename)
        for index, row in df.iterrows():
            full_path = SOURCE_CODE_BASE_PATH + row['file_path']
            data_line = {'full_path': full_path, 'data': row.to_dict()}
            data_array.append(data_line)
            
            try:
                with open(full_path, 'r', encoding='utf-8') as file:
                    data_array[index]['file_content'] = file.read(12000) # limit to 12000 characters to avoid context window limits
            except FileNotFoundError:
                print(f'File not found: {full_path}')
        return data_array
    except Exception as e:
        print(f'Error reading CSV file: {e}')

# Function to write CSV header
def write_csv_header(out_csv_filename):
    try:
        with open(out_csv_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["file_path", "line_content", "old_groupid", "old_artifactid", "old_versionid", "target_groupid", "target_artifactid", "target_versionid", "change_type", "change_description", "explanation"])
    except Exception as e:
        print(f'Error writing to CSV file: {e}')

# Function to generate instruction for LLM
def generate_instruction(file_content):
    old_groupid = file_content['data']['old groupId']
    old_artifactid = file_content['data']['old artifactId']
    old_versionid = file_content['data']['old versionId']
    target_groupid = file_content['data']['target groupId']
    target_artifactid = file_content['data']['target artifactId']
    target_versionid = file_content['data']['target versionId']
    line_content = file_content['data']['line_content']
    source_code = file_content['file_content']
    instruction = f"""
        We are upgrading from {old_groupid} {old_artifactid} {old_versionid} to {target_groupid} {target_artifactid} {target_versionid}.
        I am aware that {line_content} has possibly changed or is deprecated. Review the source code and explain what changes need to be made to comply with the new libraries in {target_versionid}.
        
        Your response should only consist of the following JSON object, no other text and no markdown:
            {{"change_type": "None", "change_description": "Details", "explanation": "Rationale"}}
        Possible change types: 
        None, Simple, Moderate, Complex, System-wide

        Meaning of change types:
        None: No change is required. The code is already correct and does not need to be modified.
        Simple: A small change or addition is needed. This could involve basic text search and replace, or a simple code addition.
        Moderate: A moderate change or addition is needed. This could involve method changes, refactoring, or adding new functionality.
        Complex: A large change or addition is needed. This could involve changes to multiple files or classes, or a significant refactoring effort.
        System-wide: A change or addition that affects the entire system. This could involve changing the architecture of the system, or a significant refactoring effort that affects many parts of the codebase.

        Here is the source code:
        {source_code}
        """
    return instruction

# Function to process file content with LLM
def process_file_content(file_content, llms):
    instruction = generate_instruction(file_content)
    response = None
    model = ""

    try:
        for i, llm in enumerate(llms):
            try:
                chain = llm | StrOutputParser()
                response = chain.invoke(instruction)
                model = model_names[i]
                break
            except groq.RateLimitError as e:
                print(f'Rate limit reached. Error: {e}')
            except Exception as e:
                print(f'Error processing file content: {e}')

        if response is None:
            print(f'Failed to process file content after trying all chains')
            return None

        response = response.strip('```json').strip('```')
        response = response.strip('```').strip('```')
        response = response.strip('```java').strip('```')
        response = json.loads(response)
                
        change_type = response.get('change_type', 'None')
        change_description = response.get('change_description', '')
        explanation = response.get('explanation', '')
        
        print('\n--------------------------------\n')
        print(f'LLM used: {llm.__class__.__name__}, Model: {model}')
        print('\n--------------------------------\n')
        print(response)
        print(f'Change type: {change_type}')
        print(f'Change description: {change_description}')
        print(f'Explanation: {explanation}')
        print('\n--------------------------------\n')
    except json.JSONDecodeError:
        print(f'Invalid response: {response}')
        response = None

    return response

# Function to process multiple file contents
def process_file_contents(file_contents, llms, out_csv_filename):
    responses = []

    for file_content in file_contents:
        for _ in range(3):
            response = process_file_content(file_content, llms)
            if response:
                responses.append(response)
                try: 
                    with open(out_csv_filename, 'a', newline='') as file:
                        writer = csv.writer(file)                
                        writer.writerow([file_content['data']['file_path'], file_content['data']['line_content'], file_content['data']['old groupId'], file_content['data']['old artifactId'], file_content['data']['old versionId'], file_content['data']['target groupId'], file_content['data']['target artifactId'], file_content['data']['target versionId'], response['change_type'], response['change_description'], response['explanation']])
                except Exception as e:
                    print(f'Error writing to CSV: {e}')
                break
            else:
                print(f'No response for {file_content["full_path"]}\nWill retry.\n')
        if not response:
            print(f'Failed to get response for {file_content["full_path"]} after 3 attempts')

    return responses

# Main execution
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python main.py <csv_filename>')
    else:
        csv_filename = sys.argv[1]
        file_contents = read_csv(csv_filename)
        
        out_csv_filename = csv_filename.replace('.csv', '_out.csv')
        write_csv_header(out_csv_filename)
        
        responses = process_file_contents(file_contents, llms, out_csv_filename)
