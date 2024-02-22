from datetime import datetime

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.now())

    def __str__(self):
        return self.name


class PaperInfo(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True, default='Not set')
    description = models.TextField(max_length=1000, null=True, blank=True, default='Not set')
    file = models.FileField(upload_to='media/',max_length=500)
    category = models.ManyToManyField(Category, blank=True, null=True)

    def __str__(self):
        return self.title
