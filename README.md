# 🧾 AI-Powered Invoice Parser

A modular Python application that leverages **Large Language Models (LLMs)** like **LLaMA 2** to extract structured data from PDF invoices. It features a user-friendly **Streamlit** web interface and supports **custom prompt-based extraction**, **Pydantic validation**, and **multi-invoice parsing**.

---

## 📁 Project Structure

<pre lang="markdown"> ```bash Invoice-Parser-LLM/ ├── app/ # Streamlit UI components │ ├── main.py # App launcher │ └── layout.py # Streamlit UI layout ├── core/ # Core logic │ ├── parser.py # PDF parsing & text extraction │ ├── prompt_templates.py # LLM prompt templates │ └── validator.py # Data validation with Pydantic ├── models/ # LLM integration │ └── llama_model.py # Load & run LLaMA from Hugging Face ├── data/sample_invoices/ # Sample invoice PDFs ├── outputs/extracted_data/ # Parsed JSON outputs ├── tests/test_parser.py # Unit tests ├── requirements.txt # Dependencies ├── .env # API keys / tokens └── README.md # Project overview ``` </pre>

---

## 🚀 Features

- 📄 **PDF Invoice Upload** – Upload invoices via a web interface.
- 💬 **Custom Prompting** – Use natural language to define extraction logic.
- 🧠 **LLM Integration** – Built with LLaMA 2 and Hugging Face transformers.
- 📦 **Structured Output** – Data returned in validated JSON format.
- ✅ **Data Validation** – Uses Pydantic to ensure schema correctness.
- 🧩 **Modular Codebase** – Scalable and easy to maintain.

---

## ⚙️ Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Invoice-Parser-LLM.git
```
### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4.Authenticate with Hugging Face
Request Access: LLaMA-2 on Hugging Face

Login via CLI:
```bash
huggingface-cli login
```
▶️ How to Run the App
Ensure you're in the project root and your virtual environment is active
```bash
python -m streamlit run app/main.py
```

