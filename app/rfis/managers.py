from django.contrib.auth.base_user import BaseUserManager


class MyUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **kwargs):
        """
        Create and save a User with the given email and password.
        """  
        if not email or not password:
            raise ValueError(('Email and password must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save()
        
        return user

    def create_superuser(self, email, password, **kwargs):
        """
        Create and save a SuperUser with the given email and password.
        """
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)
        return self.create_user(email, password, **kwargs)

    def reset_password(self, password):
        self.set_password(password)
        self.save()


