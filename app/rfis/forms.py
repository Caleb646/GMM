from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import MyUser


class MyUserCreateForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = MyUser
        fields = ('email', 'groups',)


class MyUserChangeForm(UserChangeForm):

    class Meta:
        model = MyUser
        fields = ('email', 'groups',)