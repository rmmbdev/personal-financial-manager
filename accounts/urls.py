from django.urls import path
from . import views

urlpatterns = [
    # path('login/', views.login_page, name='login'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('change-account/', views.change_account, name='change_account'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('update-personal-details/', views.update_personal_details, name='update_personal_details'),
    path('set-default-account/', views.set_default_account, name='set_default_account'),
    path('create-account/', views.create_account, name='create_account'),
    path('update-account/', views.update_account, name='update_account'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('invite-user/', views.invite_user, name='invite_user'),
    path('accept-invitation/', views.accept_invitation, name='accept_invitation'),
    path('decline-invitation/', views.decline_invitation, name='decline_invitation'),
    path('change-password/', views.change_password, name='change_password'),
]
