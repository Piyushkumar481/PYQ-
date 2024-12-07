from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim import corpora, models

# Function for TF-IDF
def calculate_tfidf(questions):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(questions)
    feature_names = vectorizer.get_feature_names_out()
    return tfidf_matrix, feature_names

# Function for LDA Topic Modeling
def lda_topic_modeling(questions, num_topics=3):
    # Create a dictionary and corpus for LDA
    dictionary = corpora.Dictionary([q.split() for q in questions])
    corpus = [dictionary.doc2bow(q.split()) for q in questions]
    
    # Apply LDA
    lda_model = models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=10)
    topics = lda_model.print_topics()
    return topics
