from django.urls import path

from share_file import views

app_name = 'share_file'

urlpatterns = [
    path('', views.FileList.as_view(), name='file_list'),
    path('file-add/', views.FileFieldFormView.as_view(), name='file_add'),
    path('file-delete/<int:pk>/', views.file_delete, name='file_delete'),

]
