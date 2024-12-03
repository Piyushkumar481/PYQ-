import os
import re
from django.shortcuts import render
from django.core.exceptions import ValidationError
from .forms import FileUploadForm
from .models import UploadedFile
from .utils import extract_text_from_pdf, parse_docx, parse_image_or_scanned_pdf
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
import logging

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF. If the PDF contains scanned images, OCR is used to extract text.
    """
    try:
        # Try extracting text from the PDF directly (for text-based PDFs)
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()  # Extract text from each page
        
        # If no text is found, use OCR on the scanned pages
        if not text.strip():
            print("No text extracted, trying OCR.")
            images = convert_from_path(file_path)  # Convert PDF pages to images
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)  # Use OCR to extract text from image
        
        return text.strip()  # Return cleaned text
    
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""



import logging

# Setting up logging
logging.basicConfig(level=logging.DEBUG)

def parse_and_clean_file(file_path):
    """
    Parse and clean the uploaded file based on its extension.
    It extracts text and structures the questions in a readable format.
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    text = ""

    # Parse the file based on its extension
    if file_extension == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        text = parse_docx(file_path)
    elif file_extension in ['.jpg', '.jpeg', '.png']:
        text = parse_image_or_scanned_pdf(file_path)
    else:
        raise ValidationError("Unsupported file type. Only PDF, DOCX, and image files are allowed.")
    
    # Debug: Log raw extracted text
    logging.debug(f"Raw extracted text from {file_path}: {text}")

    # Clean the parsed text
    cleaned_text = clean_text(text)
    logging.debug(f"Cleaned text: {cleaned_text}")

    # Structure the text data into questions
    structured_data = structure_questions(cleaned_text)
    logging.debug(f"Structured data: {structured_data}")

    return structured_data


def clean_text(text):
    """
    This function cleans up the extracted text by removing unnecessary metadata
    and extra spaces, ensuring that only relevant content remains.
    """
    text = re.sub(r'(Answer: Not available|None: .*)', '', text)  # Remove answer or metadata lines
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = text.strip()  # Remove leading/trailing whitespace
    return text
def structure_questions(text):
    """
    Processes the input text and separates questions, choices, and long-form questions.
    """
    # Updated regex to handle multiple types of questions: Q1., Q1), Q1:, etc.
    question_pattern = r'(Q\d+[\.:)]?\s?.*?)(?=\s?Q\d+[\.:)]?|$)'  # Match Q1., Q1), Q1:, etc.
    choice_pattern = r'^[A-E][.)]\s?'  # Match choices like A), B), C), etc.

    questions = []
    matches = re.findall(question_pattern, text, re.DOTALL)  # Find all question blocks
    
    if not matches:
        print("No questions found with the current regex pattern.")  # Debugging log if no questions are found

    for match in matches:
        lines = match.split('\n')  # Split by lines within the question block
        question_text = []
        choices = []

        for line in lines:
            line = line.strip()
            if re.match(choice_pattern, line):  # Match choices
                choices.append(line)
            else:
                question_text.append(line)

        question = ' '.join(question_text).strip()  # Combine question text

        if question:  # Only add questions that aren't empty
            questions.append({
                'question': question,
                'choices': choices if choices else None
            })
    
    if not questions:
        print("No valid questions found.")  # Debugging log if no valid questions are found

    return questions


def upload_success_view(request):
    """
    Displays the success page after a file is successfully uploaded and processed.
    """
    return render(request, 'uploads/success.html')

from django.shortcuts import render
from django.core.exceptions import ValidationError
from .forms import FileUploadForm
from .models import UploadedFile
from .utils import extract_text_from_pdf, parse_docx, parse_image_or_scanned_pdf
from .views import parse_and_clean_file

def file_upload_view(request):
    """
    Handles file upload, processes the file, and renders success page with parsed data.
    """
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']  # Handle a single file upload
            parsed_data = []

            # Save the uploaded file to the database
            uploaded_file_instance = UploadedFile(file=uploaded_file)
            uploaded_file_instance.save()

            # Parse and clean the uploaded file, extracting structured questions
            try:
                file_path = uploaded_file_instance.file.path  # Get the file path after saving
                parsed_data = parse_and_clean_file(file_path)

                if not parsed_data:
                    raise ValidationError("No questions were found in the uploaded file.")
            except ValidationError as e:
                logging.error(f"Validation error: {str(e)}")  # Log validation error
                return render(request, 'uploads/upload.html', {'form': form, 'error': str(e)})
            except Exception as e:
                logging.error(f"Error processing file: {str(e)}")  # Log general error
                return render(request, 'uploads/upload.html', {'form': form, 'error': f'An error occurred while processing the file: {str(e)}'})

            # Pass the parsed data to the success template
            return render(request, 'uploads/success.html', {'parsed_data': parsed_data})

    else:
        form = FileUploadForm()

    return render(request, 'uploads/upload.html', {'form': form})
