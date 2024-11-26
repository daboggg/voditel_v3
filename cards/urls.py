from django.urls import path

from cards import views

urlpatterns = [
    path('cards/', views.CardList.as_view(), name='card_list'),
    path('card-add/', views.CardAdd.as_view(), name='card_add'),
    path('card/<int:pk>/', views.CardDetail.as_view(), name='card_detail'),
    path('card-delete/<int:pk>/', views.CardDelete.as_view(), name='card_delete'),
    path('card-edit/<int:pk>/', views.CardUpdate.as_view(), name='card_edit'),

    path('departure-add/<int:pk>/', views.DepartureAdd.as_view(), name='departure_add'),
    path('departure/<int:pk>/', views.DepartureDetail.as_view(), name='departure_detail'),
    path('departure-delete/<int:pk>/', views.DepartureDelete.as_view(), name='departure_delete'),
    path('departure-edit/<int:pk>/', views.DepartureUpdate.as_view(), name='departure_edit'),

    path('norms/', views.NormList.as_view(), name='norm_list'),
    path('norm-add/', views.NormAdd.as_view(), name='norm_add'),
    path('norm-delete/<int:pk>/', views.NormDelete.as_view(), name='norm_delete'),
    path('norm-edit/<int:pk>/', views.NormUpdate.as_view(), name='norm_edit'),

    path('report/<int:pk>/', views.ReportDetail.as_view(), name='report_detail'),

    path('short-report/<int:pk>/', views.ShortReport.as_view(), name='short_report'),
    path('short-report_email/<int:pk>/', views.ShortReportEmail.as_view(), name='short_report_email'),
    path('full-report/<int:pk>/', views.FullReport.as_view(), name='full_report'),
    path('full-report_email/<int:pk>/', views.FullReportEmail.as_view(), name='full_report_email'),

    path('', views.home, name='home')
]
