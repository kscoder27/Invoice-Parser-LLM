import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import pypdf
import json

# Add project root to path to allow imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.parser import parse_invoice, extract_text_from_pdf

class TestInvoiceParser(unittest.TestCase):

    def create_dummy_pdf(self) -> BytesIO:
        """Creates a dummy in-memory PDF for testing."""
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=612, height=792) # Standard letter size
        
        # In a real test, you might add text here, but for this, we'll mock extract_text
        pdf_buffer = BytesIO()
        writer.write(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer

    @patch('core.parser.extract_text_from_pdf')
    @patch('core.parser.llm_model.run')
    def test_parse_invoice_success(self, mock_llm_run, mock_extract_text):
        """
        Test the end-to-end parsing process with mocked dependencies.
        """
        # --- Arrange ---
        # Mock the text extraction to return some sample text
        mock_extract_text.return_value = "Invoice #123. Vendor: Test Corp. Total: $99.99"
        
        # Mock the LLM response
        mock_llm_response = {
            "invoice_number": "123",
            "vendor_name": "Test Corp",
            "total_amount": 99.99
        }
        mock_llm_run.return_value = json.dumps(mock_llm_response)
        
        # Create a dummy PDF file
        dummy_pdf = self.create_dummy_pdf()
        user_prompt = "Extract invoice number, vendor name, and total."

        # --- Act ---
        result = parse_invoice(dummy_pdf, user_prompt)

        # --- Assert ---
        self.assertTrue(result.get('success'))
        self.assertIn('data', result)
        self.assertEqual(result['data']['invoice_number'], "123")
        self.assertEqual(result['data']['vendor_name'], "Test Corp")
        self.assertEqual(result['data']['total_amount'], 99.99)
        
        # Verify that our mocks were called
        mock_extract_text.assert_called_once()
        mock_llm_run.assert_called_once()

    def test_extract_text_from_pdf(self):
        """
        A more direct test for text extraction (though limited without a real file).
        This mainly tests the function's structure.
        """
        # --- Arrange ---
        # We can't easily add text to a pypdf object in memory for extraction,
        # so we'll test the error case for an empty/image PDF.
        dummy_pdf = self.create_dummy_pdf()

        # --- Act ---
        text = extract_text_from_pdf(dummy_pdf)

        # --- Assert ---
        # Since the blank PDF has no text, we expect the error message.
        self.assertIn("Could not extract any text", text)

if __name__ == '__main__':
    unittest.main()

