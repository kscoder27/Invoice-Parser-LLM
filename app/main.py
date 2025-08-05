import streamlit as st
from io import BytesIO
from dotenv import load_dotenv

from app.layout import set_page_config, display_header, display_results
from core.parser import parse_invoice

load_dotenv()

def main():
    set_page_config()
    display_header()

    with st.sidebar:
        st.header("Controls")
        
        uploaded_file = st.file_uploader(
            "Upload your invoice (PDF)",
            type="pdf",
            accept_multiple_files=False
        )

        default_prompt = "Extract the invoice number, the vendor's name, and the total amount."
        user_prompt = st.text_area(
            "Prompt",
            value=default_prompt,
            height=150,
            help="Clearly state what information you want to extract from the invoice."
        )

        extract_button = st.button("Extract Information", type="primary", use_container_width=True)

    if "result" not in st.session_state:
        st.session_state.result = {}

    if extract_button:
        if uploaded_file is not None:
            with st.spinner("Processing invoice... This may take a moment."):
                pdf_bytes = BytesIO(uploaded_file.getvalue())
                extraction_result = parse_invoice(pdf_file=pdf_bytes, user_prompt=user_prompt)
                st.session_state.result = extraction_result
        else:
            st.warning("Please upload a PDF file first.")
            st.session_state.result = {}

    if st.session_state.result:
        display_results(st.session_state.result)

if __name__ == "__main__":
    main()
