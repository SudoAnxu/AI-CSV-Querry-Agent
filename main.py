from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from groq import Groq
import pandas as pd
import requests
import os
import re
import ast
import logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# Groq API configuration
os.environ["GROQ_API_KEY"] = "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"
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Replace with the correct endpoint URL
client = Groq(
    api_key="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",  # Or set your API key directly
)
# Google Sheets and Search API configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEETS_CREDENTIALS = "token.json"
SERPAPI_KEY = "b5371d2b326d0cb17d3cc54202d32fd3ba3f44bbfad1c65df9fbb93f5c88c014"

# Placeholder for storing uploaded data
uploaded_data = None

# Google Sheets data retrieval function
def fetch_google_sheet_data(sheet_id, service_account_path):
    """
    Fetches data from a Google Sheet using its ID and a service account JSON file.

    Args:
        sheet_id (str): The Google Sheet ID.
        service_account_path (str): The path to the service account JSON file.

    Returns:
        pd.DataFrame: A DataFrame containing the data from the Google Sheet.
    """
    import gspread
    from google.oauth2.service_account import Credentials

    # Define the required scope for Google Sheets API
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Authenticate with the service account
    creds = Credentials.from_service_account_file(service_account_path, scopes=scope)
    
    # Connect to the Google Sheets API
    client = gspread.authorize(creds)
    
    # Open the Google Sheet by ID
    sheet = client.open_by_key(sheet_id)
    
    # Access the first worksheet
    worksheet = sheet.get_worksheet(0)
    
    # Fetch all data from the worksheet
    data = worksheet.get_all_values()

    # Convert the data to a Pandas DataFrame
    df = pd.DataFrame(data)
    
    # Use the first row as column headers if available
    if not df.empty:
        df.columns = df.iloc[0]  # Set the first row as the header
        df = df[1:]  # Drop the first row from the data
    
    return df


@app.route('/')
def index():
    return '''
        <form action="/upload_csv" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".csv">
            <input type="submit" value="Upload CSV">
        </form>
        <form action="/connect_google_sheet" method="post">
            <input type="text" name="sheet_id" placeholder="Enter Google Sheet ID">
            <input type="submit" value="Connect Google Sheet">
        </form>
    '''

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    global uploaded_data
    file = request.files['file']
    if file:
        uploaded_data = pd.read_csv(file)
        return redirect(url_for('select_column'))
    else:
        return "File upload failed."

@app.route('/connect_google_sheet', methods=['POST'])
def connect_google_sheet():
    global uploaded_data
    sheet_id = request.form['sheet_id']
    service_account_path = "service-account.json"
    try:
        uploaded_data = fetch_google_sheet_data(sheet_id, service_account_path)
        if not uploaded_data.empty:
            return redirect(url_for('select_column'))
        else:
            return "Google Sheet is empty or could not be fetched.", 400
    except Exception as e:
        logging.exception("Failed to connect to Google Sheet.")
        data = fetch_google_sheet_data(sheet_id, service_account_path)
        print(data)
        return f"Google Sheet connection failed: {str(e)}", 500


@app.route('/select_column', methods=['GET', 'POST'])
def select_column():
    if request.method == 'POST':
        selected_column = request.form['selected_column']
        user_prompt = request.form['user_prompt']
        return redirect(url_for('process_data', selected_column=selected_column, user_prompt=user_prompt,uploaded_data=uploaded_data))
    
    columns = uploaded_data.columns.tolist()
    preview = uploaded_data.head().to_html()
    return render_template('select_column.html', columns=columns, preview=preview)

@app.route('/process_data')
def process_data():
    selected_column = request.args.get('selected_column')
    user_prompt = request.args.get('user_prompt')
    
    results = []
    for entity in uploaded_data[selected_column].unique():
        prompt = user_prompt.replace("{company}", entity)
        search_results = search_entity(entity,user_prompt)
        extracted_info = extract_with_groq(entity, search_results, user_prompt)
        # print("extracted_info after:" ,extracted_info)
        extracted_info = ast.literal_eval(extracted_info)
        entity_info = {f"{selected_column}": entity}
        entity_info.update(extracted_info)
        results.append(entity_info)
    print(results)
    results_df = pd.DataFrame(results)
    combined_df = pd.merge(uploaded_data, results_df, on=f"{selected_column}", how="inner")
    combined_df.to_csv("results.csv", index=False)
    
    return redirect(url_for('download_results'))

