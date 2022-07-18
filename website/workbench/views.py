from __future__ import division
import datetime
import math
import os

from sklearn.neural_network import MLPClassifier
from website.settings import BASE_DIR
from tkinter.tix import Form
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, UserModel, User, AuthenticationForm
from django.http import HttpResponse
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC, LinearSVC
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from workbench.models import DocumentRIS
from workbench.models import TempRIS
from workbench.models import HistoryProfile
from workbench.models import HistoryReview
from workbench.models import Profile
from workbench.models import Review
from workbench.models import Document
import workbench.functions
import random
from django.db.models import Q
import csv
import pathlib
import pandas as pd
import numpy as np
from pathlib import Path
import re
import nltk
nltk.download('omw-1.4')
from sklearn.datasets import load_files
nltk.download('stopwords')
nltk.download('wordnet')
import pickle
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from . import functions
from . import estimate_recall
import pdfplumber
from simple_search import search_filter
import rispy

def index_redirect(request):
  return redirect(index)

#Function to load the initial app page
def index(request):
  
  if request.user.is_authenticated:
    return redirect('/app/home')
      
  if request.method == 'POST':

    if 'login_form' in request.POST:
      
      #--------------------------------------- LOGIN FORM ---------------------------------------
      username = request.POST['username_login']
      password = request.POST['password_login']
      
      user = authenticate(request, username=username, password=password)
      
      if user is not None:
        
          login(request, user)
          
          #--------------------------------------- RECORD ACTIONS ---------------------------------------
          #Add action to history
          action_string = "You have logged in"
          action_type = "user_login"
          
          functions.create_profile_action(action_string, action_type, request.user)
          
          return redirect('/app/home')
      else:
          form_login = AuthenticationForm(request.POST)
          return render(request, 'index.html', {'form': form_login})
        
    elif 'register_form' in request.POST:
      
      #--------------------------------------- REGISTRATION FORM ---------------------------------------     
      form_register = UserCreationForm(request.POST)

      #Validate registration form
      try:
          user_exists = User.objects.get(username=request.POST['username'])
          return HttpResponse("Username already taken")
        
      except User.DoesNotExist:
        
        username = form_register.data['username']
        password = form_register.data['password1']
        password_repeat = form_register.data['password2']
        
        name_valid = functions.validate_username(username)
        password_valid = functions.validate_passwords(password, password_repeat)
        
        if name_valid[0] == False or password_valid[0] == False:
          
          #--------------------------------------- FORM NOT VALID ---------------------------------------
          
          if name_valid[0] == False:
            error_msg = name_valid[1]
          elif password_valid[0] == False:
            error_msg = password_valid[1]
          
          return HttpResponse(error_msg)
        
        else:
          
          if form_register.is_valid():
          
            #--------------------------------------- FORM VALID ---------------------------------------
          
            form_register.save()          
            user = authenticate(username=username, password=password)
            login(request, user)
            
            #Save the new account
            profile = Profile(
              user_id=request.user,
              profile_username=str(request.user),
              role='User',
              description='No description',
              documents_screened=0)
            profile.save()
            
            #--------------------------------------- RECORD ACTIONS ---------------------------------------
            #Add action to history
            action_string = "You have created your account"
            action_type = "user_register"
            
            functions.create_profile_action(action_string, action_type, request.user)
            
            return redirect('/')
          
          else:
            return HttpResponse("Something went wrong, please contanct an adminsistrator!")
        
  else:
    form_login = AuthenticationForm()
    form_register = UserCreationForm()
    return render(request, 'index.html', {'form_login': form_login, 'form_register': form_register})

#Function to load the homepage
def show_homepage(request):
  
  if request.user.is_authenticated:
    return render(request, 'homepage.html')
  else:
    return redirect('/')

#Function to display the current user's account information
def displayAccount(request):
  
  if request.user.is_authenticated:
    
    profile = Profile.objects.get(user_id=request.user)
    user = request.user
    
    context_dict = {
      "profile" : profile,
      "user" : user,
    }
     
    return render(request, 'account.html', context=context_dict)
  else:
    return redirect('/')

#Function to display all the reviews for the current user
#Used to created/search reviews
def reviewController(request):
   
  if request.user.is_authenticated:
    
    all_reviews = Review.objects.filter(profile_id=Profile.objects.get(user_id=request.user)).order_by('-created_on')
    
    if request.method == 'POST':
    
      if 'new_review_form' in request.POST:
        
        #------------- CREATE NEW REVIEW -----------------------
        review_title = request.POST['review_title']
        review_description = request.POST['review_description']
        review_history = request.POST.get('review_history', False)
        
        if review_history == 'on':
          review_history = True
        
        #Create the new review
        review = Review(
              profile_id=Profile.objects.get(user_id=request.user), 
              title=review_title,
              description=review_description,
              history_enabled=review_history)

        review.save()
        
        #--------------------------------------- RECORD ACTIONS ---------------------------------------
        #Add action to history
        action_string = "You have created a new review - " + review_title
        action_type = "review_create"
        
        functions.create_profile_action(action_string, action_type, request.user)
        
    elif request.method == 'GET':
      
      if 'search_button' in request.GET:
        
        #------------- SEARCH REVIEWS -----------------------
        search_fields = ['^title', 'description']
        search_query = str(request.GET['search_query'])
        if search_query:
          all_reviews = Review.objects.filter(search_filter(search_fields, search_query)).order_by('-created_on')

        
    
    
    context = {
      "all_reviews" : all_reviews,
    }
    
    # -------------------------------------------------------
    return render(request, 'documents.html', context)
  
  else:
    return redirect('/')

