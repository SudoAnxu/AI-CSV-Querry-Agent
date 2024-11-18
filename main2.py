import streamlit as st
import pandas as pd
import requests
import os
import re
import ast
import logging
from google.oauth2.service_account import Credentials
import gspread
from groq import Groq

logging.basicConfig(level=logging.DEBUG)

# Configuration
os.environ["GROQ_API_KEY"] = "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"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
SERPAPI_KEY = "b5371d2b326d0cb17d3cc54202d32fd3ba3f44bbfad1c65df9fbb93f5c88c014"

# Streamlit app
st.title("Google Sheets & Groq API Integration")
groq_api_key = st.secrets["GROQ_API_KEY"]["value"]
serpapi_key = st.secrets["SERPAPI_KEY"]["value"]
# Placeholder for uploaded data
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None

# Function to fetch data from Google Sheets
def fetch_google_sheet_data(sheet_id, service_account_path):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(service_account_path, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    if not df.empty:
        df.columns = df.iloc[0]
        df = df[1:]
    return df

# Step 1: Upload CSV
st.subheader("Step 1: Upload a CSV File or Connect to Google Sheets")
file = st.file_uploader("Upload a CSV file", type=["csv"])

if file:
    st.session_state.uploaded_data = pd.read_csv(file)
    st.success("CSV uploaded successfully!")

# Step 2: Connect to Google Sheets
sheet_id = st.text_input("Enter Google Sheet ID to fetch data")
if st.button("Fetch Google Sheet Data"):
    service_account_path = "service-account.json"
    try:
        st.session_state.uploaded_data = fetch_google_sheet_data(sheet_id, service_account_path)
        st.success("Google Sheet data fetched successfully!")
    except Exception as e:
        st.error(f"Error: {e}")

# Preview the uploaded or fetched data
if st.session_state.uploaded_data is not None:
    st.subheader("Preview of the Data")
    st.dataframe(st.session_state.uploaded_data.head())
# Step 3: Select Column and Prompt
if st.session_state.uploaded_data is not None:
    st.subheader("Step 2: Select a Column and Enter a Prompt")
    column = st.selectbox("Select a Column", st.session_state.uploaded_data.columns)
    user_prompt = st.text_area("Enter your prompt with `{company}` placeholder")

    if st.button("Process Data"):
        def search_entity(entity, user_prompt):
            response = requests.get(
                "https://serpapi.com/search",
                params={"q": f"{user_prompt} {entity}", "api_key": SERPAPI_KEY, "location": "United States"}
            )
            search_data = response.json()
            results = [
                {"title": result.get("title"), "snippet": result.get("snippet"), "link": result.get("link")}
                for result in search_data.get("organic_results", [])
            ]
            return results

        def extract_with_groq(entity, search_results, user_prompt):
            context = "\n".join([f"Title: {res['title']}, Snippet: {res['snippet']}" for res in search_results])
            prompt = f"{user_prompt}:\n{context}"
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}], model="llama3-8b-8192"
            )
            contextual_info = chat_completion.choices[0].message.content
            dict_prompt = """Please analyze the response text below and extract specific information based on the requirements provided in the initial prompt. Structure the information into a clean dictionary, ensuring that only relevant keys and values are included.
                        Please analyze the provided response text and extract only the relevant information required by the initial prompt. Structure the extracted data in a dictionary format, where the key corresponds exactly to the specific prompt requirement, and the value is the relevant information from the response.

                        Guidelines:
                        Key Consistency: Ensure that the key in the dictionary directly matches the requirement in the prompt. Avoid variations or added detail in the key name, such as "CEO_name" when it should simply be "CEO". The key should be as precise as the prompt’s requirement (e.g., if the prompt asks for the CEO, the key should be "CEO").

                        Relevant Data Only: Only    include the specific data requested in the prompt. Do not include extra or unnecessary details. If the prompt asks for "CEO", the response should include only the CEO's name with the key "CEO".

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
                messages=[{"role": "user", "content": prompt_2}], model="llama3-8b-8192"
            )
            extracted_info = chat_completion_2.choices[0].message.content
            pattern = r"\{(.*?)\}"
            cleaned_info = re.search(pattern, extracted_info, re.DOTALL).group(0)
            return cleaned_info

        results = []
        for entity in st.session_state.uploaded_data[column].unique():
            prompt = user_prompt.replace("{company}", entity)
            search_results = search_entity(entity, user_prompt)
            extracted_info = extract_with_groq(entity, search_results, user_prompt)
            entity_info = {f"{column}": entity}
            entity_info.update(ast.literal_eval(extracted_info))
            results.append(entity_info)

        results_df = pd.DataFrame(results)
        combined_df = pd.merge(st.session_state.uploaded_data, results_df, on=column, how="inner")
        st.session_state.results_df = combined_df

        # Display the results before offering download
        st.subheader("Processed Data")
        st.dataframe(st.session_state.results_df)

# Step 4: Download Processed Data
if "results_df" in st.session_state:
    st.subheader("Step 3: Download the Results")
    st.download_button(
        label="Download Results CSV",
        data=st.session_state.results_df.to_csv(index=False),
        file_name="results.csv",
        mime="text/csv",
    )
