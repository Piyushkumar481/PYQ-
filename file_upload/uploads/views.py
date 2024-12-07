import os
import re
import logging
from django.shortcuts import render
from django.core.exceptions import ValidationError
from .forms import FileUploadForm
from .models import UploadedFile
from .utils import extract_text_from_pdf, parse_docx, parse_image_or_scanned_pdf
from .analysis.topic_modeling import calculate_tfidf, lda_topic_modeling
from .analysis.categorization import train_question_categorizer, categorize_questions

# Setting up logging
logging.basicConfig(level=logging.DEBUG)

def extract_text(file_path, file_extension):
    """
    Extracts text based on file type.
    """
    try:
        if file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return parse_docx(file_path)
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            return parse_image_or_scanned_pdf(file_path)
        else:
            raise ValidationError("Unsupported file type. Only PDF, DOCX, and image files are allowed.")
    except Exception as e:
        logging.error(f"Error extracting text: {str(e)}")
        raise e


def clean_text(text):
    """
    Cleans extracted text to remove unnecessary metadata, headers, or formatting.
    """
    text = re.sub(r'(Answer: Not available|None: .*)', '', text)  # Remove answer or metadata lines
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    return text.strip()


def structure_questions(text):
    """
    Extracts and structures questions and their choices from text.
    """
    question_pattern = r'(Q\d+[\.:)]?\s?.*?)(?=\s?Q\d+[\.:)]?|$)'  # Match Q1., Q1), Q1:, etc.
    choice_pattern = r'^[A-E][.)]\s?'  # Match choices like A), B), C), etc.

    questions = []
    matches = re.findall(question_pattern, text, re.DOTALL)

    for match in matches:
        lines = match.split('\n')
        question_text = []
        choices = []

        for line in lines:
            line = line.strip()
            if re.match(choice_pattern, line):
                choices.append(line)
            else:
                question_text.append(line)

        question = ' '.join(question_text).strip()
        if question:
            questions.append({'question': question, 'choices': choices if choices else None})

    return questions


def analyze_questions(questions):
    """
    Analyzes questions to determine types and topics.
    """
    # Train a categorization model
    categorizer = train_question_categorizer()

    # Categorize each question
    question_types = categorize_questions([q['question'] for q in questions], categorizer)

    # Calculate TF-IDF
    tfidf_matrix, feature_names = calculate_tfidf([q['question'] for q in questions])

    # Perform Topic Modeling
    topics = lda_topic_modeling([q['question'] for q in questions])

    return question_types, topics


def file_upload_view(request):
    """
    Handles file upload, processes the file, and renders the success page with parsed data.
    """
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            try:
                # Save uploaded file to the database
                uploaded_file_instance = UploadedFile(file=uploaded_file)
                uploaded_file_instance.save()

                # Get the file path and extension
                file_path = uploaded_file_instance.file.path
                file_extension = os.path.splitext(file_path)[1].lower()

                # Extract, clean, and structure the file content
                text = extract_text(file_path, file_extension)
                cleaned_text = clean_text(text)
                questions = structure_questions(cleaned_text)

                if not questions:
                    raise ValidationError("No valid questions were found in the uploaded file.")

                # Analyze the questions
                question_types, topics = analyze_questions(questions)

                # Render the success template with analyzed data
                return render(request, 'uploads/upload_success.html', {
                    'questions': questions,
                    'types': question_types,
                    'topics': topics,
                })

            except ValidationError as e:
                logging.error(f"Validation error: {str(e)}")
                return render(request, 'uploads/upload.html', {'form': form, 'error': str(e)})

            except Exception as e:
                logging.error(f"Error processing file: {str(e)}")
                return render(request, 'uploads/upload.html', {
                    'form': form,
                    'error': 'An unexpected error occurred while processing the file. Please try again.',
                })

    else:
        form = FileUploadForm()

    return render(request, 'uploads/upload.html', {'form': form})
