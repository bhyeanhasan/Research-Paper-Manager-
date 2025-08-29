from django.contrib import admin

from .models import PaperInfo, Category,Tag

admin.site.register(PaperInfo)
admin.site.register(Category)
admin.site.register(Tag)
