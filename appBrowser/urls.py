from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='ok'),
    path('personal_library/', views.personal_library, name='mylibrary'),
    path('sort', views.sorted_name, name='sorted_name'),
    path('view/<id>', views.read, name='read'),
    path('category/<id>', views.category, name='category'),
    path('search', views.search, name='search'),
    path("papers/<int:pk>/comment/", views.add_comment, name="add_comment"),
]
