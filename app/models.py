from datetime import date

from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver

import cache


class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_no = models.IntegerField()
    std = models.IntegerField()



class Teacher(models.Model):
    name = models.CharField(max_length=100)
    contact = models.IntegerField()
    sub = models.CharField(max_length=100)

