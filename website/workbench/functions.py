from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, UserModel, User
from django.http import HttpResponse
import re
import nltk
from requests import request
from sklearn.feature_selection import SelectKBest
from workbench.models import DocumentRIS
from workbench.models import HistoryProfile
from workbench.models import HistoryReview
from workbench.models import Profile
from workbench.models import Review
from workbench.models import Document
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, UserModel, User, AuthenticationForm
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score

nltk.download('omw-1.4')
from sklearn.datasets import load_files
nltk.download('stopwords')
import pickle
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

def validate_username(username):
  
  if len(username) == 0 or username is None:
    return (False, "Please enter an Username")
  
  if len(username) < 4:
    return (False, "Username must be atleast 4 characters")
  
  if len(username) > 50:
    return (False, "Username must not exceed 50 characters")
  
  return (True, "Validated")

def validate_passwords(password, repeat_password):
  
  if len(password) == 0 or password is None:
    return (False, "Please enter a Password")
  
  if len(repeat_password) == 0 or repeat_password is None:
    return (False, "Please repeat your Password")
  
  if len(password) < 8:
    return (False, "Password must be atleast 8 characters")
  
  if len(password) > 50:
    return (False, "Password must not exceed 50 characters")
  
  if password != repeat_password:
    return (False, "Passwords must match. Please try again")
  
  return (True, "Validated")

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
  
def create_profile_action(action_string, action_type, user):
  
  #Create profile action
  history_profile_action = HistoryProfile(
        profile_id=Profile.objects.get(user_id=user), 
        action=action_string,
        type=action_type)
  
  history_profile_action.save()
  
def create_review_action(action_string, action_type, user, review):
    
  #Create profile action
  history_review_action = HistoryReview(
        review_id=review, 
        action=action_string,
        type=action_type,
        created_by=str(user.username),
        user_id=user)
  
  history_review_action.save()
  
def parse_ris_file(file_path, review):
  
  tempFile = open(file_path, 'r')
  fileLines = tempFile.readlines()
        
  entries = 0
  reading_entry = False
  text_id = ""
  text_title = ""
  text_abstract = ""
  needed_data_bool = False
  
  for line in fileLines: 
    
    entries_number = line.strip().partition(".")[0].strip()
    if entries_number.isnumeric():
      entries += 1
      reading_entry = True   

    if reading_entry:
      temp_line_type = str(line.strip().partition("  - ")[0]).strip()
      end_line_type = str(line.strip().partition("  -")[0]).strip()
      
      if temp_line_type == "ID":
        text_id = str(line.strip().partition("  - ")[2]).strip()
        
      if temp_line_type == "T1":
        text_title = str(line.strip().partition("  - ")[2]).strip()
        
      if temp_line_type == "N2":
        text_abstract = str(line.strip().partition("  - ")[2]).strip()
        
      if end_line_type == "ER":
        needed_data_bool = True

      if (needed_data_bool == True):
        
        #Check for dublicates before saving
        
        #Save document here:
        new_document = DocumentRIS(
              review_id=review, 
              title=text_title,
              abstract=text_abstract,
              doc_id=text_id)
        
        new_document.save()
        
        text_id, text_title, text_abstract = "", "", ""
        needed_data_bool = False
        reading_entry = False
  
  return entries     
        
    
        
        
        