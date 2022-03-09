from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django import forms
from . import models as m


class LoginForm(forms.Form):
    username = forms.EmailField(widget = forms.EmailInput(attrs={'rows':1, 'cols':35}))
    password = forms.CharField(widget = forms.PasswordInput(attrs={'rows':1, 'cols':35}))


class MyUserCreateForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = get_user_model()
        fields = ('email', 'can_notify', 'groups',)


class MyUserChangeForm(UserChangeForm):

    class Meta:
        model = get_user_model()
        fields = ('email', 'can_notify', 'groups',)


class DashboardCreateForm(forms.ModelForm):
    class Meta: 
       model = m.Dashboard
       fields = ['owner']

class DashboardChangeForm(forms.ModelForm):
    class Meta: 
       model = m.Dashboard
       fields = ['owner']