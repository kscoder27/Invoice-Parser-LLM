AI-Powered Invoice Parser
This project is a Python application that uses a Large Language Model (LLM) like LLaMA 2 to extract structured data from PDF invoices. It provides a simple web interface built with Streamlit for uploading invoices and specifying extraction requirements via custom prompts.

Project Directory Structure
Here is the complete layout of the project, designed for clarity and scalability.

invoice_parser_project/
├── app/
│   ├── __init__.py
│   ├── main.py             # Streamlit app launcher
│   └── layout.py           # UI components (Streamlit widgets)
│
├── core/
│   ├── __init__.py
│   ├── parser.py           # Invoice text extraction & parsing logic
│   ├── prompt_templates.py # Prompt templates for the LLM
│   └── validator.py        # Pydantic models for data validation
│
├── models/
│   ├── __init__.py
│   └── llama_model.py      # Load & run the LLM from Hugging Face
│
├── data/
│   └── sample_invoices/    # Place your test PDF files here
│
├── outputs/
│   └── extracted_data/     # Stores JSON output from successful runs
│
├── tests/
│   ├── __init__.py
│   └── test_parser.py      # Unit tests for the parser
│
├── requirements.txt        # Project dependencies
├── README.md               # This file
└── .env                    # Environment variables (e.g., Hugging Face Token)

Features
PDF Invoice Upload: Easily upload invoices through a web interface.

Custom Prompting: Use natural language to specify what data you want to extract.

LLM Integration: Powered by state-of-the-art models like LLaMA 2 for accurate data extraction.

Structured Output: The LLM returns data in a validated JSON format.

Data Validation: Extracted data is validated using Pydantic models to ensure quality and structure.

Modular Design: A clean, organized codebase that is easy to maintain and extend.

Setup & Installation
1. Clone the Repository:

git clone <your-repo-url>
cd invoice_parser_project

2. Create a Virtual Environment:

It's highly recommended to use a virtual environment to manage dependencies.

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

3. Install Dependencies:

Install all the necessary packages from the requirements.txt file.

pip install -r requirements.txt

4. Log in to Hugging Face:

To download gated models like LLaMA 2, you first need to request access on the model's Hugging Face page and then log in via your terminal.

Request Access: Visit the Llama-2-7b-chat-hf page and agree to the terms to get access. You will receive an email upon approval.

Log In: Once access is granted, run the following command in your terminal and paste your Hugging Face read token when prompted.

huggingface-cli login

How to Run the Application
Ensure you are in the project's root directory and your virtual environment is active. Use the python -m flag to ensure all modules are found correctly.

python -m streamlit run app/main.py

Open your web browser and navigate to the local URL provided by Streamlit (usually http://localhost:8501).

The first time you run this, it will download the LLM, which can take a significant amount of time and disk space.

Once loaded, upload a PDF invoice, provide a prompt, and click "Extract Information".

How to Run Tests
To ensure the core components are working correctly, you can run the provided tests using pytest.

pytest