#Function to display history of the account and the history for the selected review
#Also used to search through the account/review history
def historyManager(request):
  
  if request.user.is_authenticated:
    
    #Get all the required information from the page - profile, reviews, search queries, etc.
    profile_id = Profile.objects.get(user_id=request.user)
    all_reviews = Review.objects.filter(profile_id=Profile.objects.get(user_id=request.user)).order_by('-created_on')
    history_profile_actions = HistoryProfile.objects.filter(profile_id=profile_id).order_by('-created_on')
    search_query_profile = ""
    search_query_review = ""
    
    
    if all_reviews.count() > 0:
        selected_review = all_reviews[:1].get()
        history_review_actions = HistoryReview.objects.filter(review_id=selected_review.id).order_by('-created_on')
    else:
      selected_review = "empty"
      history_review_actions = HistoryReview.objects.none()
    
    if request.method == 'GET':
            
      #------------- SEARCH REVIEW HISTORY -----------------------
      if 'history_review_input' in request.GET or 'history_profile_input' in request.GET:
        
        #Search for string matching the query in the desired db fields
        search_fields_profile = ['action', 'created_on', 'type']
        search_query_profile = str(request.GET['history_profile_input'])
        
        #Check if there is a search word in the query
        if search_query_profile:
          history_profile_actions = HistoryProfile.objects.filter(search_filter(search_fields_profile, search_query_profile), profile_id=profile_id).order_by('-created_on')
        
        #Search for string matching the query in the desired db fields
        review_id = request.GET['history_review_dropdown']
        selected_review = Review.objects.get(id=review_id)
        search_fields_reivew = ['action', 'created_on', 'type', 'created_by']
        search_query_review = str(request.GET['history_review_input'])

        #Check if there is a search word in the query
        if search_query_review:
          history_review_actions = HistoryReview.objects.filter(search_filter(search_fields_reivew, search_query_review), review_id=review_id).order_by('-created_on')
        else:
          history_review_actions = HistoryReview.objects.filter(review_id=review_id).order_by('-created_on')

    context_dict = {
      "history_profile" : history_profile_actions,
      "history_review" : history_review_actions,
      "all_reviews" : all_reviews,
      "selected_review": selected_review,
      "search_query_profile" : search_query_profile,
      "search_query_review" : search_query_review,
    }
    
    return render(request, 'history.html', context=context_dict)
  else:
    return redirect('/')

#Function to display the page holding the apps documentation
def show_info(request):
  
  if request.user.is_authenticated:
    return render(request, 'info.html')
  else:
    return redirect('/')

#Function used to display the setting page
#Used to change profile attributes of the current user's account - Role, Description, Profile picture, etc.
def settingsController(request):
  
  if request.user.is_authenticated:
    
    profile = Profile.objects.get(user_id=request.user)
    user = request.user
    
    if request.method == 'POST':
      
      if 'update_profile' in request.POST:
        
        #------------- UPDATE PROFILE -------------
        profile_role = request.POST['profile_role']
        profile_description = request.POST['profile_description']
        
        #Check if new profile picture has been selected
        if 'profile_picture' in request.FILES:
          profile_picture = request.FILES['profile_picture']
          profile_picture_validation = request.POST['profile_picture_validate']
          if len(str(profile_picture)) > 0 and profile_picture_validation == "True":
            profile.profile_pic = profile_picture

        #Check if new banner picture has been selected
        if 'banner_picture' in request.FILES:
          banner_picture = request.FILES['banner_picture']
          banner_picture_validation = request.POST['banner_picture_validate']
          if len(str(banner_picture)) > 0 and banner_picture_validation == "True":
            profile.banner_pic = banner_picture
          
        profile.role = profile_role
        profile.description = profile_description
        profile.save()
    
    context_dict = {
      "profile" : profile,
      "user" : user,
    }
         
    return render(request, 'settings.html', context=context_dict)
  else:
    return redirect('/')
  
