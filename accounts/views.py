from django.shortcuts import render, redirect
from django.views.generic import FormView
from .forms import UserRegistrationForm,UserUpdateForm, UserPasswordChangeForm
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View
from django.contrib.auth.views import PasswordChangeView
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def send_update_email(user, subject, message):
    email = EmailMultiAlternatives(
        subject=subject,
        body=message,
        to=[user.email]
    )
    email.send()


class UserRegistrationView(FormView):
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('profile')
    
    def form_valid(self,form):
        print(form.cleaned_data)
        user = form.save()
        login(self.request, user)
        print(user)
        return super().form_valid(form) # form_valid function call hobe jodi sob thik thake
    

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    def get_success_url(self):
        return reverse_lazy('home')

class UserLogoutView(LogoutView):
    def get_success_url(self):
        if self.request.user.is_authenticated:
            logout(self.request)
        return reverse_lazy('home')


class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'
    

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})
    
    

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        user = form.save()
        send_update_email(
        user=self.request.user,
        subject="Password Changed Successfully",
        message="Your password has been updated successfully. If this wasn't you, please contact support immediately."
        )

        return super().form_valid(form)

    
    
    