# Route to download results.csv
@app.route('/download_results')
def download_results():
    return send_file("results.csv", as_attachment=True)

# Search function using SerpAPI
def search_entity(entity,user_prompt):
    response = requests.get(
        "https://serpapi.com/search",
        params={"q": f"{user_prompt} {entity}", "api_key": SERPAPI_KEY, "location": "United States"}
    )
    search_data = response.json()
    results = [
        {"title": result.get("title"), "snippet": result.get("snippet"), "link": result.get("link")}
        for result in search_data.get("organic_results", [])
    ]
    # print(results)
    return results

# Groq LLM extraction function
def extract_with_groq(entity, search_results,user_prompt):
    context = "\n".join([f"Title: {res['title']}, Snippet: {res['snippet']}" for res in search_results])
    prompt = f"{user_prompt}:\n{context}"

    # Groq API call for chat completion
    # try:
    chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",  # Choose the appropriate model
        )

        # Get the response from the model
    
    contextual_info= chat_completion.choices[0].message.content
    print("contextual",contextual_info)
    dict_prompt = """

Please analyze the response text below and extract specific information based on the requirements provided in the initial prompt. Structure the information into a clean dictionary, ensuring that only relevant keys and values are included.
Please analyze the provided response text and extract only the relevant information required by the initial prompt. Structure the extracted data in a dictionary format, where the key corresponds exactly to the specific prompt requirement, and the value is the relevant information from the response.

Guidelines:
Key Consistency: Ensure that the key in the dictionary directly matches the requirement in the prompt. Avoid variations or added detail in the key name, such as "CEO_name" when it should simply be "CEO". The key should be as precise as the prompt’s requirement (e.g., if the prompt asks for the CEO, the key should be "CEO").

Relevant Data Only: Only include the specific data requested in the prompt. Do not include extra or unnecessary details. If the prompt asks for "CEO", the response should include only the CEO's name with the key "CEO".

Handling Missing Information: If the requested information is missing, mark it explicitly as "Not found". Ensure this is consistent across all responses.

Flexibility in Labeling: The model should decide the most accurate label for the key based on the context of the response. The key should be aligned with the most relevant and common term used for the entity in the response.

Output Structure: The final output should be in the form of a dictionary with the key-value pair. Only return the dictionary with the relevant keys. The dictionary should be clean, well-structured, and precise, with no extraneous text or formatting.
- The dictionary should contain only the keys directly related to the prompt's requirements. If a specific piece of information is not found in the response, the value should be marked as "Not found".
- The dictionary must be formatted as follows:
 
 {
     "only_relevant_key_from_prompt_requirement": "value_from_response"
 }
 
 For example:
If the context of the prompt is "Find me the Email of the company", the expected output would look like:
{
    "email": "Not found"
    }


Return only after making into dictionary, ensuring no additional text, explanation, or formatting.

"""
    prompt_2 = f"{dict_prompt}:\n{contextual_info}"
    chat_completion_2 = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt_2,
                }
            ],
            model="llama3-8b-8192",  # Choose the appropriate model
        )
    extracted_info_1= chat_completion_2.choices[0].message.content
    print("extracted info:",extracted_info_1)
    # pattern = r"```(.*?)```"
    # cleaned_info = extracted_info_1.strip()

# Remove any leading/trailing context that is not part of the dictionary (if necessary)
    # cleaned_info = re.sub(r'^.*\{', '{', cleaned_info)  # Ensures we start at the opening curly brace
    # cleaned_info = re.sub(r'\}.*$', '}', cleaned_info)  # Ensures we end at the closing curly brace
    pattern1 = r"\{(.*?)\}"
    cleaned_info = ((re.search(pattern1, extracted_info_1, re.DOTALL)).group(0))
    # {pattern1 = r"\{(.*?)\}"
    # match1 = re.search(pattern1, extracted_info_1, re.DOTALL)
    
    print("clened:",cleaned_info)
    
    # return extracted_info}
    return cleaned_info

    
    # except Exception as e:
    #     print(f"Error during Groq API request: {e}")
    #     return "Error extracting info"

if __name__ == '__main__':
    app.run(debug=True)
