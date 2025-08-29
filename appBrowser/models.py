from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.now())

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.now())

    def __str__(self):
        return self.name

class PaperInfo(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    title = models.CharField(max_length=200, null=True, blank=True, default='Not set')
    description = models.TextField(max_length=1000, null=True, blank=True, default='Not set')
    file = models.FileField(upload_to='media/')
    category = models.ManyToManyField(Category, blank=True, null=True)
    tag = models.ManyToManyField(Tag, blank=True, null=True)
    doi = models.CharField(max_length=200, null=True, blank=True, default='Not set')
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_read = models.IntegerField(default=0)
    total_downloaded = models.IntegerField(default=0)
    owner = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)

    def __str__(self):
        return self.title
