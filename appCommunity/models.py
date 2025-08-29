# forum/models.py
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class Topic(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:120]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(TimeStampedModel):
    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:60]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(TimeStampedModel):
    class Kind(models.TextChoices):
        QUESTION = "question", "Question"
        DISCUSSION = "discussion", "Discussion"
        News = "news", "News"
        Update = "Update", "Update"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="posts"
    )
    title = models.CharField(max_length=180)
    content = models.TextField()  # Markdown or plain text
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.QUESTION)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["kind", "-created_at"]),
            models.Index(fields=["topic", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]

    def __str__(self):
        return self.title


class Comment(TimeStampedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="comments"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]  # oldest→newest per thread
        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["parent", "created_at"]),
            models.Index(fields=["author", "created_at"]),
        ]

    def __str__(self):
        txt = (self.content or "").replace("\n", " ").strip()
        return f"{self.author or 'Anon'}: {txt[:30]}{'…' if len(txt) > 30 else ''}"


class Reaction(TimeStampedModel):
    class Kind(models.TextChoices):
        LIKE = "like", "Like"
        DISLIKE = "dislike", "Dislike"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")

    kind = models.CharField(
        max_length=8,
        choices=Kind.choices,
    )

    class Meta:
        constraints = [
            # user can react only once per target
            models.UniqueConstraint(
                fields=["user", "content_type", "object_id"],
                name="unique_reaction_per_user_and_target",
            )
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} by {self.user}"


class Attachment(TimeStampedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/")
    name = models.CharField(max_length=140, blank=True)

    def __str__(self):
        return self.name or self.file.name


