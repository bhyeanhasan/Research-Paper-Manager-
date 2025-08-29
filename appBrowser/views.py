from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import PaperInfo, Category
from django.db.models import Q
from appDiscussion.models import Comment


# Create your views here.
def home(request):
    papers = PaperInfo.objects.filter(Q(visibility='public') | Q(owner=request.user))
    categories = Category.objects.all()
    return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})


# Create your views here.
def personal_library(request):
    papers = PaperInfo.objects.filter(Q(owner=request.user))
    categories = Category.objects.all()
    return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})


def sorted_name(request):
    papers = PaperInfo.objects.filter(Q(visibility='public') | Q(owner=request.user))
    categories = Category.objects.all()
    return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})


def category(request, id):
    papers = PaperInfo.objects.filter(category__in=id)
    categories = Category.objects.all()
    return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})


# def read(request, id):
#     paper = PaperInfo.objects.get(id=id)
#     categories = Category.objects.all()
#     comments = Comment.objects.filter(paper=paper)
#     return render(request, 'read.html', {'paper': paper, 'categories': categories, 'comments': comments})


from django.shortcuts import get_object_or_404, render
from django.db.models import Prefetch


def read(request, id):
    paper = get_object_or_404(PaperInfo, id=id)
    categories = Category.objects.all()

    # Prefetch replies (and authors) so templates don't cause N+1 queries
    reply_qs = Comment.objects.select_related("author").order_by("created_at")

    all_comments = (
        Comment.objects
        .filter(paper=paper)
        .select_related("author")  # author for each comment
        .prefetch_related(Prefetch("replies", queryset=reply_qs))
        .order_by("created_at")
    )

    root_comments = [c for c in all_comments if c.parent_id is None]

    return render(
        request,
        "read.html",
        {
            "paper": paper,
            "categories": categories,
            "root_comments": root_comments,  # use this in the template
        },
    )


@login_required
def add_comment(request, pk):
    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        parent_id = request.POST.get("parent") or None
        if content:
            Comment.objects.create(
                paper_id=pk,
                author=request.user,
                parent_id=parent_id,
                content=content,
            )
    return redirect("read", id=pk)


def search(request):
    if request.method == 'POST':
        search_query = request.POST['key']
        papers = PaperInfo.objects.filter(title__contains=search_query)
        categories = Category.objects.all()
        return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})
    else:
        return redirect('ok')
