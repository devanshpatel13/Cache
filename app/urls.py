from django.contrib import admin
from django.urls import path, include
from rest_framework import routers


from app.views import StudentViewSet,TeacherViewSet

from rest_framework import routers

router = routers.DefaultRouter()
router.register("student", StudentViewSet , basename = "student")
router.register("teacher", TeacherViewSet, basename="teacher")

urlpatterns = [

    path('', include(router.urls)),
    # path("student", StudentViewSet.as_view(), name="student"),
    path('auth', include('rest_framework.urls', namespace='rest_framework'))
]