#Function to display the selected review and all its relevant information
#Can be used to upload documents to the review, classify documents in the review
#or download the review output in the desired format  
def reviewManager(request, id):
  
  if request.user.is_authenticated:
    
    #------------- OPEN REVIEW -----------------------
    review_id = id
    review = Review.objects.get(id=review_id)
    
    if review.history_enabled:
      history_enabled = "Yes"
    else:
      history_enabled = "No"
    
    all_docs_length = DocumentRIS.objects.filter(review_id=review_id).count()
    annotated_docs_var = 0
    not_annotated_docs_var = 0
    
    if all_docs_length > 0:
      annotated_docs_var = round(((DocumentRIS.objects.filter(~Q(relevancy=2), review_id=review_id,).count()) / (DocumentRIS.objects.filter(review_id=review_id).count()))*100)
      not_annotated_docs_var = round(((DocumentRIS.objects.filter(review_id=review_id, relevancy=2).count()) / (DocumentRIS.objects.filter(review_id=review_id).count()))*100)
    else:
      annotated_docs_var = 0
      not_annotated_docs_var = 0
      
    #Calculate recall here:
    recall_number = "Not enough data"
    recall_percentage = "Not enough data"
    
    relevant_documents_count = DocumentRIS.objects.filter(review_id=review_id, relevancy=1).count()
    all_documents_count = DocumentRIS.objects.filter(review_id=review_id).count()
    recall_list = list(str(review.recall_list))
    recall_list = list(map(int, recall_list))
    
    if relevant_documents_count >= 20 and len(recall_list) >= 20:  
      recall_number = estimate_recall.predict_unseen_rel(all_documents_count, recall_list)
      recall_percentage = '{0:.2f}'.format(relevant_documents_count/(recall_number + relevant_documents_count)*100) + "%"
      
      if recall_number == "-1":
        recall_number = "Unable to calculate"
        recall_percentage = "Unable to calculate"
    else:
      pass
    
    # print("-----------------------------------")
    # print(predicted_unseen_rel)
    # print("-----------------------------------")
    
    context_dict = {
      "review" : review,
      "history_enabled" : history_enabled,
      "all_documents" : DocumentRIS.objects.filter(review_id=review_id),
      "annotated_docs" : DocumentRIS.objects.filter(~Q(relevancy=2), review_id=review_id,),
      "not_annotated_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=2),
      "relevant_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=1),
      "not_relevant_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=0),
      "undecided_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=3),
      "annotated_percent": annotated_docs_var,
      "not_annotated_percent": not_annotated_docs_var,
      "recall_number": recall_number,
      "recall_percentage": recall_percentage,
    }

    
    if request.method == 'POST':
      
      # if 'upload_documents' in request.POST:
        
      #   #------------- UPLOAD DOCUMENTS -----------------------       
      #   uploaded_documents = request.FILES.getlist('uploaded_file')
      #   upload_review = Review.objects.get(id=request.POST['upload_review_id'])
      #   counter = 0
        
      #   #Go over the selected documents
      #   for document in uploaded_documents: 
          
      #     #Check if document is in the desired format
      #     if str(document).lower().endswith(('.pdf', '.txt')):
            
      #       doc_title = str(document)[:-4]
            
      #       #Save the document
      #       new_document = Document(
      #         review_id= upload_review,
      #         document_file=document,
      #         title=doc_title,
      #       )

      #       new_document.save()
            
      #       counter += 1
        
      #   #--------------------------------------- RECORD ACTIONS ---------------------------------------
      #   #Add action to history
      #   action_string = "You have uploaded " + str(counter)  + " new documents in review " + upload_review.title
      #   action_type = "review_upload"
        
      #   functions.create_profile_action(action_string, action_type, request.user)
        
      #   #Add action to review history
      #   if upload_review.history_enabled:
          
      #     action_string_2 = str(counter)  + " new documents have been uploaded"
      #     action_type_2 = "review_upload"
          
      #     functions.create_review_action(action_string_2, action_type_2, request.user, upload_review)
          
      if 'upload_documents' in request.POST:
        print("------------ UPLOADING RIS FILE ---------------------")
        
        #------------- UPLOAD DOCUMENTS -----------------------       
        uploaded_documents = request.FILES.getlist('uploaded_file')
        upload_review = Review.objects.get(id=request.POST['upload_review_id'])
        entries = 0
        
        #Go over the selected documents
        for document in uploaded_documents: 
          
          #Check if document is in the desired format
          if str(document).lower().endswith(('.ris')):
            
            doc_title = str(document)[:-4]
            
            #Save the temporary .ris file
            tempRISFile = TempRIS(
              review_id= upload_review,
              document_file=document,
            )
            
            tempRISFile.save()
          
            #--------------------------------------------------------------------------
            #Work with the .ris file here
            tempQS = TempRIS.objects.filter(review_id=review_id)
            tempRIS = tempQS[:1].get()
            
            tempFilePath = tempRIS.document_file.url
            absoluteFilePath = str(BASE_DIR).replace("\\", "/") + str(tempFilePath)
            
            entries = functions.parse_ris_file(absoluteFilePath, upload_review)
            
            #--------------------------------------------------------------------------
            #Delete the temporary .ris file
            os.remove(absoluteFilePath)
            TempRIS.objects.filter(review_id=review_id).delete()      
        
        #--------------------------------------- RECORD ACTIONS ---------------------------------------
        #Add action to history
        action_string = "You have uploaded " + str(entries)  + " new documents in review " + upload_review.title
        action_type = "review_upload"
        
        functions.create_profile_action(action_string, action_type, request.user)
        
        #Add action to review history
        if upload_review.history_enabled:
          
          action_string_2 = str(entries)  + " new documents have been uploaded"
          action_type_2 = "review_upload"
          
          functions.create_review_action(action_string_2, action_type_2, request.user, upload_review)
        
          
      if 'download_output' in request.POST:
        
        #------------- CREATE OUTPUT -----------------------)
        upload_review = Review.objects.get(id=request.POST['upload_review_id'])
        
        #Create a .csv file as output
        if 'upload_type_csv' in request.POST:
          
          headers = ['ID', 'Title', 'Relevancy']
          
          #Get all the required data for the output   
          annotated_docs_qs = DocumentRIS.objects.filter(~Q(relevancy=2),review_id=review_id)
          not_annotated_docs_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2)
          
          #Generate path for the output
          selected_folder = '\\workbench\\outputs\\review_' + str(upload_review.title) + '_output.csv'
          final_file_path = str(pathlib.Path().resolve()) + selected_folder

          temp_id_counter = 1
          
          with open(final_file_path, 'w+', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            #Write the header
            writer.writerow(headers)
            
            for document in annotated_docs_qs:
              writer.writerow([temp_id_counter, str(document.title), document.relevancy])
              temp_id_counter += 1
              
            for document in not_annotated_docs_qs:
              writer.writerow([temp_id_counter, str(document.title), document.relevancy])
              temp_id_counter += 1
         
        #Create a .txt file as output     
        if 'upload_type_txt' in request.POST:
          
          headers = ['ID', 'Title', 'Relevancy']
          
          #Get all the required data for the output   
          annotated_docs_qs = DocumentRIS.objects.filter(~Q(relevancy=2),review_id=review_id)
          not_annotated_docs_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2)
          
          #Generate path for the output
          selected_folder = '\\workbench\\outputs\\review_' + str(upload_review.title) + '_output.txt'
          final_file_path = str(pathlib.Path().resolve()) + selected_folder

          temp_id_counter = 1
          
          with open(final_file_path, 'w+', encoding='UTF8', newline='') as f:
            
            f.write(headers[0] + "\t" + headers[1] + "\t" + headers[2] + "\n")
            
            for document in annotated_docs_qs:
              f.write(str(temp_id_counter) + "\t" + str(document.title) + "\t" + str(document.relevancy) + "\n")
              temp_id_counter += 1
              
            for document in not_annotated_docs_qs:
              f.write(str(temp_id_counter) + "\t" + str(document.title) + "\t" + str(document.relevancy) + "\n")
              temp_id_counter += 1
        
        #--------------------------------------- RECORD ACTIONS ---------------------------------------
        #Add action to history
        action_string = "You have downloaded output for " + upload_review.title
        action_type = "review_download"
        
        functions.create_profile_action(action_string, action_type, request.user)
        
        #Add action to review history
        if upload_review.history_enabled:
          
          action_string_2 = "Downloaded output for this review"
          action_type_2 = "review_download"
          
          functions.create_review_action(action_string_2, action_type_2, request.user, upload_review)

      if 'download_export' in request.POST:
        #------------- CREATE OUTPUT -----------------------)
        upload_review = Review.objects.get(id=request.POST['export_review_id'])
        
        #Get selected export options
        export_data = request.POST['export_data']
        export_percentage = request.POST['data_export_percentage']
        export_file_type = request.POST['export_file_type']
        
        print("----------------------------------------------------")
        print(str(export_data))
        print("-----------------------------------")
        print(str(export_percentage))
        print("-----------------------------------")
        print(str(export_file_type))
        print("----------------------------------------------------")
        
        headers = ['ID', 'Title', 'Relevancy']
          
        #Get all the required data for the output   
        annotated_docs_qs = DocumentRIS.objects.filter(~Q(relevancy=2),review_id=review_id)
        not_annotated_docs_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2)
        relevant_docs_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=1)
        not_relevant_docs_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=0)
        undecided_docs_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=3)
        all_docs_qs = DocumentRIS.objects.filter(review_id=review_id)
        
        if export_file_type == "type_csv":
          
          #Generate path for the output
          selected_folder = '\\workbench\\exports\\review_' + str(upload_review.title) + '_export.csv'
          final_file_path = str(pathlib.Path().resolve()) + selected_folder

          temp_id_counter = 1
        
          with open(final_file_path, 'w+', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            #Write the header
            writer.writerow(headers)
            
            if export_data == "selected_all":
              chosen_set = list(all_docs_qs)
            elif export_data == "selected_rel":
              chosen_set = list(relevant_docs_qs)
            elif export_data == "selected_not_rel":
              chosen_set = list(not_relevant_docs_qs)
            elif export_data == "selected_undecided":
              chosen_set = list(undecided_docs_qs)
            elif export_data == "selected_annotated":
              chosen_set = list(annotated_docs_qs)
            elif export_data == "selected_not_annotated":
              chosen_set = list(not_annotated_docs_qs)
            else:
              chosen_set = list(all_docs_qs)
              
            
            chosen_docs_final = random.sample(chosen_set, math.floor((math.floor(int(export_percentage))/100)*len(chosen_set)))
            
            for document in chosen_docs_final:
              writer.writerow([temp_id_counter, str(document.title), document.relevancy])
              temp_id_counter += 1
        
        if export_file_type == "type_txt":
          
          #Generate path for the output
          selected_folder = '\\workbench\\exports\\review_' + str(upload_review.title) + '_export.txt'
          final_file_path = str(pathlib.Path().resolve()) + selected_folder

          temp_id_counter = 1
          
          with open(final_file_path, 'w+', encoding='UTF8', newline='') as f:
            
            f.write(headers[0] + "\t" + headers[1] + "\t" + headers[2] + "\n")
            
            if export_data == "selected_all":
              chosen_set = list(all_docs_qs)
            elif export_data == "selected_rel":
              chosen_set = list(relevant_docs_qs)
            elif export_data == "selected_not_rel":
              chosen_set = list(not_relevant_docs_qs)
            elif export_data == "selected_undecided":
              chosen_set = list(undecided_docs_qs)
            elif export_data == "selected_annotated":
              chosen_set = list(annotated_docs_qs)
            elif export_data == "selected_not_annotated":
              chosen_set = list(not_annotated_docs_qs)
            else:
              chosen_set = list(all_docs_qs)
              
            
            chosen_docs_final = random.sample(chosen_set, math.floor((math.floor(int(export_percentage))/100)*len(chosen_set)))
            
            for document in chosen_docs_final:
              f.write(str(temp_id_counter) + "\t" + str(document.title) + "\t" + str(document.relevancy) + "\n")
              temp_id_counter += 1
        
        if export_file_type == "type_ris":
          
          #Generate path for the output
          selected_folder = '\\workbench\\exports\\review_' + str(upload_review.title) + '_export.ris'
          final_file_path = str(pathlib.Path().resolve()) + selected_folder

          temp_id_counter = 1
          
          with open(final_file_path, 'w+', encoding='UTF8', newline='') as f:
            
            if export_data == "selected_all":
              chosen_set = list(all_docs_qs)
            elif export_data == "selected_rel":
              chosen_set = list(relevant_docs_qs)
            elif export_data == "selected_not_rel":
              chosen_set = list(not_relevant_docs_qs)
            elif export_data == "selected_undecided":
              chosen_set = list(undecided_docs_qs)
            elif export_data == "selected_annotated":
              chosen_set = list(annotated_docs_qs)
            elif export_data == "selected_not_annotated":
              chosen_set = list(not_annotated_docs_qs)
            else:
              chosen_set = list(all_docs_qs)
              
            
            chosen_docs_final = random.sample(chosen_set, math.floor((math.floor(int(export_percentage))/100)*len(chosen_set)))
            
            for document in chosen_docs_final:
              f.write(str(temp_id_counter) + "." + "\n")
              f.write("ID  - " + str(document.doc_id) + "\n")
              f.write("T1  - " + str(document.title) + "\n")
              f.write("N2  - " + str(document.abstract) + "\n")
              f.write("\n")
              temp_id_counter += 1
        
        
      
      #Attempt to classify documents
      if 'classify' in request.POST:
        
        #Get the labaled and unlabaled sets
        annotated_docs = DocumentRIS.objects.filter(~Q(relevancy=2), review_id=review_id,)
        not_annotated_docs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2)
        
        #Check if sets are not empty
        if (annotated_docs.count() > 0 and not_annotated_docs.count() > 0):
          
          #Create headers for pandas dataframe
          dataHeaders = {'ID': [],
            'Title': [],
            'Text': [],
            'Relevancy': []
            }
            
          #Create dataframes 
          df_not_annotated_final = pd.DataFrame(dataHeaders)
          df_annotated_final = pd.DataFrame(dataHeaders)
          
          #Add document info into a dataframe for not annotated documents
          for document in not_annotated_docs:
            
            document_id = str(document.id)
            document_title = str(document.title)
            document_relevancy = str(document.relevancy)  
            document_text = str(document.abstract)
              
            # Create the new row as its own dataframe
            df_new_row = pd.DataFrame({'ID':[document_id], 'Title':[document_title], 'Text':[document_text], 'Relevancy':[document_relevancy]})
            df_not_annotated_final = pd.concat([df_not_annotated_final, df_new_row])
              
          #Add document info into a dataframe for annotated documents
          for document in annotated_docs:
            
            # selected_folder = '\\media\\media\\' + str(document.title) + ".ris"
            # final_file_path = str(pathlib.Path().resolve()) + selected_folder
            
            # file_type = str(document.document_file)[-3:]
            
            document_id = str(document.id)
            document_title = str(document.title)
            document_relevancy = str(document.relevancy)
            document_text = str(document.abstract)

            # #Extract the data from a .txt file
            # if file_type == 'txt':
          
            #   with open(final_file_path, 'r', encoding="utf8") as file:
            #     data = file.read()
            #     document_text = str(data)
            
            # #Extract the data from a .pdf file
            # elif file_type == 'pdf':
              
            #   all_text = '' # new line
            #   with pdfplumber.open(final_file_path) as pdf:
            #       for pdf_page in pdf.pages:
            #         single_page_text = pdf_page.extract_text()
            #         all_text = all_text + '\n' + single_page_text
                
            #   document_text = str(all_text)
              
            # Create the new row as its own dataframe and concatonate to the existing one
            df_new_row = pd.DataFrame({'ID':[document_id], 'Title':[document_title], 'Text':[document_text], 'Relevancy':[document_relevancy]})
            df_annotated_final = pd.concat([df_annotated_final, df_new_row])
              
          # ---------------------------------------------------------------------------------------
          
          #Train a model using the annotated documents as training data
          train_data_text = df_annotated_final['Text'].tolist()
          train_data_relevancy = df_annotated_final['Relevancy'].to_numpy()
          
          #Apply text preprocessing
          functions.preprocess_text(train_data_text)
          
          #tfidfconverter = TfidfVectorizer(max_features=1500, min_df=5, max_df=0.7, stop_words=stopwords.words('english'))
          
          #Get selected classifier type
          selected_classifier = request.POST['selected_classifier']
          
          if selected_classifier == "1":
            classifier_pipeline = ('clf', SVC(kernel="rbf", gamma='scale', C=1, probability=True))
            
          elif selected_classifier == "2":
            classifier_pipeline = ('clf', RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1))
            
          elif selected_classifier == "3":
            classifier_pipeline = ('clf', DecisionTreeClassifier(max_depth=5))
            
          elif selected_classifier == "4":
            classifier_pipeline = ('clf', MLPClassifier(alpha=1, max_iter=1000))
            
          elif selected_classifier == "5":
            classifier_pipeline = ('clf', KNeighborsClassifier(3))
          
          else:
            classifier_pipeline = ('clf', SVC(kernel="rbf", gamma='scale', C=1, probability=True))
          
          
          #Create classifier pipeline. Transform words into numerical values using the bag of words method
          pipeline = Pipeline([('vect', TfidfVectorizer(stop_words=stopwords.words('english'), sublinear_tf=True)),
                              ('chi', functions.SelectAtMostKBest(chi2, k=100)),
                              classifier_pipeline])
          
          model = pipeline.fit(train_data_text, train_data_relevancy)     
          
          #Calculate and give relevancy score to each unannotated document
          for index in range(0, len(not_annotated_docs)):
            test_text_list = []
            test_text_list.append(df_not_annotated_final['Text'].values[index])
            
            #Apply text preprocessing
            functions.preprocess_text(test_text_list)
              
            document_prediction_probability = model.predict_proba(test_text_list)
            
            not_annotated_docs[index].score = document_prediction_probability[0][1].tolist()
            not_annotated_docs[index].save()
            
          #Mark the review as classified  
          current_review = Review.objects.get(id=review_id)
          current_review.is_classified = True
          current_review.save()
          
          #--------------------------------------- RECORD ACTIONS ---------------------------------------
          #Add action to history
          action_string = "You have classified documents in review " + current_review.title
          action_type = "review_classify"
          
          functions.create_profile_action(action_string, action_type, request.user)
          
          #Add action to review history
          if current_review.history_enabled:
            
            action_string_2 = "Documents in this review have been classified"
            action_type_2 = "review_classify"
            
            functions.create_review_action(action_string_2, action_type_2, request.user, current_review)
          # --------------------------------------- ONLINE CLASSIFIER -------------------------------------------------
        
      else:
        #Cannot classify. Not enough documents
        pass
      
      return redirect('/app/documents/review/' + str(id))
        
    return render(request, 'review.html', context=context_dict)
    
  else:
    return redirect('/')

