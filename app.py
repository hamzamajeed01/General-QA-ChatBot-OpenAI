from flask import Flask, request, jsonify
import openai
import pandas as pd
from docx import Document
import pdfplumber
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to extract data from CSV/Excel with multiple encoding handling
def extract_data_from_csv_excel(file_path):
    encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252', 'utf-16', 'utf-32']
    for encoding in encodings:
        try:
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path, encoding=encoding)
            else:
                return pd.read_excel(file_path, encoding=encoding)
        except (UnicodeDecodeError, ValueError) as e:
            print(f"Failed to read file with encoding {encoding}: {e}")
            continue
    raise ValueError("Unable to read the file with any known encoding.")

# Function to estimate token count
def estimate_token_count(text):
    return len(text.split())

# Function to trim text to the first 10,000 tokens
def trim_text_to_token_limit(text, max_tokens=9000):
    tokens = text.split()
    trimmed_text = " ".join(tokens[:max_tokens])
    return trimmed_text

# Function to process a single file
def process_file(file_path):
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    elif file_path.lower().endswith(('.csv', '.xlsx')):
        data = extract_data_from_csv_excel(file_path)
        return data.to_csv(index=False)
    return None

# Load all supported files from the data folder
data_folder = "D:\\Private\\Fiv\\bot\\ChatBot-GPT4API\\data" 
combined_data = ""

for filename in os.listdir(data_folder):
    file_path = os.path.join(data_folder, filename)
    if os.path.isfile(file_path) and filename.lower().endswith(('.pdf', '.docx', '.csv', '.xlsx')):
        try:
            file_content = process_file(file_path)
            if file_content:
                combined_data += f"\nContent from {filename}:\n{file_content}\n"
                print(f"Successfully processed: {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

if not combined_data:
    raise ValueError("No supported files found in the data folder. Please provide PDF, DOCX, CSV, or Excel files.")

# Check the token count and trim if necessary
token_count = estimate_token_count(combined_data)
if token_count > 9000:
    combined_data = trim_text_to_token_limit(combined_data)
    print(f"Data trimmed to 10,000 tokens. Original token count: {token_count}")

# Prepare initial messages for GPT-4
messages = [
    {"role": "system", "content": "You are an educational assistant from Hamza Corporation. Your role is to provide comprehensive answers to academic queries using both the provided educational data and your general knowledge. Be proactive in understanding the student's interests and learning goals. When interacting: 1) Introduce yourself as a Hamza Corporation educational advisor, 2) Provide detailed, well-structured explanations, 3) Ask follow-up questions to better understand the student's needs, 4) Suggest related topics they might be interested in, 5) Maintain a supportive and encouraging tone. If a question is unclear, ask for clarification to ensure you provide the most relevant and helpful response."},
    {"role": "user", "content": f"Here is the data:\n{combined_data} now user will ask questions from the data"}
]

@app.route('/ask', methods=['POST'])
def ask_question():
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({'status': 'fail', 'message': 'No question provided.'}), 400

    messages.append({"role": "user", "content": user_question})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000
        )
        output_text = response.choices[0].message.content
        messages.append({"role": "assistant", "content": output_text})
        return jsonify({'status': 'success', 'answer': output_text})
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        return jsonify({'status': 'fail', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
