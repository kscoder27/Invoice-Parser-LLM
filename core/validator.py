import re
import json
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """Validator class for extracted invoice data."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email:
            return True  # Allow null/empty emails
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return True  # Allow null/empty phones
        # Remove common formatting characters
        cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', str(phone))
        # Check if it contains only digits and is reasonable length
        return cleaned_phone.isdigit() and 7 <= len(cleaned_phone) <= 15
    
    @staticmethod
    def validate_amount(amount: Any) -> bool:
        """Validate monetary amount."""
        if amount is None:
            return True  # Allow null amounts
        
        try:
            # Handle string amounts with currency symbols
            if isinstance(amount, str):
                # Remove currency symbols and whitespace
                cleaned_amount = re.sub(r'[^\d\.\-,]', '', amount)
                if not cleaned_amount:
                    return True  # Empty string after cleaning
                # Replace comma with dot for decimal
                cleaned_amount = cleaned_amount.replace(',', '.')
                float(cleaned_amount)
            else:
                float(amount)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate date format."""
        if not date_str:
            return True  # Allow null/empty dates
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',      # 2023-12-25
            '%d/%m/%Y',      # 25/12/2023
            '%m/%d/%Y',      # 12/25/2023
            '%d-%m-%Y',      # 25-12-2023
            '%m-%d-%Y',      # 12-25-2023
            '%d.%m.%Y',      # 25.12.2023
            '%B %d, %Y',     # December 25, 2023
            '%b %d, %Y',     # Dec 25, 2023
            '%d-%m-%Y',      # 25-01-2019
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(str(date_str), fmt)
                return True
            except ValueError:
                continue
        return False
    
    @staticmethod
    def validate_invoice_number(invoice_number: str) -> bool:
        """Validate invoice number format."""
        if not invoice_number:
            return True  # Allow null/empty invoice numbers
        
        # Basic validation - should contain alphanumeric characters
        return bool(re.match(r'^[a-zA-Z0-9\-_/#]+$', str(invoice_number)))
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], user_prompt: str) -> List[str]:
        """Check if commonly required fields are present based on user prompt."""
        missing_fields = []
        prompt_lower = user_prompt.lower()
        
        # Enhanced field mappings with better total amount detection
        field_keywords = {
            'invoice_number': ['invoice number', 'invoice #', 'invoice id'],
            'total_amount': ['total', 'amount', 'total amount', 'grand total', 'final total', 'total cost', 'gross total', 'gross worth'],
            'vendor_name': ['vendor', 'supplier', 'company', 'from', 'sold by'],
            'date': ['date', 'invoice date', 'due date'],
            'customer_name': ['customer', 'client', 'to', 'bill to']
        }
        
        # Check if specific fields are mentioned in prompt but missing in data
        for field, keywords in field_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                # Look for this field in the extracted data (case insensitive)
                found = False
                for key in data.keys():
                    key_lower = key.lower()
                    if field == 'total_amount':
                        # Special handling for total amount - prefer final total over taxable value
                        if any(keyword.replace(' ', '_') in key_lower for keyword in keywords):
                            # Prioritize fields that are NOT taxable/net values
                            if not any(avoid in key_lower for avoid in ['taxable', 'net_worth', 'net_amount']):
                                found = True
                                break
                    else:
                        if any(keyword.replace(' ', '_') in key_lower for keyword in keywords):
                            found = True
                            break
                
                if not found:
                    missing_fields.append(field)
        
        return missing_fields

    @staticmethod
    def validate_total_amount_accuracy(data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Validate if the extracted total amount seems correct and is truly the final total."""
        validation_result = {"valid": True, "warnings": [], "recommendations": []}
        
        prompt_lower = user_prompt.lower()
        if not any(term in prompt_lower for term in ['total', 'amount', 'cost']):
            return validation_result
        
        # Categorize amount fields
        total_fields = {}
        taxable_fields = {}
        other_amount_fields = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            if any(term in key_lower for term in ['amount', 'total', 'cost', 'price', 'worth']):
                try:
                    # Convert to float for comparison
                    if isinstance(value, str):
                        numeric_value = float(re.sub(r'[^\d.-]', '', value))
                    else:
                        numeric_value = float(value)
                    
                    # Categorize the field
                    if any(term in key_lower for term in ['taxable', 'net_worth', 'net_amount']):
                        taxable_fields[key] = numeric_value
                    elif any(term in key_lower for term in ['total', 'grand', 'final', 'gross_worth', 'gross_total']):
                        total_fields[key] = numeric_value
                    else:
                        other_amount_fields[key] = numeric_value
                        
                except (ValueError, TypeError):
                    continue
        
        # Check if we have the right total
        if total_fields and taxable_fields:
            max_total = max(total_fields.values())
            max_taxable = max(taxable_fields.values())
            
            # The total should be higher than or equal to taxable value
            if max_taxable > max_total:
                validation_result["warnings"].append(
                    f"ERROR: Extracted 'total' ({max_total}) is less than taxable value ({max_taxable}). "
                    f"This suggests the wrong amount was extracted as 'total'."
                )
                validation_result["valid"] = False
                validation_result["recommendations"].append(
                    "The system may have extracted 'Net Worth' or 'Taxable Value' instead of 'Gross Total'. "
                    "Look for the final amount that includes all taxes."
                )
            elif max_taxable == max_total:
                validation_result["warnings"].append(
                    f"Warning: Total amount ({max_total}) equals taxable value. "
                    f"Check if taxes are included in the total."
                )
        
        # If only one type of amount field exists, provide guidance
        elif taxable_fields and not total_fields:
            validation_result["warnings"].append(
                "Only taxable/net amounts found. The final total (including taxes) may be missing."
            )
            validation_result["recommendations"].append(
                "Look for 'Gross Total', 'Grand Total', or 'Final Amount' which includes all taxes."
            )
        
        # Check for suspicious amounts (common error patterns)
        all_amounts = {**total_fields, **taxable_fields, **other_amount_fields}
        if len(all_amounts) > 1:
            amounts_list = list(all_amounts.values())
            amounts_list.sort(reverse=True)
            
            # If the difference between highest and second highest is exactly 10% or common tax rates
            if len(amounts_list) >= 2:
                highest = amounts_list[0]
                second_highest = amounts_list[1]
                difference_percent = ((highest - second_highest) / second_highest) * 100
                
                # Common tax rates: 10%, 15%, 18%, 20%, 25%
                common_tax_rates = [10, 15, 18, 20, 25]
                
                if any(abs(difference_percent - rate) < 1 for rate in common_tax_rates):
                    validation_result["recommendations"].append(
                        f"The amounts suggest a {difference_percent:.1f}% tax rate. "
                        f"Ensure the higher amount ({highest}) is extracted as the total."
                    )
        
        return validation_result


def validate_extraction(extracted_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
    """Main validation function for extracted invoice data."""
    validator = DataValidator()
    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "field_validations": {}
    }
    
    try:
        # Check if data is empty
        if not extracted_data:
            validation_results["is_valid"] = False
            validation_results["errors"].append("No data extracted from invoice")
            return validation_results
        
        # Validate total amount accuracy if relevant - ENHANCED
        total_validation = validator.validate_total_amount_accuracy(extracted_data, user_prompt)
        validation_results["warnings"].extend(total_validation["warnings"])
        validation_results["recommendations"].extend(total_validation.get("recommendations", []))
        if not total_validation["valid"]:
            validation_results["is_valid"] = False
        
        # Validate individual fields
        for field_name, field_value in extracted_data.items():
            field_validation = {"valid": True, "message": ""}
            
            # Skip null values
            if field_value is None:
                field_validation["message"] = "Field is null"
                validation_results["field_validations"][field_name] = field_validation
                continue
            
            field_name_lower = field_name.lower()
            
            # Email validation
            if 'email' in field_name_lower:
                if not validator.validate_email(field_value):
                    field_validation["valid"] = False
                    field_validation["message"] = "Invalid email format"
                    validation_results["errors"].append(f"Invalid email format for {field_name}")
            
            # Phone validation
            elif 'phone' in field_name_lower or 'tel' in field_name_lower:
                if not validator.validate_phone(field_value):
                    field_validation["valid"] = False
                    field_validation["message"] = "Invalid phone format"
                    validation_results["warnings"].append(f"Questionable phone format for {field_name}")
            
            # Amount validation with enhanced total amount checking
            elif any(keyword in field_name_lower for keyword in ['amount', 'total', 'price', 'cost', 'subtotal', 'tax', 'worth']):
                if not validator.validate_amount(field_value):
                    field_validation["valid"] = False
                    field_validation["message"] = "Invalid amount format"
                    validation_results["errors"].append(f"Invalid amount format for {field_name}")
                else:
                    # Enhanced check for total amount accuracy
                    try:
                        numeric_value = float(field_value) if isinstance(field_value, (int, float)) else float(re.sub(r'[^\d.-]', '', str(field_value)))
                        
                        # Enhanced warning for total amount requests
                        if any(term in user_prompt.lower() for term in ['total', 'total amount', 'total cost']):
                            # Check if this looks like a pre-tax amount when user asked for total
                            if any(pre_tax_indicator in field_name_lower for pre_tax_indicator in ['taxable', 'net_worth', 'net_amount']):
                                validation_results["errors"].append(
                                    f"CRITICAL ERROR: '{field_name}' appears to be a pre-tax amount (${numeric_value}), "
                                    f"but user requested total amount. Look for 'Gross Total' or 'Grand Total' instead."
                                )
                                validation_results["is_valid"] = False
                            
                            # Check if this is the right type of total
                            elif any(total_indicator in field_name_lower for total_indicator in ['total', 'grand', 'final', 'gross']):
                                field_validation["message"] = f"Correctly identified as final total: ${numeric_value}"
                        
                    except (ValueError, TypeError):
                        pass
            
            # Date validation
            elif 'date' in field_name_lower:
                if not validator.validate_date(field_value):
                    field_validation["valid"] = False
                    field_validation["message"] = "Invalid date format"
                    validation_results["warnings"].append(f"Questionable date format for {field_name}")
            
            # Invoice number validation
            elif 'invoice' in field_name_lower and 'number' in field_name_lower:
                if not validator.validate_invoice_number(field_value):
                    field_validation["valid"] = False
                    field_validation["message"] = "Invalid invoice number format"
                    validation_results["warnings"].append(f"Questionable invoice number format for {field_name}")
            
            validation_results["field_validations"][field_name] = field_validation
        
        # Check for missing required fields
        missing_fields = validator.validate_required_fields(extracted_data, user_prompt)
        if missing_fields:
            validation_results["warnings"].extend([f"Possibly missing field: {field}" for field in missing_fields])
        
        # Set overall validation status
        if validation_results["errors"]:
            validation_results["is_valid"] = False
        
        # Add summary
        validation_results["summary"] = {
            "total_fields": len(extracted_data),
            "valid_fields": len([v for v in validation_results["field_validations"].values() if v["valid"]]),
            "error_count": len(validation_results["errors"]),
            "warning_count": len(validation_results["warnings"]),
            "recommendation_count": len(validation_results["recommendations"])
        }
        
        logger.info(f"Validation completed: {validation_results['summary']}")
        
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        validation_results["is_valid"] = False
        validation_results["errors"].append(f"Validation error: {str(e)}")
    
    return validation_results


def validate_json_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean JSON response from LLM with improved total amount handling."""
    if not isinstance(data, dict):
        logger.warning("Response is not a dictionary")
        return {"error": "Invalid response format"}
    
    # Check for error in response
    if "error" in data:
        return data
    
    validated_data = {}
    
    # Enhanced field mappings with priority for final totals over taxable values
    field_mappings = {
        "invoice_number": ["Invoice Number", "invoice_number", "InvoiceNumber"],
        "date": ["Date of Issue", "date", "Date", "invoice_date"],
        "seller": ["Seller", "seller", "vendor", "from"],
        "client": ["Client", "client", "customer", "to"],
        # CRITICAL: Prioritize final total over taxable value
        "total": ["gross_total", "gross_worth", "final_total", "grand_total", "total", "Total", "amount_due"],
        "taxable_value": ["taxable_value", "taxable_amount", "net_worth", "net_amount"],
        "items": ["Items", "items", "line_items"]
    }
    
    # Extract fields using flexible field names with priority
    for standard_field, possible_names in field_mappings.items():
        for field_name in possible_names:
            if field_name in data:
                validated_data[standard_field] = data[field_name]
                break
    
    # ENHANCED: Special handling to ensure we get the RIGHT total (not taxable value)
    if "total" not in validated_data:
        # Look for any field that might be the FINAL total amount (highest priority)
        total_candidates = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Prioritize fields that indicate final total
            if any(term in key_lower for term in ['gross_total', 'gross_worth', 'final_total', 'grand_total']):
                total_candidates[key] = {"value": value, "priority": 1}
            elif any(term in key_lower for term in ['total', 'amount_due']) and \
                 not any(avoid in key_lower for avoid in ['taxable', 'net_worth', 'net_amount', 'subtotal']):
                total_candidates[key] = {"value": value, "priority": 2}
            elif any(term in key_lower for term in ['amount']) and \
                 not any(avoid in key_lower for avoid in ['taxable', 'net_', 'subtotal']):
                total_candidates[key] = {"value": value, "priority": 3}
        
        # Select the highest priority total
        if total_candidates:
            best_candidate = min(total_candidates.items(), key=lambda x: x[1]["priority"])
            validated_data["total"] = best_candidate[1]["value"]
            logger.info(f"Selected '{best_candidate[0]}' as total amount with priority {best_candidate[1]['priority']}")
    
    # Validate items if present
    if "items" in validated_data and isinstance(validated_data["items"], list):
        validated_items = []
        for item in validated_data["items"]:
            if isinstance(item, dict):
                validated_items.append(item)
        validated_data["items"] = validated_items
    
    return validated_data


def is_valid_json_string(json_string: str) -> bool:
    """Check if a string is valid JSON."""
    try:
        json.loads(json_string)
        return True
    except (json.JSONDecodeError, TypeError):
        return False




def clean_json_string(json_string: str) -> str:
    """Clean and fix common JSON string issues."""
    cleaned = json_string.strip()
    
    # Fix common LLM JSON issues
    fixes = [
        (r',\s*}', '}'),          # Remove trailing commas before }
        (r',\s*]', ']'),          # Remove trailing commas before ]
        (r'}\s*}$', '}'),         # Remove extra closing braces
        (r'"\s*\n\s*}', '"}'),    # Fix missing quotes
    ]
    
    for pattern, replacement in fixes:
        cleaned = re.sub(pattern, replacement, cleaned)
    
    return cleaned