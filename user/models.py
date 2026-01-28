from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []  # phone & password only

    objects = UserManager()

    def __str__(self):
        return self.phone
