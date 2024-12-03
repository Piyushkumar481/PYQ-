import PyPDF2
from docx import Document
import pytesseract
from pdf2image import convert_from_path
import re
from PIL import Image
import os

def parse_pdf(file_path):
    """Parse PDF file using PyPDF2"""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def parse_docx(file_path):
    """Parse DOCX file using python-docx"""
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def parse_image_or_scanned_pdf(file_path):
    """Parse scanned PDF or image using Tesseract OCR"""
    images = convert_from_path(file_path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

def clean_text(text):
    """Clean extracted text by removing unnecessary formatting, headers, and footers"""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with one space
    text = re.sub(r'[^a-z0-9\s]', '', text)  # Remove non-alphanumeric characters
    lines = text.split("\n")
    cleaned_text = "\n".join([line for line in lines if not line.startswith("page")])
    return cleaned_text

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF using PyPDF2 or OCR if needed.
    Returns the extracted text as a string.
    """
    text = parse_pdf(file_path)
    
    # If no text is found using PyPDF2, use OCR
    if not text.strip():
        print("No text found using PyPDF2. Attempting OCR...")
        text = parse_image_or_scanned_pdf(file_path)

    return text

def extract_questions(text):
    """
    Extracts questions from the given text based on common patterns.
    Returns a list of questions.
    """
    # Example: Match questions starting with numbers (e.g., "1. What is...?") and general questions
    numbered_questions = re.findall(r'\d+\..*?\?', text)
    general_questions = re.findall(r'.*?\?', text)
    
    # Combine results and remove duplicates
    questions = list(set(numbered_questions + general_questions))
    return questions

