#!/usr/bin/env python3
"""
Script for parsing PDF XML data.
This script provides functionality to:
1. Extract text from PDF files
2. Parse XML data from files
3. Process and combine the extracted information
"""

import argparse
import logging
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
except ImportError:
    print("Please install pdfminer.six: pip install pdfminer.six")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFXMLParser:
    def __init__(self, pdf_path: Optional[str] = None, xml_path: Optional[str] = None):
        """
        Initialize the parser with paths to PDF and XML files.
        
        Args:
            pdf_path: Path to the PDF file
            xml_path: Path to the XML file
        """
        self.pdf_path = pdf_path
        self.xml_path = xml_path
        
    def parse_pdf(self) -> str:
        """
        Extract text content from PDF file.
        
        Returns:
            str: Extracted text from PDF
        """
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        
        try:
            laparams = LAParams(
                line_margin=0.5,
                word_margin=0.1,
                char_margin=2.0,
                boxes_flow=0.5
            )
            text = extract_text(
                self.pdf_path,
                laparams=laparams
            )
            return text.strip()
        except Exception as e:
            logger.error(f"Error parsing PDF {self.pdf_path}: {str(e)}")
            raise
    
    def parse_xml(self) -> Dict:
        """
        Parse XML file and extract structured data.
        
        Returns:
            dict: Parsed XML data as dictionary
        """
        if not self.xml_path or not os.path.exists(self.xml_path):
            raise FileNotFoundError(f"XML file not found: {self.xml_path}")
        
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            
            # Convert XML to dictionary (implement based on your XML structure)
            return self._xml_to_dict(root)
        except ET.ParseError as e:
            logger.error(f"Error parsing XML {self.xml_path}: {str(e)}")
            raise
    
    def _xml_to_dict(self, element: ET.Element) -> Union[Dict, str]:
        """
        Convert XML element to dictionary recursively.
        
        Args:
            element: XML element to convert
            
        Returns:
            Union[Dict, str]: Converted dictionary or string value
        """
        result = {}
        
        # Handle attributes
        if element.attrib:
            result.update(element.attrib)
            
        # Handle nested elements
        for child in element:
            if len(child) == 0 and not child.attrib:
                # Simple element with just text
                result[child.tag] = child.text
            else:
                # Complex element with nested elements or attributes
                child_data = self._xml_to_dict(child)
                if child.tag in result:
                    if isinstance(result[child.tag], list):
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = [result[child.tag], child_data]
                else:
                    result[child.tag] = child_data
                    
        return result if result else element.text

def main():
    parser = argparse.ArgumentParser(description='Parse PDF and XML files')
    parser.add_argument('--pdf', type=str, help='Path to PDF file')
    parser.add_argument('--xml', type=str, help='Path to XML file')
    parser.add_argument('--output', type=str, help='Output file path')
    args = parser.parse_args()
    
    try:
        pdf_xml_parser = PDFXMLParser(
            pdf_path=args.pdf,
            xml_path=args.xml
        )
        
        results = {}
        
        # Parse PDF if provided
        if args.pdf:
            logger.info(f"Parsing PDF file: {args.pdf}")
            results['pdf_content'] = pdf_xml_parser.parse_pdf()
            
        # Parse XML if provided
        if args.xml:
            logger.info(f"Parsing XML file: {args.xml}")
            results['xml_content'] = pdf_xml_parser.parse_xml()
            
        # Handle output
        if args.output:
            import json
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to: {args.output}")
        else:
            # Print to console
            import json
            print(json.dumps(results, ensure_ascii=False, indent=2))
            
    except Exception as e:
        logger.error(f"Error during parsing: {str(e)}")
        raise

if __name__ == "__main__":
    main()
