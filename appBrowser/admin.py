from django.contrib import admin

from .models import PaperInfo, Category

admin.site.register(PaperInfo)
admin.site.register(Category)
