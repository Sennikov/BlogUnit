from django.urls import path

# from mysait.urls import urlpatterns
from .import views

from .uploader import markdown_uploader

app_name = 'blog'

urlpatterns = [
    #Главная страница сайта!
    path('', views.home, name='home'),

    path('search/', views.search, name='search'),
    path('uploader/', markdown_uploader, name='markdown_uploader'),

    path('admin-deploy/', views.admin_deploy_view, name='admin_deploy'),

    path('ads/click/<int:pk>/', views.ad_click, name='ad_click'),
    path('ads/impression/<int:pk>/', views.ad_impression, name='ad_impression'),

    path('preview/<int:pk>/', views.preview_post, name='preview_post'),

    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    # Один маршрут для категорий и страниц
    path('<slug:slug>/', views.slug_detail, name='slug_detail'),

    #Статьи
    path('<slug:category_slug>/<slug:post_slug>/', views.post_detail, name='post_detail'),

]