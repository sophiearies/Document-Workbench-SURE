import datetime
import os
from django.db import models
from django.conf import settings

class Profile(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=False,  null=False)
    profile_username = models.CharField(max_length=50, blank=False, null=False, default='temp_username')
    role = models.CharField(max_length=50, blank=True, null=False)
    description = models.CharField(max_length=300, blank=True, null=True)
    created_on = models.DateTimeField(auto_now=False, default=datetime.datetime.now)
    profile_pic = models.FileField(upload_to='images/', default='images/avatar2.png')
    banner_pic = models.FileField(upload_to='images/', default='images/banner1.jpg')
    documents_screened = models.IntegerField(default=0)
    
    def __str__(self):
        return self.url
    def path(self):
        return self.url

class Review(models.Model):
    profile_id = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=False, null=False)
    title = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=300, blank=True, null=True)
    created_on = models.DateTimeField(auto_now=False, default=datetime.datetime.now)
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    history_enabled = models.BooleanField(default=True)
    is_classified = models.BooleanField(default=False)
    recall_list = models.CharField(max_length=500000, blank=False, null=False, default='')

class Participant(models.Model):
    review_id = models.ForeignKey(Review, on_delete=models.CASCADE, blank=False, null=False)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,blank=False, null=False)
    role = models.CharField(max_length=50, blank=False, null=False)
    documents_screened = models.IntegerField(default=0)

class Tag(models.Model):
    review_id = models.ForeignKey(Review, on_delete=models.CASCADE,blank=False, null=False)
    tag_name = models.CharField(max_length=50)
    
class DocumentRIS(models.Model):
    review_id = models.ForeignKey(Review, on_delete=models.CASCADE, blank=False, null=False)
    title = models.CharField(max_length=50, blank=False, null=False, default='(Unknown title)')
    abstract = models.CharField(max_length=50, blank=False, null=False, default='(Unavailable)')
    doc_id = models.CharField(max_length=50, blank=False, null=False, default='(Unavailable)')
    screened_by_username = models.CharField(max_length=50, blank=False, null=False, default='None')
    screened_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='screened_by_user')
    is_screened = models.BooleanField(default=False)
    relevancy = models.IntegerField(default=2)
    score = models.FloatField(default=0.0000000000000000)
    added_on = models.DateTimeField(auto_now=False, default=datetime.datetime.now)
    # tag = models.CharField(max_length=50, blank=False, null=False, default='(Unavailable)')
    # reason = models.CharField(max_length=50, blank=False, null=False, default='(Unavailable)')

    
class TempRIS(models.Model):
    review_id = models.ForeignKey(Review, on_delete=models.CASCADE, blank=False, null=False)
    document_file = models.FileField(upload_to='media/', default='media/test1.pdf')
    
    def __str__(self):
        return self.url
    def path(self):
        return self.url

class Document(models.Model):
    review_id = models.ForeignKey(Review, on_delete=models.CASCADE, blank=False, null=False)
    document_file = models.FileField(upload_to='media/', default='media/test1.pdf')
    title = models.CharField(max_length=50, blank=False, null=False, default='Unknown title')
    screened_by_username = models.CharField(max_length=50, blank=False, null=False, default='None')
    screened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='screened_by')
    is_screened = models.BooleanField(default=False)
    relevancy = models.IntegerField(default=2)
    score = models.FloatField(default=0.0000000000000000)
    added_on = models.DateTimeField(auto_now=False, default=datetime.datetime.now)
    
    def __str__(self):
        return self.url
    def path(self):
        return self.url

class DocumentTag(models.Model):
    document_id = models.ForeignKey(Document, on_delete=models.CASCADE, blank=False, null=False)
    tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True)

class HistoryProfile(models.Model):
    profile_id = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=False, null=False)
    action = models.CharField(max_length=200, blank=False, null=False)
    created_on = models.DateTimeField(auto_now=False, default=datetime.datetime.now, null=False)
    type = models.CharField(max_length=50, null=False)

class HistoryReview(models.Model):
    review_id = models.ForeignKey(Review, on_delete=models.CASCADE, blank=False, null=False)
    action = models.CharField(max_length=200, blank=False, null=False)
    created_on = models.DateTimeField(auto_now=False, default=datetime.datetime.now, null=False)
    type = models.CharField(max_length=50, null=False)
    created_by = models.CharField(max_length=50, blank=False, null=False, default='temp_username')
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=False, null=False)
    