#Function used to display all the documents in the current review
#Can be used to search trough them and select a specific document to view/annotate/modify
def displayDocuments(request, id):
     
  if request.user.is_authenticated:
    
    #------------- OPEN LIST OF DOCS -----------------------
    review_id = id  
    current_review = Review.objects.get(id=review_id)
    profile = Profile.objects.get(user_id=request.user)
    all_documents = DocumentRIS.objects.filter(review_id=review_id).order_by('-added_on')

    if request.method == 'GET':
      
      if 'document_list_input' in request.GET:
            
        #------------- SEARCH DOCUMENT LIST -----------------------
        
        #Search for string matching the query in the desired db fields
        search_query = request.GET['document_list_input']
        search_fields = ['screened_by_username', 'added_on', 'title']
        
        #Check if there is a search word in the query
        if search_query:
          all_documents = DocumentRIS.objects.filter(search_filter(search_fields, search_query), review_id=review_id).order_by('-added_on')
    
    if request.method == 'POST':
      
      #Open annotate page for the selected document     
      if 'selected_document_id' not in request.POST:
        
        document_id = request.POST['annoint_document_id']
        document_to_annoint = DocumentRIS.objects.get(id=document_id),
        
        if 'annoint_relevant' in request.POST:
          
          #Annotate selected document as relevant          
          document_to_annoint[0].relevancy = 1
          document_to_annoint[0].is_screened = True
          document_to_annoint[0].screened_by = request.user
          document_to_annoint[0].screened_by_username = str(request.user)
          document_to_annoint[0].added_on = datetime.datetime.now()
          document_to_annoint[0].save()
          
          profile.documents_screened += 1
          profile.save()
          
          #Add to recall list
          updated_string = str(current_review.recall_list) + "1"
          current_review.recall_list = updated_string
          current_review.save()

          #--------------------------------------- RECORD ACTIONS ---------------------------------------
          document_title = str(document_to_annoint[0].title)
          #Add action to history
          action_string = "You have annotated document " + document_title + " in review " + current_review.title + " as relevant"
          action_type = "review_annotate_relevant"
          
          functions.create_profile_action(action_string, action_type, request.user)
          
          #Add action to review history
          if current_review.history_enabled:
          
            action_string_2 = "Document " + document_title + " has been annotated as relevant"
            action_type_2 = "review_classify"
              
            functions.create_review_action(action_string_2, action_type_2, request.user, current_review)
          
        
        if 'annoint_not_relevant' in request.POST:
          
          #Annotate selected document as not relevant            
          document_to_annoint[0].relevancy = 0
          document_to_annoint[0].is_screened = True
          document_to_annoint[0].screened_by = request.user
          document_to_annoint[0].screened_by_username = str(request.user)
          document_to_annoint[0].added_on = datetime.datetime.now()
          document_to_annoint[0].save()
          
          profile.documents_screened += 1
          profile.save()
          
          #Add to recall list
          updated_string = str(current_review.recall_list) + "0"
          current_review.recall_list = updated_string
          current_review.save()
          
          #--------------------------------------- RECORD ACTIONS ---------------------------------------
          document_title = str(document_to_annoint[0].title)
          #Add action to history
          action_string = "You have annotated document " + document_title + " in review " + current_review.title + " as not relevant"
          action_type = "review_annotate_notrelevant"
          
          functions.create_profile_action(action_string, action_type, request.user)
          
          #Add action to review history
          if current_review.history_enabled:
            
            action_string_2 = "Document " + document_title + " has been annotated as not relevant"
            action_type_2 = "review_classify"
              
            functions.create_review_action(action_string_2, action_type_2, request.user, current_review)
          
        if 'annoint_skip' in request.POST:
          
          
          #Annotate selected document as undecided
          document_to_annoint[0].relevancy = 3
          document_to_annoint[0].is_screened = True
          document_to_annoint[0].screened_by = request.user
          document_to_annoint[0].screened_by_username = str(request.user)
          document_to_annoint[0].added_on = datetime.datetime.now()
          document_to_annoint[0].save()
          
          profile.documents_screened += 1
          profile.save()
          
          #--------------------------------------- RECORD ACTIONS ---------------------------------------
          document_title = str(document_to_annoint[0].title)
          #Add action to history
          action_string = "You have annotated document " + document_title + " in review " + current_review.title + " as undecided"
          action_type = "review_annotate_undecided"
          
          functions.create_profile_action(action_string, action_type, request.user)
          
          #Add action to review history
          if current_review.history_enabled:
            
            action_string_2 = "Document " + document_title + " has been annotated as undecided"
            action_type_2 = "review_classify"
              
            functions.create_review_action(action_string_2, action_type_2, request.user, current_review)
          
          
      else:
        
        selected_document_id = request.POST['selected_document_id']
        not_annoited_documents_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2)
        
        context_dict = {
          "review" : Review.objects.get(id=review_id),
          "all_documents" : DocumentRIS.objects.filter(review_id=review_id),
          "not_annoited_documents" : not_annoited_documents_qs,
          "document_to_annoint" : DocumentRIS.objects.get(id=selected_document_id),
          "annotated_docs" : DocumentRIS.objects.filter(~Q(relevancy=2), review_id=review_id,),
          "not_annotated_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=2),
          "relevant_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=1),
          "not_relevant_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=0),
          "undecided_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=3),
        }
        
        return render(request, 'annotate.html', context=context_dict)
      
    context_dict = {
      "review" : current_review,
      "all_documents" : all_documents
    }
        
    return render(request, 'document_list.html', context=context_dict)
    
  else:
    return redirect('/')

