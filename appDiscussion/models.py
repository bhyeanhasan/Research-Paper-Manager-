from django.db import models
from django.conf import settings
from appBrowser.models import PaperInfo

class Comment(models.Model):
    paper = models.ForeignKey(
        PaperInfo,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paper_comments",
    )
    parent = models.ForeignKey(
        "self",
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["paper", "created_at"]),
            models.Index(fields=["parent", "created_at"]),
        ]

    def __str__(self):
        preview = (self.content[:30] + "…") if len(self.content) > 30 else self.content
        return f"{preview} ({self.author})"
