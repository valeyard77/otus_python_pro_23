from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .views import signup, profile

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(redirect_authenticated_user=True, template_name="accounts/login.html"), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('accounts:login')), name='logout'),
    path('profile/', profile, name='profile'),
]
