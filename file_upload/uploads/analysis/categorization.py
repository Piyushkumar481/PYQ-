import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB

nltk.download('punkt')

# Dummy Data for Training
# Format: [(question_text, type, difficulty)]
DUMMY_DATA = [
    ("What is Newton's second law of motion?", "short_answer", "easy"),
    ("Derive the formula for acceleration.", "long_answer", "hard"),
    ("Which of the following is not a prime number?", "multiple_choice", "medium"),
]

# Train a Classification Model
def train_question_categorizer():
    # Split Data
    questions, types, difficulties = zip(*DUMMY_DATA)
    X_train, X_test, y_train, y_test = train_test_split(questions, types, test_size=0.2, random_state=42)

    # Define a pipeline for vectorization and classification
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('classifier', MultinomialNB())  # You can replace this with SVC() for SVM
    ])

    # Train the model
    pipeline.fit(X_train, y_train)
    return pipeline

# Predict Question Type or Difficulty
def categorize_questions(questions, model):
    return model.predict(questions)
