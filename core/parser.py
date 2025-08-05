import PyPDF2
import json
import logging
import re
from io import BytesIO
from typing import Dict, Any, Optional, List, Tuple
from .validator import validate_extraction
from models.llama_model import LlamaModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvoiceParser:
    def __init__(self):
        self.llama_model = LlamaModel()
        
        # Enhanced field mapping for better extraction - MORE SPECIFIC KEYWORDS
        self.field_keywords = {
            'invoice_number': ['invoice number', 'invoice #', 'invoice id', 'invoice no', 'inv no', 'inv #'],
            'vendor_name': ['vendor name', 'vendor', 'supplier', 'company name', 'seller', 'from', 'sold by'],
            'customer_name': ['customer name', 'customer', 'client', 'buyer', 'bill to', 'sold to'],
            'total_amount': ['total amount', 'final total', 'grand total', 'amount due', 'final amount', 'net payable', 'amount payable', 'gross worth', 'gross total'],
            'date': ['date', 'invoice date', 'issue date', 'created date'],
            'due_date': ['due date', 'payment due', 'due by'],
            'tax': ['tax', 'vat', 'gst', 'sales tax', 'igst', 'cgst', 'sgst'],
            'taxable_value': ['taxable value', 'taxable amount', 'net worth', 'net amount'],
            'subtotal': ['subtotal', 'sub total'],
            'items': ['items', 'products', 'line items', 'goods', 'services'],
            'address': ['address', 'billing address', 'shipping address'],
            'phone': ['phone', 'telephone', 'contact', 'tel'],
            'email': ['email', 'e-mail', 'electronic mail'],
            'po_number': ['po number', 'purchase order', 'po #'],
            'discount': ['discount', 'reduction'],
            'currency': ['currency', 'curr']
        }

    def extract_text_from_pdf(self, pdf_file: BytesIO) -> str:
        """Extract text content from PDF file with improved handling."""
        try:
            pdf_file.seek(0)  # Ensure we're at the beginning of the file
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                try:
                    pdf_reader.decrypt("")  # Try empty password first
                except:
                    raise Exception("PDF is password protected and cannot be read")
            
            if len(pdf_reader.pages) == 0:
                raise Exception("PDF contains no pages")
            
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"--- Page {page_num + 1} ---\n{page_text}\n"
                except Exception as page_error:
                    logger.warning(f"Could not extract text from page {page_num + 1}: {str(page_error)}")
                    continue
            
            if not text_content.strip():
                raise Exception("No readable text found in PDF")
            
            return self.clean_extracted_text(text_content)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Replace multiple newlines with double newline
        text = re.sub(r' +', ' ', text)  # Replace multiple spaces with single space
        text = text.strip()
        
        # Remove common PDF artifacts
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)  # Remove control characters
        
        return text

    def analyze_user_request(self, user_prompt: str) -> Dict[str, Any]:
        """Analyze user prompt to understand what they're asking for."""
        user_prompt_lower = user_prompt.lower()
        
        analysis = {
            'requested_fields': [],
            'is_specific_request': False,
            'extraction_type': 'general'  # 'specific', 'general', 'all'
        }
        
        # Check for specific field requests
        for field_type, keywords in self.field_keywords.items():
            if any(keyword in user_prompt_lower for keyword in keywords):
                analysis['requested_fields'].append(field_type)
        
        # Special handling for "total cost" vs "total amount" - prioritize final total
        if any(term in user_prompt_lower for term in ['total cost', 'total amount', 'total', 'final total']):
            if 'total_amount' not in analysis['requested_fields']:
                analysis['requested_fields'].append('total_amount')
        
        # Determine if it's a specific or general request
        specific_indicators = ['only', 'just', 'extract', 'find', 'get', 'what is']
        if any(indicator in user_prompt_lower for indicator in specific_indicators):
            analysis['is_specific_request'] = True
            analysis['extraction_type'] = 'specific'
        
        # Check for "all" or comprehensive requests
        all_indicators = ['all', 'everything', 'complete', 'full', 'entire']
        if any(indicator in user_prompt_lower for indicator in all_indicators):
            analysis['extraction_type'] = 'all'
        
        # If no specific fields detected but it's a short prompt, assume specific
        if not analysis['requested_fields'] and len(user_prompt.split()) <= 5:
            analysis['is_specific_request'] = True
            analysis['extraction_type'] = 'specific'
        
        return analysis

    def create_extraction_prompt(self, invoice_text: str, user_prompt: str) -> str:
        """Create a structured prompt for the LLM with improved context."""
        
        # Analyze the user request
        request_analysis = self.analyze_user_request(user_prompt)
        
        # Create context-aware instructions
        if request_analysis['extraction_type'] == 'specific':
            extraction_instruction = """
CRITICAL INSTRUCTIONS:
1. Extract ONLY the specific information requested by the user
2. Do NOT extract any additional information that was not specifically asked for
3. Use the exact terminology from the user's request when creating field names
4. If the requested information is not found, use null as the value
5. Return a minimal JSON object containing only the requested fields
6. Be precise and focused - no extra fields

IMPORTANT FOR AMOUNT FIELDS - CRITICAL DISTINCTION:
- If user asks for "total cost", "total amount", or "total", find the FINAL PAYABLE AMOUNT
- This is the amount AFTER all taxes are added (highest amount)
- Look for labels like "Total", "Grand Total", "Gross Total", "Gross Worth", "Amount Due", "Final Amount"
- DO NOT confuse with:
  * "Net Worth" or "Net Amount" (this is BEFORE taxes)
  * "Taxable Value" or "Taxable Amount" (this is BEFORE taxes)
  * "Subtotal" (this is BEFORE taxes)
- The final total is typically in the bottom section of the invoice and includes VAT/taxes
- Example: If Net Worth = $192.81 and VAT = $19.28, then Total/Gross Worth = $212.09
- ALWAYS choose the higher amount that includes taxes"""
        
        elif request_analysis['extraction_type'] == 'all':
            extraction_instruction = """
CRITICAL INSTRUCTIONS:
1. Extract ALL available information from the invoice
2. Include all standard invoice fields: invoice_number, vendor_name, customer_name, total_amount, date, items, etc.
3. Use standardized field names for consistency
4. If any information is not found, use null as the value
5. Be comprehensive and thorough

IMPORTANT FOR AMOUNT FIELDS - CRITICAL DISTINCTION:
- total_amount should be the FINAL PAYABLE AMOUNT (AFTER all taxes - highest amount)
- taxable_value/net_worth should be the amount BEFORE taxes (lower amount)
- subtotal should be the sum before taxes and discounts
- Clearly distinguish between these different amount types
- Always prioritize the amount that includes all taxes and charges for total_amount"""
        
        else:  # general
            extraction_instruction = """
CRITICAL INSTRUCTIONS:
1. Extract the key information requested by the user
2. Focus on the main invoice details that address the user's request
3. Use clear, descriptive field names
4. If information is not found, use null as the value
5. Balance completeness with relevance to the user's request

IMPORTANT FOR AMOUNT FIELDS - CRITICAL DISTINCTION:
- When extracting amounts, prioritize the FINAL TOTAL PAYABLE AMOUNT
- This is the amount AFTER taxes (highest amount on the invoice)
- Look for "Total", "Grand Total", "Gross Total", "Gross Worth"
- Do NOT use "Net Worth", "Net Amount", or "Taxable Value" as the total
- Include all taxes and charges in the total amount"""

        prompt = f"""You are an AI assistant specialized in extracting information from invoices.
Your task is to analyze the following invoice text and extract the information as requested by the user.

INVOICE TEXT:
{invoice_text}

USER REQUEST:
{user_prompt}

{extraction_instruction}

RESPONSE RULES:
- Return ONLY a valid JSON object
- Keep field names simple and descriptive
- Use consistent data types (strings for text, numbers for amounts, etc.)
- Do not include any explanatory text before or after the JSON
- Ensure the JSON is properly formatted and valid
- For amount fields, use numeric values without currency symbols

JSON Response:"""
        
        return prompt

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and clean the LLM response to extract JSON with better error handling."""
        if not response or not response.strip():
            raise Exception("Empty response from LLM")
        
        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                # Handle case where it might be ```\n{json}\n```
                parts = cleaned_response.split("```")
                if len(parts) >= 3:
                    cleaned_response = parts[1].strip()
                else:
                    cleaned_response = parts[-1].strip()
            
            # Remove any leading/trailing text that's not JSON
            lines = cleaned_response.split('\n')
            json_lines = []
            in_json = False
            brace_count = 0
            
            for line in lines:
                if '{' in line and not in_json:
                    in_json = True
                
                if in_json:
                    json_lines.append(line)
                    brace_count += line.count('{') - line.count('}')
                    
                    if brace_count == 0 and '}' in line:
                        break
            
            if json_lines:
                json_str = '\n'.join(json_lines)
            else:
                # Fallback: try to find JSON object boundaries
                start_idx = cleaned_response.find('{')
                end_idx = cleaned_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = cleaned_response[start_idx:end_idx]
                else:
                    json_str = cleaned_response
            
            # Parse JSON
            parsed_data = json.loads(json_str)
            
            # Validate that we got a dictionary
            if not isinstance(parsed_data, dict):
                raise Exception("LLM response is not a JSON object")
            
            return parsed_data
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Cleaned response: {cleaned_response}")
            
            # Try to fix common JSON issues
            try:
                fixed_json = self.fix_common_json_issues(cleaned_response)
                return json.loads(fixed_json)
            except:
                raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            raise Exception(f"Failed to parse LLM response: {str(e)}")

    def fix_common_json_issues(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues."""
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix single quotes to double quotes
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
        
        # Fix unquoted keys
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        return json_str

    def filter_extracted_data(self, extracted_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Filter extracted data to include only fields mentioned in the user prompt."""
        request_analysis = self.analyze_user_request(user_prompt)
        
        # If it's an "all" request, return everything
        if request_analysis['extraction_type'] == 'all':
            return extracted_data
        
        # If no specific fields were identified and it's not a specific request, return as-is
        if not request_analysis['requested_fields'] and not request_analysis['is_specific_request']:
            return extracted_data
        
        user_prompt_lower = user_prompt.lower()
        filtered_data = {}
        
        # Special handling for total cost/amount requests - IMPROVED LOGIC
        if any(term in user_prompt_lower for term in ['total cost', 'total amount', 'total']):
            # Priority order for total amount fields (highest priority first)
            total_priority = [
                'gross_total', 'gross_worth', 'final_total', 'grand_total', 
                'total_amount', 'amount_due', 'total', 'final_amount'
            ]
            
            # Find the best total field
            best_total_field = None
            best_total_value = None
            
            for key, value in extracted_data.items():
                key_lower = key.lower()
                
                # Skip non-total fields
                if any(avoid in key_lower for avoid in ['taxable', 'net_worth', 'net_amount', 'subtotal']):
                    continue
                
                # Check if this is a total field
                for priority_field in total_priority:
                    if priority_field in key_lower:
                        if best_total_field is None:
                            best_total_field = key
                            best_total_value = value
                        break
                
                # Also check for generic "total" if no specific match found
                if best_total_field is None and 'total' in key_lower:
                    best_total_field = key
                    best_total_value = value
            
            if best_total_field:
                filtered_data[best_total_field] = best_total_value
        
        # First, include fields that match the identified requested fields
        for key, value in extracted_data.items():
            key_lower = key.lower().replace('_', ' ').replace('-', ' ')
            include_field = False
            
            # Check against identified field types
            for field_type in request_analysis['requested_fields']:
                field_keywords_for_type = self.field_keywords.get(field_type, [])
                if any(keyword in key_lower for keyword in field_keywords_for_type):
                    include_field = True
                    break
            
            # Also check for direct word matches in the prompt
            prompt_words = [word for word in user_prompt_lower.split() if len(word) > 3]
            for word in prompt_words:
                if word in key_lower or any(word in keyword for keyword in key_lower.split()):
                    include_field = True
                    break
            
            if include_field:
                filtered_data[key] = value
        
        # If filtering resulted in empty data but we extracted something, be more lenient
        if not filtered_data and extracted_data:
            # For very specific requests (short prompts), return the most relevant field
            if len(user_prompt.split()) <= 3:
                # Return the first non-null field as it's likely what they want
                for key, value in extracted_data.items():
                    if value is not None:
                        filtered_data[key] = value
                        break
            else:
                logger.warning("Filtering resulted in no data, returning original extraction")
                return extracted_data
        
        return filtered_data if filtered_data else extracted_data

    def post_process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process extracted data for consistency and formatting."""
        processed_data = {}
        
        for key, value in data.items():
            # Clean up the key
            clean_key = key.strip().lower().replace(' ', '_').replace('-', '_')
            
            # Clean up the value
            if isinstance(value, str):
                # Remove extra whitespace
                value = value.strip()
                # Handle empty strings
                if not value or value.lower() in ['n/a', 'na', 'none', 'null']:
                    value = None
                # Try to convert numeric strings to numbers for amount fields
                elif any(amount_key in clean_key for amount_key in ['amount', 'total', 'price', 'cost', 'tax']):
                    # Remove currency symbols and commas
                    numeric_value = re.sub(r'[^\d.-]', '', value)
                    try:
                        if '.' in numeric_value:
                            value = float(numeric_value)
                        else:
                            value = int(numeric_value) if numeric_value else None
                    except ValueError:
                        pass  # Keep as string if conversion fails
            
            processed_data[clean_key] = value
        
        return processed_data

def parse_invoice(pdf_file: BytesIO, user_prompt: str) -> Dict[str, Any]:
    """Main function to parse invoice and extract information."""
    llm_response = None
    
    try:
        parser = InvoiceParser()
        
        # Validate inputs
        if not pdf_file:
            return {
                "success": False,
                "error": "No PDF file provided"
            }
        
        if not user_prompt or not user_prompt.strip():
            return {
                "success": False,
                "error": "No user prompt provided"
            }
        
        # Extract text from PDF
        logger.info("Extracting text from PDF...")
        invoice_text = parser.extract_text_from_pdf(pdf_file)
        
        if not invoice_text.strip():
            return {
                "success": False,
                "error": "No text could be extracted from the PDF file"
            }
        
        # Create extraction prompt
        logger.info("Creating extraction prompt...")
        prompt = parser.create_extraction_prompt(invoice_text, user_prompt)
        
        # Get response from LLM
        logger.info("Querying LLM for extraction...")
        llm_response = parser.llama_model.generate_response(prompt)
        
        if not llm_response:
            return {
                "success": False,
                "error": "No response received from LLM",
                "raw_output": None
            }
        
        # Parse the response
        logger.info("Parsing LLM response...")
        extracted_data = parser.parse_llm_response(llm_response)
        
        # Filter data to include only requested fields
        logger.info("Filtering extracted data to match user request...")
        filtered_data = parser.filter_extracted_data(extracted_data, user_prompt)
        
        # Post-process the data
        logger.info("Post-processing extracted data...")
        processed_data = parser.post_process_data(filtered_data)
        
        # Validate the extracted data
        logger.info("Validating extracted data...")
        validation_result = validate_extraction(processed_data, user_prompt)
        
        return {
            "success": True,
            "data": processed_data,
            "validation": validation_result,
            "raw_output": llm_response,
            "extracted_text_length": len(invoice_text),
            "fields_extracted": len(processed_data)
        }
        
    except Exception as e:
        logger.error(f"Error in parse_invoice: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "raw_output": llm_response,
            "fields_extracted": 0
        }