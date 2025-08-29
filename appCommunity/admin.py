from django.contrib import admin

from .models import Post, Topic, Tag, Attachment, Comment, Reaction

admin.site.register(Post)
admin.site.register(Topic)
admin.site.register(Attachment)
admin.site.register(Comment)
admin.site.register(Reaction)
admin.site.register(Tag)
