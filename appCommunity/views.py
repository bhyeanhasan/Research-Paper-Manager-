from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.contenttypes.models import ContentType
from .models import Topic, Tag, Post, Comment, Reaction, Attachment


def community(request):
    return render(request, 'Forum.html')


# ---------- Lists ----------

def post_list(request, topic_slug=None, tag_slug=None):
    posts = (Post.objects
             .select_related("author", "topic")
             .prefetch_related("tags")
             .annotate(num_comments=Count("comments"))
             .order_by("-created_at"))

    active_topic = None
    active_tag = None
    if topic_slug:
        active_topic = get_object_or_404(Topic, slug=topic_slug)
        posts = posts.filter(topic=active_topic)

    if tag_slug:
        active_tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags=active_tag)

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ---- like + dislike counts for posts on this page ----
    post_ids = [p.id for p in page_obj.object_list]
    likes_map, dislikes_map = {}, {}
    if post_ids:
        ct_post = ContentType.objects.get_for_model(Post)
        rows = (Reaction.objects
                .filter(content_type=ct_post, object_id__in=post_ids,
                        kind__in=[Reaction.Kind.LIKE, Reaction.Kind.DISLIKE])
                .values("object_id", "kind")
                .annotate(c=Count("id")))
        for r in rows:
            if r["kind"] == Reaction.Kind.LIKE:
                likes_map[r["object_id"]] = r["c"]
            elif r["kind"] == Reaction.Kind.DISLIKE:
                dislikes_map[r["object_id"]] = r["c"]

    for p in page_obj.object_list:
        p.like_count = likes_map.get(p.id, 0)
        p.dislike_count = dislikes_map.get(p.id, 0)

    ctx = {
        "page_obj": page_obj,
        "topics": Topic.objects.order_by("name"),
        "tags": Tag.objects.order_by("name"),
        "active_topic": active_topic,
        "active_tag": active_tag,
    }
    return render(request, "Forum.html", ctx)



def post_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related("author", "topic").prefetch_related("tags"),
        pk=pk,
    )

    # ----- threaded comments (evaluate so we can attach attrs) -----
    reply_qs = Comment.objects.select_related("author").order_by("created_at")
    comments = list(
        Comment.objects.filter(post=post)
        .select_related("author")
        .prefetch_related(Prefetch("replies", queryset=reply_qs))
        .order_by("created_at")
    )
    root_comments = [c for c in comments if c.parent_id is None]

    # ----- reaction data for comments -----
    comment_ids = [c.id for c in comments]
    ct_comment = ContentType.objects.get_for_model(Comment)

    # counts per comment (one query with grouping)
    like_counts_map = {}
    dislike_counts_map = {}
    if comment_ids:
        agg = (
            Reaction.objects
            .filter(content_type=ct_comment, object_id__in=comment_ids)
            .values("object_id", "kind")
            .annotate(c=Count("id"))
        )
        for row in agg:
            if row["kind"] == Reaction.Kind.LIKE:
                like_counts_map[row["object_id"]] = row["c"]
            elif row["kind"] == Reaction.Kind.DISLIKE:
                dislike_counts_map[row["object_id"]] = row["c"]

    # current user's reaction per comment
    my_map = {}
    if request.user.is_authenticated and comment_ids:
        my_map = {
            r["object_id"]: r["kind"]
            for r in (
                Reaction.objects
                .filter(user=request.user, content_type=ct_comment, object_id__in=comment_ids)
                .values("object_id", "kind")
            )
        }

    # attach attributes to each comment instance
    for c in comments:
        c.my_reaction = my_map.get(c.id)                    # 'like' | 'dislike' | None
        c.like_count = like_counts_map.get(c.id, 0)         # int
        c.dislike_count = dislike_counts_map.get(c.id, 0)   # int

    # ----- post-level reaction counts + user's reaction -----
    ct_post = ContentType.objects.get_for_model(Post)
    post_like_count = 0
    post_dislike_count = 0
    for row in (
        Reaction.objects
        .filter(content_type=ct_post, object_id=post.pk)
        .values("kind").annotate(c=Count("id"))
    ):
        if row["kind"] == Reaction.Kind.LIKE:
            post_like_count = row["c"]
        elif row["kind"] == Reaction.Kind.DISLIKE:
            post_dislike_count = row["c"]

    user_post_reaction = None
    if request.user.is_authenticated:
        user_post_reaction = (
            Reaction.objects
            .filter(user=request.user, content_type=ct_post, object_id=post.pk)
            .first()
        )

    ctx = {
        "post": post,
        "root_comments": root_comments,
        "topics": Topic.objects.order_by("name"),
        "tags": Tag.objects.order_by("name"),
        "user_post_reaction": user_post_reaction,
        "post_like_count": post_like_count,
        "post_dislike_count": post_dislike_count,
    }
    return render(request, "forum/post_detail.html", ctx)


