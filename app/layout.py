import streamlit as st
import json
from core.prompt_templates import PromptTemplates

def set_page_config():
    st.set_page_config(
        page_title="AI-Powered Invoice Parser",
        page_icon="📄",
        layout="centered"
    )

def display_header():
    st.title("📄 AI-Powered Invoice Parser")
    st.markdown(
        "Upload a PDF invoice, provide a prompt specifying what information you need, "
        "and let the AI extract the data for you."
    )

def display_template_selector():
    """Display template selector in sidebar."""
    st.subheader("Quick Templates")
    
    # Get all templates
    all_templates = PromptTemplates.get_all_templates()
    
    # Create selectbox for templates
    template_options = ["Custom Prompt"]
    template_mapping = {}
    
    for category_name, templates in all_templates.items():
        for template_key, template_info in templates.items():
            display_name = f"{category_name}: {template_info['name']}"
            template_options.append(display_name)
            template_mapping[display_name] = template_key
    
    selected_template = st.selectbox(
        "Choose a template or use custom prompt:",
        options=template_options,
        help="Select a pre-defined template for common extraction scenarios"
    )
    
    if selected_template != "Custom Prompt":
        template_key = template_mapping[selected_template]
        template_prompt = PromptTemplates.get_template_by_name(template_key)
        
        # Show template description
        for templates in all_templates.values():
            if template_key in templates:
                st.info(f"📝 {templates[template_key]['description']}")
                break
        
        return template_prompt
    
    return None

def display_results(result):
    st.subheader("Extraction Results")
    if result.get("success"):
        st.success("Data extracted and validated successfully!")
        
        # Display validation summary if available
        if "validation" in result:
            validation = result["validation"]
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Fields Extracted", validation.get("summary", {}).get("total_fields", 0))
            with col2:
                st.metric("Valid Fields", validation.get("summary", {}).get("valid_fields", 0))
            with col3:
                error_count = validation.get("summary", {}).get("error_count", 0)
                st.metric("Errors", error_count, delta_color="inverse")
            
            # Show warnings if any
            if validation.get("warnings"):
                st.warning("⚠️ Validation Warnings:")
                for warning in validation["warnings"]:
                    st.write(f"• {warning}")
            
            # Show errors if any
            if validation.get("errors"):
                st.error("❌ Validation Errors:")
                for error in validation["errors"]:
                    st.write(f"• {error}")
        
        # Display the extracted data
        st.subheader("Extracted Data")
        st.json(result.get("data", {}))
        
        # Provide download options
        col1, col2 = st.columns(2)
        
        with col1:
            # Download JSON
            json_string = json.dumps(result.get("data", {}), indent=4)
            st.download_button(
                label="📥 Download as JSON",
                file_name="extracted_data.json",
                mime="application/json",
                data=json_string,
                use_container_width=True
            )
        
        with col2:
            # Download full report including validation
            full_report = {
                "extracted_data": result.get("data", {}),
                "validation_report": result.get("validation", {}),
                "extraction_timestamp": st.session_state.get("extraction_time", "")
            }
            report_string = json.dumps(full_report, indent=4)
            st.download_button(
                label="📊 Download Full Report",
                file_name="extraction_report.json",
                mime="application/json",
                data=report_string,
                use_container_width=True
            )
        
        # Show raw LLM output in expander for debugging
        if "raw_output" in result:
            with st.expander("🔍 View Raw LLM Output (Debug)"):
                st.code(result.get("raw_output"), language="text")
                
    elif result.get("error"):
        st.error(f"An error occurred: {result.get('error')}")
        
        # If there's raw output from the LLM, display it for debugging
        if "raw_output" in result:
            st.subheader("Raw LLM Output (for debugging)")
            st.code(result.get("raw_output"), language="text")

def display_invoice_examples():
    """Display example invoices that the system can handle."""
    with st.expander("📋 Supported Invoice Types & Examples"):
        st.markdown("""
        **This system can handle various invoice formats:**
        
        🇮🇳 **Indian GST Invoices**
        - GSTIN numbers, HSN codes
        - CGST, SGST, IGST breakdowns
        - Place of supply information
        
        🇪🇺 **European VAT Invoices**  
        - VAT numbers and rates
        - IBAN/SWIFT bank details
        - Multi-currency support
        
        🇺🇸 **US Sales Tax Invoices**
        - EIN numbers
        - State sales tax calculations
        - Payment terms and conditions
        
        📦 **E-commerce Invoices**
        - Flipkart, Amazon, eBay format
        - Order IDs and tracking numbers
        - Shipping and handling charges
        
        **Tips for better extraction:**
        - Use clear, specific prompts
        - Try the pre-defined templates
        - Upload high-quality PDF files
        - Specify exactly what fields you need
        """)

def display_sidebar_content():
    """Display all sidebar content including controls and templates."""
    st.header("🎛️ Controls")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload your invoice (PDF)",
        type="pdf",
        accept_multiple_files=False,
        help="Upload a PDF invoice file. Supported formats: PDF only"
    )
    
    # Template selector
    template_prompt = display_template_selector()
    
    # Prompt input
    default_prompt = template_prompt or "Extract the invoice number, the vendor's name, and the total amount."
    user_prompt = st.text_area(
        "Extraction Prompt",
        value=default_prompt,
        height=150,
        help="Clearly state what information you want to extract from the invoice. Be specific for better results."
    )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        temperature = st.slider(
            "Model Temperature", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.1, 
            step=0.1,
            help="Lower values make output more focused and deterministic"
        )
        
        max_tokens = st.slider(
            "Max Response Tokens",
            min_value=256,
            max_value=2048,
            value=1024,
            step=128,
            help="Maximum length of the model's response"
        )
    
    # Extract button
    extract_button = st.button(
        "🚀 Extract Information", 
        type="primary", 
        use_container_width=True,
        help="Click to start extracting information from the uploaded invoice"
    )
    
    return uploaded_file, user_prompt, extract_button, {"temperature": temperature, "max_tokens": max_tokens}