from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout, name='logout'),
    path('update-role/<int:pk>/', views.update_role, name='update_role'), 
    path('delete-user/<int:pk>/', views.delete_user, name='delete_user'),  
    path("update-user/<int:pk>/", views.update_user),

    path('get-users/', views.get_users, name='get_users'),
    path("demo-request/", views.create_demo_request, name="demo_request"),
    path("activate-demo/<int:pk>/", views.activate_demo, name="activate_demo"),
    path("demo-users/", views.get_demo_users, name="get_demo_users"),
    path('deactivate-user/<int:pk>/', views.deactivate_user, name='deactivate_user'),
]