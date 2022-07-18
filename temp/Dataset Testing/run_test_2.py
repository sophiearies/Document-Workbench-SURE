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
from myFunctions import *





print("--------------------------------------------")



#Reading train dictionary
train_dict = pickle.load(open('train_data_3.pkl','rb'))  

train_text_list = []
train_text_relevancy = []

for key in train_dict.keys():
  print(key)

for index, review in enumerate(train_dict):
  
  if index == 0:
    break
    
    # for key in train_dict[review].keys():
    #   print(key)
      
    #print(train_dict[review]['search_results'][4])

#   if (index == 1):
#     relevant_ids = train_dict[review]['included']['ids_abs']
#     data_search_results = train_dict[review]['search_results']
#     data_ids = data_search_results['ids']
#     data_records = data_search_results['records']
    
#     for index, id in enumerate(data_ids):
#       if id in relevant_ids:
#         train_text_relevancy.append(1)
#       else:
#         train_text_relevancy.append(0)

    
#     for index_record, record in enumerate(data_records):
#       review_text = data_records[index_record][2]
#       train_text_list.append(str(review_text))
      
      
# #Reading test dictionary
# test_dict = pickle.load(open('test_data_3.pkl','rb'))  

# test_text_list = []
# test_text_relevancy = []

# for index, review in enumerate(test_dict):

#   if (index == 1):
#     relevant_ids = test_dict[review]['included']['ids_abs']
#     data_search_results = test_dict[review]['search_results']
#     data_ids = data_search_results['ids']
#     data_records = data_search_results['records']
    
#     for index, id in enumerate(data_ids):
#       if id in relevant_ids:
#         test_text_relevancy.append(1)
#       else:
#         test_text_relevancy.append(0)

    
#     for index_record, record in enumerate(data_records):
#       review_text = data_records[index_record][2]
#       test_text_list.append(str(review_text))

# #Train a model using the annotated documents as training data
# train_data_text = train_text_list
# train_data_relevancy = train_text_relevancy

# #Apply text preprocessing
# preprocess_text(train_data_text)

# #tfidfconverter = TfidfVectorizer(max_features=1500, min_df=5, max_df=0.7, stop_words=stopwords.words('english'))

# #Create classifier pipeline. Transform words into numerical values using the bag of words method
# pipeline = Pipeline([('vect', TfidfVectorizer(max_features=500, min_df=15, max_df=0.7, stop_words=stopwords.words('english'), sublinear_tf=True)),
#                     ('chi', SelectAtMostKBest(chi2, k=1000)),
#                     ('clf', SVC(kernel="rbf", gamma='scale', C=1, probability=True))])

# model = pipeline.fit(train_data_text, train_data_relevancy)

# #Apply text preprocessing
# preprocess_text(test_text_list)
  
# prediction_list = model.predict(test_text_list)
# prediction_list_proba = model.predict_proba(test_text_list)

# # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
# # print(test_text_relevancy)
# # print("**********************************************************")
# # for i in range(0, len(prediction_list_proba)):
# #   print(i)
# #   print(prediction_list_proba[i])
# # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

# true_labels = 0
# all_labels = len(prediction_list)
# for i in range(0, len(prediction_list)):
#   if(prediction_list[i] == test_text_relevancy[i]):
#     true_labels += 1
    
# accuracy = true_labels/all_labels
# print(accuracy)
  
    
    

  
    
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