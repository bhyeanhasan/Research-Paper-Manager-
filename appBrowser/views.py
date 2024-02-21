from django.shortcuts import render, redirect
from .models import PaperInfo, Category


# Create your views here.
def home(request):
    papers = PaperInfo.objects.all()
    categories = Category.objects.all()
    return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})


def sorted_name(request):
    papers = PaperInfo.objects.order_by('title')
    categories = Category.objects.all()
    return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})


def category(request, id):
    papers = PaperInfo.objects.filter(category__in=id)
    categories = Category.objects.all()
    return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})


def read(request, id):
    paper = PaperInfo.objects.get(id=id)
    categories = Category.objects.all()
    return render(request, 'read.html', {'paper': paper, 'categories': categories})


def search(request):
    if request.method == 'POST':
        search_query = request.POST['key']
        papers = PaperInfo.objects.filter(title__contains=search_query)
        categories = Category.objects.all()
        return render(request, 'dashboard.html', {'papers': papers, 'categories': categories})
    else:
        return redirect('ok')
