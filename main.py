from flask import Flask, request, jsonify
from flask_cors import CORS
from fastapi import FastAPI
import json
import os
import pandas as pd
import zipfile
from werkzeug.utils import secure_filename
import requests
from dotenv import load_dotenv
import uvicorn

from prompts import (
    conceptual_doubt_prompt,
    get_implementation_guidance_prompt,
    get_test_cases_qr_v0_prompt,
    get_specific_errors_qr_v0_prompt,
    get_publishing_related_query_system_prompt,
    get_ide_related_queries_system_prompt,
    get_query_classification_prompt
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

load_dotenv()

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Path to the commands.csv file
COMMANDS_CSV_PATH = 'commands.csv'

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_question_id(filename):
    """
    Extracts the question ID from the zip file's name.
    Assumes the zip file name is in the format "RJSCPYQN94.zip".
    """
    # Remove the .zip extension and extract the question ID
    if filename.endswith('.zip'):
        return filename[:-4]  # Remove the last 4 characters (.zip)
    return None

def get_question_details(question_id):
    """
    Fetches the question details from the commands.csv file based on the question ID.
    """
    try:
        df = pd.read_csv(COMMANDS_CSV_PATH)
        question_details = df[df['question_command_id'] == question_id]
        return {
            "question_content": question_details['question_content'],
            "question_test_cases": question_details['question_test_cases']
        }
    except Exception as e:
        print(f"Error fetching question details: {e}")
        return None

def extract_user_code(zip_path):
    """
    Extracts and reads all files from the uploaded zip file.
    Returns a concatenated string of all file contents.
    """
    try:
        user_code = ""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(UPLOAD_FOLDER)
            extracted_files = zip_ref.namelist()
            print(f"Extracted files: {extracted_files}")  # Debug: List all files in the zip

            for file in extracted_files:
                file_path = os.path.join(UPLOAD_FOLDER, file)
                if os.path.isfile(file_path):  # Ensure it's a file, not a directory
                    # print(f"Reading file: {file_path}")  # Debug: Print the file being read
                    try:
                        with open(file_path, 'r', encoding='utf-8') as code_file:
                            content = code_file.read()
                            user_code += f"\n\n=== {file} ===\n"
                            user_code += content
                    except UnicodeDecodeError:
                        print(f"Skipping binary or non-utf-8 file: {file_path}")
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")

        if not user_code:
            print("No valid text files found in the zip file.")  # Debug: No files were read
            return "No valid text files found in the zip file."
        return user_code
    except Exception as e:
        print(f"Error extracting user code: {e}")
        return None

def llm_call(system_prompt, user_prompt):
    print("Calling Deepseek API")

    # Prepare messages as required by the API.
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    print("system_prompt", system_prompt)
    print("user_prompt", user_prompt)
    request_body = {
        "messages": messages,
        "model": "DEEPSEEK-REASONER", # Specify the valid model
        "temperature": 0.0
    }

    # Instantiate the OpenAI client with the proper endpoint and API key.
    request_url = os.getenv("REQUEST_URL")
    api_key = os.getenv("API_KEY")

    # Send the request and get the response.
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.post(request_url, headers=headers, json=request_body)

    # Convert response to JSON and extract the assistant's message.
    data = response.json()
    res_text = data["choices"][0]["message"]["content"]
    return res_text

def analyze_user_query(user_query):
    """
    Analyzes the user query and classifies it into one of the predefined categories.
    """
    print("statred")
    system_prompt = get_query_classification_prompt()
    result = llm_call(system_prompt, user_query)
    result = json.loads(result.replace("```json","").replace("```",""))
    print(result)
    return result

@app.route("/")
def home():
    return "Hello, Render!"

@app.route('/api/process', methods=['POST'])
def process_query():
    """
    Handles the POST request from the frontend.
    Expects a user query and an optional zip file.
    """
    try:
        # Get the user query from the request
        user_query = request.form.get('query')
        if not user_query:
            return jsonify({"response": "User query is required"}), 400

        # Handle file upload (if any)
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                print(f"File uploaded successfully: {file_path}")
            else:
                return jsonify({"response": "Invalid file type. Only .zip files are allowed"}), 400

        # Extract question ID from the zip file name
        if file_path:
            question_id = extract_question_id(file.filename)
            if not question_id:
                return jsonify({"response": "Question ID not found in the zip file name"}), 400
        else:
            return jsonify({"response": "Zip file is required to extract the question ID"}), 400

        # Analyze the user query
        print("stated")
        analysis_result = analyze_user_query(user_query)
        print("ended")
        user_query_summary = analysis_result.get("user_query_summary", "")
        query_category = analysis_result.get("query_category", "Other")

        # Fetch question details from the CSV file
        question_details = get_question_details(question_id)
        if not question_details:
            return jsonify({"response": "Question details not found"}), 400

        # Extract user code from the zip file
        user_code = extract_user_code(file_path) if file_path else "No code provided"

        # Construct the issue context
        issue_context = (
            f"User Query: {user_query_summary}, "
            f"Question details: {question_details}, "
            f"User code: {user_code}"
        )
        
        # Import prompts based on query category
        # Replace this with your actual logic to import prompts
        if "Test case failures" in query_category or \
        "Unexpected output" in query_category or \
        "Mistakes Explanation" in query_category:
            response = llm_call(get_test_cases_qr_v0_prompt(), issue_context)

        elif "Fix specific errors" in query_category:
            response = llm_call(get_specific_errors_qr_v0_prompt(), issue_context)

        elif "Code publishing issue" in query_category:
            response = llm_call(get_publishing_related_query_system_prompt(), user_query_summary)

        elif "IDE issue" in query_category:
            response = llm_call(get_ide_related_queries_system_prompt(), user_query_summary)

        elif "Conceptual doubts" in query_category:
            response = llm_call(conceptual_doubt_prompt(), user_query_summary)

        elif "Problem solving approach" in query_category or "Implementation guidance" in query_category:
            response = llm_call(get_implementation_guidance_prompt(), issue_context)

        else:
            response = "<mentor_required>"

        # Return the response as JSON
        return jsonify({"response": response}), 200

    except Exception as e:
        # Handle any unexpected errors
        return jsonify({"response": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
