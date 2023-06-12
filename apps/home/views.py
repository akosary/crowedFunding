# from asyncio.windows_events import NULL
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.db.models import Avg, Sum
from collections import defaultdict
from datetime import datetime
import re
from apps.home.models import Category, Comment, Donation, Project, Image, Project_Report, Rate, Reply, Tag, Comment_Report
from apps.home.forms import Project_Form, Report_form, Reply_form, Category_form
from django.forms.utils import ErrorList
from apps.authentication.models import Register
NULL={}

def getUser(request):
        user = Register.objects.get(id=request.session['user_id'])
        return user
    

def add_category(request):
    if 'user_id' not in request.session:
        user = NULL
        return redirect('login')
    else:
        user = getUser(request)
        categories = Category.objects.all()

        if request.method == 'GET':
            form = Category_form()
            return render(request, "home/category_form.html", context={'form': form})
        if request.method == 'POST':
            form = Category_form(request.POST)

            if form.is_valid():
                new_category = request.POST['name']
                for category in categories:
                    if category.name == new_category:

                        error = ' not valid'

                        return render(request, "home/category_form.html", context={'form': form, 'form_error': error})

                form.save()
                return redirect('home')


def search(request):
    if 'user_id' not in request.session:
        user = NULL
    else:
        user = getUser(request)
    context = {}
    try:
        search_post = request.GET.get('search')

        if len(search_post.strip()) > 0:
            projects = Project.objects.filter(title__icontains=search_post)
            searched_tags = Tag.objects.filter(name__icontains=search_post)

            donations = []
            progress_values = []
            images = []
            for project in projects:
                donate = project.donation_set.all().aggregate(Sum("donation"))
                total_donation = donate["donation__sum"] if donate["donation__sum"] else 0

                progress_values.append(
                    total_donation * 100/project.total_target)
                donations.append(total_donation)
                images.append(project.image_set.all().first().images.url)

            context = {
                'projects': projects, 
                'tags': searched_tags, 
                'images': images,
                'donations': donations,
                'progress_values': progress_values,
                'user':user}

            if(len(projects) <= 0):
                context.update(
                    {'title': 'No Projects Found for "'+search_post+'"'})
            if(len(searched_tags) <= 0):
                context.update(
                    {'title_tags': 'No Tags Found for "'+search_post + '"'})

            return render(request, "home/search-result.html", context)
        else:
            return render(request, "home/index.html", context)

    except Project.DoesNotExist:
        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))


def rate(request, project_id):
    if 'user_id' not in request.session:
        user = NULL
        return redirect('login')
    else:
        user = getUser(request)
        if request.method == "POST":
            project = get_object_or_404(Project, pk=project_id)
            context = {"project": project}

            rate = request.POST.get('rate', '')

            if rate and rate.isnumeric():

                apply_rating(project, user.id, rate)

        return redirect('show_project', project_id)


def apply_rating(project, user, rating):

    prev_user_rating = project.rate_set.filter(user_id=user)
    if prev_user_rating:
        prev_user_rating[0].rate = int(rating)
        prev_user_rating[0].save()

    else:
        Rate.objects.create(
            rate=rating, projcet_id=project.id, user_id=user)


def cancel_project(request, project_id):
    if 'user_id' not in request.session:
        user = NULL
        return redirect('login')
    else:
        user = getUser(request)
        if request.method == 'POST':
            project = get_object_or_404(Project, pk=project_id)

            donate = project.donation_set.all().aggregate(Sum("donation"))
            donation = donate["donation__sum"] if donate["donation__sum"] else 0
            total_target = project.total_target
            
            if donation < total_target*.25:
                project.delete()
                return redirect("profile")
            else:
                return redirect('show_project', project_id)
                

def pages(request):  
    if 'user_id' not in request.session:
        user = NULL
    else:
        user = getUser(request)     
    context = {}
    try : 
        load_template = request.path.split('/')[-1]
        if load_template == 'admin':
                return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template
        context['user'] = user

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:
            html_template = loader.get_template('home/page-404.html')
            return HttpResponse(html_template.render(context, request))
