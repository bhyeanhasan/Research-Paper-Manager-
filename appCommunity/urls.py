from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path("", views.post_list, name="community"),
    path("topic/<slug:topic_slug>/", views.post_list, name="post_list_by_topic"),
    path("tag/<slug:tag_slug>/", views.post_list, name="post_list_by_tag"),

    path("post/new/", views.post_create, name="post_create"),
    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path("post/<int:pk>/comment/", views.add_comment, name="add_comment"),

    path("post/<int:pk>/react/<str:kind>/", views.react_post, name="react_post"),
    path("comment/<int:pk>/react/<str:kind>/", views.react_comment, name="react_comment"),
]