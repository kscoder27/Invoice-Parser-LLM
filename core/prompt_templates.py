"""
Pre-defined prompt templates for common invoice extraction scenarios.
This helps users get better results with standardized prompts.
"""

from typing import Dict, List

class PromptTemplates:
    """Collection of pre-defined prompt templates for invoice extraction."""
    
    # Basic extraction templates
    BASIC_TEMPLATES = {
        "essential_info": {
            "name": "Essential Information",
            "description": "Extract basic invoice details",
            "prompt": """Extract the following essential information from this invoice:
- Invoice number
- Invoice date
- Vendor/seller name
- Customer/buyer name  
- Total amount (including currency)
- Due date (if mentioned)

Format the response as a clean JSON object."""
        },
        
        "financial_summary": {
            "name": "Financial Summary",
            "description": "Extract all financial information",
            "prompt": """Extract all financial information from this invoice:
- Subtotal amount
- Tax amount (VAT/GST/Sales tax)
- Discount amount (if any)
- Total/Grand total amount
- Currency used
- Tax rate percentage (if mentioned)

Include currency symbols or codes where available."""
        },
        
        "contact_details": {
            "name": "Contact Information",
            "description": "Extract contact information for both parties",
            "prompt": """Extract contact information from this invoice:
- Vendor/Seller contact details (name, address, phone, email)
- Customer/Buyer contact details (name, address, phone, email)
- Tax registration numbers (GSTIN, VAT number, Tax ID)
- Any other identification numbers (PAN, IBAN, etc.)

Organize the information clearly for seller and buyer separately."""
        }
    }
    
    # Region-specific templates
    REGIONAL_TEMPLATES = {
        "indian_gst": {
            "name": "Indian GST Invoice",
            "description": "Extract GST-specific information",
            "prompt": """Extract the following information from this Indian GST invoice:
- Invoice number
- Invoice date
- GSTIN of supplier
- GSTIN of recipient (if available)
- Place of supply
- HSN/SAC codes
- Taxable value
- CGST amount and rate
- SGST amount and rate
- IGST amount and rate (if applicable)
- Total tax amount
- Total invoice value
- Vendor name and address
- Buyer name and address

Format as JSON with clear field names."""
        },
        
        "eu_vat": {
            "name": "EU VAT Invoice",
            "description": "Extract VAT-specific information",
            "prompt": """Extract the following information from this European VAT invoice:
- Invoice number
- Invoice date
- VAT number of supplier
- VAT number of customer (if available)
- Net amount
- VAT amount
- VAT rate percentage
- Gross amount
- Currency
- Supplier details (name, address)
- Customer details (name, address)
- Any IBAN or bank details

Format as JSON with appropriate field names."""
        },
        
        "us_sales_tax": {
            "name": "US Sales Tax Invoice",
            "description": "Extract US sales tax information",
            "prompt": """Extract the following information from this US invoice:
- Invoice number
- Invoice date
- Vendor name and address
- Customer name and address
- Subtotal amount
- Sales tax amount
- Sales tax rate
- Total amount
- Tax ID numbers (EIN, etc.)
- Payment terms
- Due date

Format as JSON with clear American business terminology."""
        }
    }
    
    # Item-level extraction templates
    DETAILED_TEMPLATES = {
        "line_items": {
            "name": "Line Items Detail",
            "description": "Extract detailed information about each item",
            "prompt": """Extract detailed line item information from this invoice:
- List each product/service as a separate item
- For each item include: description, quantity, unit price, total price
- Include any item-level discounts or taxes
- Extract product codes, SKUs, or HSN codes if available
- Note the unit of measurement (pieces, kg, hours, etc.)

Format as JSON with an array of items, each containing all available details."""
        },
        
        "payment_terms": {
            "name": "Payment Information",
            "description": "Extract payment-related information",
            "prompt": """Extract all payment-related information from this invoice:
- Payment terms (Net 30, Due on receipt, etc.)
- Due date
- Payment methods accepted
- Bank details (account number, routing number, IBAN, SWIFT code)
- Late payment penalties or fees
- Early payment discounts
- Payment status (if mentioned)

Format as JSON with clear payment terminology."""
        }
    }
    
    # Custom extraction helpers
    EXTRACTION_HELPERS = {
        "flexible_extraction": {
            "name": "Smart Extraction",
            "description": "Intelligent extraction based on available data",
            "prompt": """Analyze this invoice and extract all important information you can find. 
Include but don't limit yourself to:
- Basic invoice details (number, date, amounts)
- Party information (seller, buyer with contacts)
- Financial breakdown (taxes, discounts, totals)
- Payment information
- Item details if available
- Any regulatory or compliance information (tax numbers, etc.)

Organize the information logically in JSON format with descriptive field names. 
If certain information is not available, use null values."""
        }
    }
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict]:
        """Get all available templates organized by category."""
        return {
            "Basic Templates": cls.BASIC_TEMPLATES,
            "Regional Templates": cls.REGIONAL_TEMPLATES,
            "Detailed Templates": cls.DETAILED_TEMPLATES,
            "Helper Templates": cls.EXTRACTION_HELPERS
        }
    
    @classmethod
    def get_template_by_name(cls, template_name: str) -> str:
        """Get a specific template prompt by name."""
        all_templates = cls.get_all_templates()
        for category in all_templates.values():
            if template_name in category:
                return category[template_name]["prompt"]
        return None
    
    @classmethod
    def get_template_names(cls) -> List[str]:
        """Get list of all template names."""
        names = []
        all_templates = cls.get_all_templates()
        for category in all_templates.values():
            names.extend(category.keys())
        return names
    
    @classmethod
    def suggest_template(cls, user_prompt: str) -> str:
        """Suggest the best template based on user's prompt."""
        user_prompt_lower = user_prompt.lower()
        
        # Check for specific keywords
        if any(word in user_prompt_lower for word in ["gst", "gstin", "indian", "india"]):
            return "indian_gst"
        elif any(word in user_prompt_lower for word in ["vat", "european", "eu", "iban"]):
            return "eu_vat"
        elif any(word in user_prompt_lower for word in ["sales tax", "us", "american", "ein"]):
            return "us_sales_tax"
        elif any(word in user_prompt_lower for word in ["items", "products", "line items", "detailed"]):
            return "line_items"
        elif any(word in user_prompt_lower for word in ["payment", "bank", "due date", "terms"]):
            return "payment_terms"
        elif any(word in user_prompt_lower for word in ["contact", "address", "phone", "email"]):
            return "contact_details"
        elif any(word in user_prompt_lower for word in ["tax", "financial", "money", "amount"]):
            return "financial_summary"
        else:
            return "essential_info"

def get_enhanced_prompt(base_prompt: str, invoice_type: str = "general") -> str:
    """
    Enhance a user prompt with additional context and formatting instructions.
    
    Args:
        base_prompt: User's original prompt
        invoice_type: Type of invoice (general, gst, vat, etc.)
    
    Returns:
        Enhanced prompt with better instructions
    """
    enhancements = {
        "general": """
Additional Instructions:
- Be precise with numerical values and include currency symbols
- Use consistent date formats (YYYY-MM-DD preferred)
- If information is unclear or missing, use null instead of guessing
- Maintain original spelling for company names and addresses
""",
        "gst": """
Additional Instructions:
- Pay special attention to GST numbers (format: ##AAAAA####A#Z#)
- Extract HSN/SAC codes accurately
- Separate CGST, SGST, and IGST amounts clearly
- Include place of supply information
""",
        "vat": """
Additional Instructions:
- Extract VAT numbers in their complete format
- Note the VAT rate percentages precisely
- Include any reverse charge mentions
- Extract IBAN/SWIFT codes if present
"""
    }
    
    enhancement = enhancements.get(invoice_type, enhancements["general"])
    return f"{base_prompt}\n{enhancement}"