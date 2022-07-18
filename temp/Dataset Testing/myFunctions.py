import re
import nltk
nltk.download('omw-1.4')
nltk.download('stopwords')
import pickle
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC, LinearSVC
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer

def preprocess_text(text_list):
  
  stemmer = WordNetLemmatizer()
  documents = []
  
  for sen in range(0, len(text_list)):
    #Remove all the special characters
    document = re.sub(r'\W', ' ', str(text_list[sen]))
    #remove all single characters
    document = re.sub(r'\s+[a-zA-Z]\s+', ' ', document) 
    #Remove single characters from the start
    document = re.sub(r'\^[a-zA-Z]\s+', ' ', document) 
    #Substituting multiple spaces with single space
    document = re.sub(r'\s+', ' ', document, flags=re.I)
    #Removing prefixed 'b'
    document = re.sub(r'^b\s+', '', document)
    #Converting to Lowercase
    document = document.lower()
    #Lemmatization
    document = document.split()
    document = [stemmer.lemmatize(word) for word in document]
    document = ' '.join(document)
    
    documents.append(document)
    
  text_list = documents
    
  return text_list

class SelectAtMostKBest(SelectKBest):
  
    def _check_params(self, X, y):
        if not (self.k == "all" or 0 <= self.k <= X.shape[1]):
            # set k to "all" (skip feature selection), if less than k features are available
            self.k = "all"