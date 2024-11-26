from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import requests
import os
import openai
import pdfplumber
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv

# Load .env file
load_dotenv(dotenv_path="env/.env")
# Debugging to check API Key
# print("Loaded API Key:", os.getenv("OPENAI_API_KEY"))

# Set up Flask app
app = Flask(__name__)
CORS(app)

# OpenAI API Key (replace with your actual API key)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize SentenceTransformer model
similarity_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Function to download the PDF from a URL
def download_pdf(url, save_path="downloaded.pdf"):
    response = requests.get(url)
    with open(save_path, "wb") as file:
        file.write(response.content)
    return save_path


    # Function to extract tables from PDF
def extract_tables_from_pdf(file_path):
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            for table in page_tables:
                tables.append(table)
    return tables

# Function to query OpenAI
def query_openai(question, context):
    try:
        response =  openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that answers questions based on the provided context."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip() + "\n\nUntuk info lebih lanjut silahkan ke halaman https://www.ut.ac.id/katalog/"
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return "Maaf, saya tidak dapat memproses permintaan Anda saat ini.\n\nUntuk info lebih lanjut silahkan ke halaman https://www.ut.ac.id/katalog/"

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question", "").lower()

    # PDF URL
    pdf_url = "https://www.ut.ac.id/wp-content/uploads/2024/06/KATALOG-PENYELENGGARAAN-TAHUN-2024-2025.pdf"

    # Download and extract text and tables
    pdf_path = download_pdf(pdf_url)
  
    pdf_tables = extract_tables_from_pdf(pdf_path)  # Extract tables
    os.remove(pdf_path)

    # Format tables as text
    table_related_keywords = ["biaya", "rincian", "tabel", "uang kuliah", "program studi", "nama", "e-mail", "wilayah kerja", "kode", "perssyaratan", "calon mahasiswa", "fkip", "mata kuliah", "jam ujian bentrok", "program diploma", "program sarjana", "sarjana", "diploma", "skema", "skema layanan", "skema layanan sistem paket semester", "paket semester","kelengkapan dokumen", "dokumen wajib", "syarat FKIP", 
    "mata kuliah", "jadwal bentrok", "jam ujian bentrok",
    "uang kuliah", "SIPAS", "paket semester", "layanan SIPAS", 
    "biaya layanan", "biaya uang kuliah", "layanan non-SIPAS", 
    "biaya per semester", "tarif layanan akademik", 
    "administrasi akademik", "biaya administrasi", "biaya layanan lainnya",
    "mata kuliah PGPAUD", "S-1 PGPAUD", "tugas tutorial", 
    "melibatkan anak didik", "tanpa anak didik", "bimbingan wajib", 
    "bimbingan mahasiswa", "kriteria layanan", "tuton mata kuliah", 
    "penyediaan layanan", "praktik wajib", "syarat praktik", 
    "penilaian", "praktik", "praktikum", "evaluasi praktik",
    "akreditasi internasional", "program sarjana", 
    "status akreditasi", "akreditasi nasional", "akreditasi diploma", 
    "profesi", "LAM", "status akreditasi profesi"]

    if any(keyword in question for keyword in table_related_keywords):
        formatted_tables = []
        for table in pdf_tables:
            formatted_table = "\n".join([" | ".join([str(cell) if cell else "" for cell in row]) for row in table])
            formatted_tables.append(formatted_table)

        # Combine all tables into one context
        context = "\n\n".join(formatted_tables)
        answer = query_openai(question, context)
        return jsonify({"answer": answer})

    # Default behavior for non-table-related questions
   
    answer = query_openai(question, context)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
