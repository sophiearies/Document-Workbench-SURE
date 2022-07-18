from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
  path('', views.index, name='index'),
  path('home/', views.show_homepage, name='homepage'),
  path('account/', views.displayAccount, name='account'),
  path('documents/', views.reviewController, name='documents'),
  # path('documents/review/', views.show_review, name='review'),
  path('history/', views.historyManager, name='history'),
  path('info/', views.show_info, name='info'),
  path('account/settings/', views.settingsController, name='settings'),
  path('logout/', views.request_logout, name='logout'),
  path('documents/review/<int:id>', views.reviewManager, name='review'),
  path('documents/review/<int:id>/list', views.displayDocuments, name='document_list'),
  path('documents/review/<int:id>/annotate', views.annotateDocument, name='annotate')
]

if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)