#Function used to display a document that is to be annotated along with addition information about the document
#Documents can be annotated as Relevant/Not relevant. User can also choose to skip a document
#If documents in the review have been classified, it will display those with the highest score first
#Otherwise a random document will be presented to the user
def annotateDocument(request, id):
     
  if request.user.is_authenticated and (DocumentRIS.objects.filter(review_id=id, relevancy=2).count() > 0):
    
    review_id = id
    current_review = Review.objects.get(id=review_id)  
    profile = Profile.objects.get(user_id=request.user)
    
    if request.method == 'POST':
      
      document_id = request.POST['annoint_document_id']
      document_to_annoint = DocumentRIS.objects.get(id=document_id),
      
      if 'annoint_relevant' in request.POST:
        
        #Annotate selected document as relevant  
        document_to_annoint[0].relevancy = 1
        document_to_annoint[0].is_screened = True
        document_to_annoint[0].screened_by = request.user
        document_to_annoint[0].screened_by_username = str(request.user)
        document_to_annoint[0].added_on = datetime.datetime.now()
        document_to_annoint[0].save()
        
        profile.documents_screened += 1
        profile.save()
        
        #Add to recall list
        updated_string = str(current_review.recall_list) + "1"
        current_review.recall_list = updated_string
        current_review.save()
        
        #--------------------------------------- RECORD ACTIONS ---------------------------------------
        document_title = str(document_to_annoint[0].title)
        #Add action to history
        action_string = "You have annotated document " + document_title + " in review " + current_review.title + " as relevant"
        action_type = "review_annotate_relevant"
        
        functions.create_profile_action(action_string, action_type, request.user)
        
        #Add action to review history
        if current_review.history_enabled:
        
          action_string_2 = "Document " + document_title + " has been annotated as relevant"
          action_type_2 = "review_classify"
            
          functions.create_review_action(action_string_2, action_type_2, request.user, current_review)
        
      
      if 'annoint_not_relevant' in request.POST:
        
        #Annotate selected document as not relevant  
        document_to_annoint[0].relevancy = 0
        document_to_annoint[0].is_screened = True
        document_to_annoint[0].screened_by = request.user
        document_to_annoint[0].screened_by_username = str(request.user)
        document_to_annoint[0].added_on = datetime.datetime.now()
        document_to_annoint[0].save()
        
        profile.documents_screened += 1
        profile.save()
        
        #Add to recall list
        updated_string = str(current_review.recall_list) + "0"
        current_review.recall_list = updated_string
        current_review.save()
        #--------------------------------------- RECORD ACTIONS ---------------------------------------
        document_title = str(document_to_annoint[0].title)
        #Add action to history
        action_string = "You have annotated document " + document_title + " in review " + current_review.title + " as not relevant"
        action_type = "review_annotate_notrelevant"
        
        functions.create_profile_action(action_string, action_type, request.user)
        
        #Add action to review history
        if current_review.history_enabled:
          
          action_string_2 = "Document " + document_title + " has been annotated as not relevant"
          action_type_2 = "review_classify"
            
          functions.create_review_action(action_string_2, action_type_2, request.user, current_review)
      
      if 'annoint_skip' in request.POST:
          
        #Annotate selected document as undecided
        document_to_annoint[0].relevancy = 3
        document_to_annoint[0].is_screened = True
        document_to_annoint[0].screened_by = request.user
        document_to_annoint[0].screened_by_username = str(request.user)
        document_to_annoint[0].added_on = datetime.datetime.now()
        document_to_annoint[0].save()
        
        profile.documents_screened += 1
        profile.save()
        
        #--------------------------------------- RECORD ACTIONS ---------------------------------------
        document_title = str(document_to_annoint[0].title)
        #Add action to history
        action_string = "You have annotated document " + document_title + " in review " + current_review.title + " as undecided"
        action_type = "review_annotate_undecided"
        
        functions.create_profile_action(action_string, action_type, request.user)
        
        #Add action to review history
        if current_review.history_enabled:
          
          action_string_2 = "Document " + document_title + " has been annotated as undecided"
          action_type_2 = "review_classify"
            
          functions.create_review_action(action_string_2, action_type_2, request.user, current_review)
            
        
      #------------------------ CHECK NOT ANOINTED DOCS -------------------------------
      if (DocumentRIS.objects.filter(review_id=id, relevancy=2).count() < 1): 
        return redirect('/app/documents/review/' + str(id))
      
      else:
        
        #If documents have been classified in the current review, sort by highest score first
        if current_review.is_classified:
          not_annoited_documents_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2).order_by('-score')
          document_to_annotate = not_annoited_documents_qs[:1].get()
          document_type = str("ris")
        
        #If documents have not been classified in the current review, present the user with a random document
        else:  
          not_annoited_documents_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2)
          random_doc_list = random.sample(list(not_annoited_documents_qs), 1)
          document_to_annotate = random_doc_list[0]
          document_type = str("ris")
        
        context_dict = {
          "review" : Review.objects.get(id=review_id),
          "all_documents" : DocumentRIS.objects.filter(review_id=review_id),
          "not_annoited_documents" : not_annoited_documents_qs,
          "document_type" : document_type,
          "document_to_annoint" : document_to_annotate,
          "annotated_docs" : DocumentRIS.objects.filter(~Q(relevancy=2), review_id=review_id,),
          "not_annotated_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=2),
          "relevant_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=1),
          "not_relevant_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=0),
          "undecided_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=3),
        }
     
    else:
      
      #If documents have been classified in the current review, sort by highest score first
      if current_review.is_classified:
        not_annoited_documents_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2).order_by('-score')
        document_to_annotate = not_annoited_documents_qs[:1].get()
        document_type = str("ris")
       
      #If documents have not been classified in the current review, present the user with a random document 
      else:
        not_annoited_documents_qs = DocumentRIS.objects.filter(review_id=review_id, relevancy=2)
        random_doc_list = random.sample(list(not_annoited_documents_qs), 1)
        document_to_annotate = random_doc_list[0]
        document_type = str("ris")
      
      context_dict = {
        "review" : Review.objects.get(id=review_id),
        "all_documents" : DocumentRIS.objects.filter(review_id=review_id),
        "not_annoited_documents" : not_annoited_documents_qs,
        "document_type" : document_type,
        "document_to_annoint" : document_to_annotate,
        "annotated_docs" : DocumentRIS.objects.filter(~Q(relevancy=2), review_id=review_id,),
        "not_annotated_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=2),
        "relevant_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=1),
        "not_relevant_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=0),
        "undecided_docs" : DocumentRIS.objects.filter(review_id=review_id, relevancy=3),
      }
       
    return render(request, 'annotate.html', context=context_dict)
    
  else:
    return redirect('/app/documents/review/' + str(id))
     
#Function to logout the user     
def request_logout(request):
  
  #--------------------------------------- RECORD ACTIONS ---------------------------------------
  #Add action to history
  action_string = "You have logged out"
  action_type = "user_loggout"
  
  functions.create_profile_action(action_string, action_type, request.user)
  
  logout(request)
  return redirect(index)
      
      
      
      
      
      