# ---------- Create post ----------
@login_required
def post_create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        kind = request.POST.get("kind") or Post.Kind.QUESTION
        topic_id = request.POST.get("topic") or None
        tag_ids = request.POST.getlist("tags")

        if not title or not content:
            messages.error(request, "Title and content are required.")
            return redirect("forum:post_create")

        post = Post.objects.create(
            author=request.user,
            title=title,
            content=content,
            kind=kind,
            topic_id=topic_id or None
        )
        if tag_ids:
            post.tags.set(tag_ids)

        # ✅ handle attachments
        for f in request.FILES.getlist("attachments"):
            Attachment.objects.create(post=post, file=f, name=f.name)

        messages.success(request, "Post created.")
        return redirect("post_detail", pk=post.pk)

    return render(request, "forum/post_form.html", {
        "topics": Topic.objects.order_by("name"),
        "tags": Tag.objects.order_by("name"),
        "kinds": Post.Kind.choices,
    })


# ---------- Add comment / reply ----------
@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        parent_id = request.POST.get("parent") or None
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                parent_id=parent_id,
                content=content
            )
            messages.success(request, "Comment added.")
    return redirect("post_detail", pk=post.pk)


# ---------- Reactions (like / dislike) ----------
@login_required
def react_post(request, pk, kind):
    # kind must be like or dislike
    if kind not in (Reaction.Kind.LIKE, Reaction.Kind.DISLIKE):
        messages.error(request, "Invalid reaction.")
        return redirect("post_detail", pk=pk)

    post = get_object_or_404(Post, pk=pk)
    ct = ContentType.objects.get_for_model(Post)
    existing = Reaction.objects.filter(
        user=request.user, content_type=ct, object_id=post.pk
    ).first()

    if existing and existing.kind == kind:
        # toggling off
        existing.delete()
    elif existing:
        existing.kind = kind
        existing.save(update_fields=["kind", "updated_at"])
    else:
        Reaction.objects.create(
            user=request.user, content_type=ct, object_id=post.pk, kind=kind
        )
    return redirect("post_detail", pk=post.pk)


@login_required
def react_comment(request, pk, kind):
    if kind not in (Reaction.Kind.LIKE, Reaction.Kind.DISLIKE):
        messages.error(request, "Invalid reaction.")
        # find the comment's post to redirect back properly
        c = get_object_or_404(Comment.objects.select_related("post"), pk=pk)
        return redirect("post_detail", pk=c.post_id)

    comment = get_object_or_404(Comment.objects.select_related("post"), pk=pk)
    ct = ContentType.objects.get_for_model(Comment)
    existing = Reaction.objects.filter(
        user=request.user, content_type=ct, object_id=comment.pk
    ).first()

    if existing and existing.kind == kind:
        existing.delete()
    elif existing:
        existing.kind = kind
        existing.save(update_fields=["kind", "updated_at"])
    else:
        Reaction.objects.create(
            user=request.user, content_type=ct, object_id=comment.pk, kind=kind
        )
    return redirect("post_detail", pk=comment.post_id)
