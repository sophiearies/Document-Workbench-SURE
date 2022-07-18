import re
import nltk
from sklearn.neural_network import MLPClassifier
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
from sklearn.naive_bayes import MultinomialNB
from myFunctions import *
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report
from sklearn.metrics import f1_score




print("--------------------------------------------")



#Reading train dictionary
train_dict = pickle.load(open('train_data_1.pkl','rb'))

total_accuracy = 0
total_docs_train = 0
total_docs_test = 0

reviews_numbers = 5

for z in range(0, reviews_numbers):  

  train_text_list = []
  train_text_relevancy = []

  for index, review in enumerate(train_dict):

    if z == index:
      relevant_ids = train_dict[review]['included']['ids_abs']
      data_search_results = train_dict[review]['search_results']
      data_ids = data_search_results['ids']
      data_records = data_search_results['records']
      
      total_docs_train += len(data_records)
      
      for index, id in enumerate(data_ids):
        if id in relevant_ids:
          train_text_relevancy.append(1)
        else:
          train_text_relevancy.append(0)

      
      for index_record, record in enumerate(data_records):
        review_text = data_records[index_record][2]
        train_text_list.append(str(review_text))
        
        
  #Reading test dictionary
  test_dict = pickle.load(open('test_data_1.pkl','rb'))  

  test_text_list = []
  test_text_relevancy = []

  for index, review in enumerate(test_dict):

    if z == index:
      relevant_ids = test_dict[review]['included']['ids_abs']
      data_search_results = test_dict[review]['search_results']
      data_ids = data_search_results['ids']
      data_records = data_search_results['records']
      
      total_docs_test += len(data_records)
      
      for index, id in enumerate(data_ids):
        if id in relevant_ids:
          test_text_relevancy.append(1)
        else:
          test_text_relevancy.append(0)

      
      for index_record, record in enumerate(data_records):
        review_text = data_records[index_record][2]
        test_text_list.append(str(review_text))

  #Train a model using the annotated documents as training data
  train_data_text = train_text_list
  train_data_relevancy = train_text_relevancy

  #Apply text preprocessing
  preprocess_text(train_data_text)

  #tfidfconverter = TfidfVectorizer(max_features=1500, min_df=5, max_df=0.7, stop_words=stopwords.words('english'))
  #clf = MultinomialNB().fit(X_train_tfidf, twenty_train.target)

  #Create classifier pipeline. Transform words into numerical values using the bag of words method
  pipeline = Pipeline([('vect', TfidfVectorizer(stop_words=stopwords.words('english'), sublinear_tf=True)),
                      ('chi', SelectAtMostKBest(chi2, k=100)),
                      ('clf', SVC(kernel="linear", C=0.025, probability=True))])

  model = pipeline.fit(train_data_text, train_data_relevancy)

  #Apply text preprocessing
  preprocess_text(test_text_list)
    
  prediction_list = model.predict(test_text_list)
  prediction_list_proba = model.predict_proba(test_text_list)

  for index, item in enumerate(prediction_list_proba):
    if item[1] > 0.5:
      prediction_list[index] = 1


  accuracy_metric = accuracy_score(test_text_relevancy, prediction_list)
  print(accuracy_metric)
  
  total_accuracy += accuracy_metric
  print("--------------------------------------------")



average_accuracy = total_accuracy / reviews_numbers
print("Average accuracy over " +  str(reviews_numbers) + " reviews: " + str(average_accuracy))
print("Trained documents: " + str(total_docs_train))
print("Test documents: " + str(total_docs_test))

    
  
    
print("--------------------------------------------")




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