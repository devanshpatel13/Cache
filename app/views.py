from django.http import JsonResponse
from django.dispatch import receiver
from django.db.models.signals import post_save
from requests import Response

import cache as cache
from django.shortcuts import render
from rest_framework import viewsets, request, generics, status
from django.core.cache import cache
from .models import *
from .serializers import *
from django.core.cache import cache


# Create your views here.


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def retrieve(self, request, *args, **kwargs):
        key = 'get_student_' + str(kwargs['pk'])
        print(key, "keyyyyy###################################################")
        cache_data = cache.get(key)
        if not cache_data:
            data = Student.objects.get(id=kwargs['pk'])
            serializer = StudentSerializer(data)
            stud_data = serializer.data
            cache.set(key, stud_data)
            return JsonResponse(stud_data, safe=False)
        else:
            return JsonResponse(cache_data, safe=False)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer, "dddddddddddddddddddddddddd")

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # key = 'get_student_' + str(kwargs['pk'])
        # cache_dsta = cache.get(key)
        print()
        if serializer:
            stud_data = serializer.data
            print(stud_data, "ggggggggggggggggggggggggggg")
            data = stud_data['id']
            print(data, "lqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
            key = 'get_student_' + str(data)

            cache.set(key, stud_data)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # print("instance", instance)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        print(instance, "ddddddddddddddddddddddddddddddddddddddddddddddddddddddddd")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        key = 'get_student_' + str(kwargs['pk'])
        print(key, "_______________-------------------------____________")
        cache_data = cache.get(key)
        print(cache_data, "#################3+==========================33333#######")
        if cache_data and cache_data['id'] == int(kwargs['pk']):
            cache.delete(key)
            print(cache_data, type(cache_data), '-============')

        return JsonResponse(serializer.data)



    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance, '---------')
        # super(StudentViewSet, self).destroy()
        self.perform_destroy(instance)
        return JsonResponse({'msg':'message'})
    # @receiver(post_save ,sender =Student)
    # def at_ending_save(sender, instance , created,**kwargs):
    #     if created:
    #         print("--------------------------")
    #         print(" Post-Save siganl")
    #         print(" New one is added")
    #         print("Sender:", sender)
    #         print("instance", instance)
    #         print("Created :", created)
    #         print(f'kwargs: {kwargs}')
    #     else:
    #         print("--------------------------")
    #         print(" Post save siganl ")
    #         print("update record")
    #         print("Sender:", sender)
    #         print("instance", instance)
    #         print(f'kwargs: {kwargs}')


# class StudentViewSet(generics.ListCreateAPIView):
#     queryset = Student.objects.all()
#     serializer_class = StudentSerializer
#
#     def get(self, request, *args, **kwargs):
#         key = 'get_student_' + str(kwargs['pk'])
#         cache_data = cache.get(key)
#         if not cache_data:
#             data = Student.objects.all()
#             serializer = StudentSerializer(data, many=True)
#             stud_data = serializer.data
#             cache.set(key, stud_data)
#             return JsonResponse(stud_data, safe=False)
#         else:
#             return JsonResponse(cache_data, safe=False)
#
#     def post(self, request, *args, **kwargs):
#
#         data = ' cache get' + str(kwargs['pk'])
#         cache.set(data)


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

#
# def entries_on_ a_day(request,year,month,day):
#     creationdate=new date(year,get_month_as_number(month),day)
#     key = request.user.username+ str(creationdate)
#     if key not in cache:
#         entries_for_date = Entry.objects.filter(creationdate__year=year,creationdate__month=get_month_as_number(month),creationdate__day=day,author=request.user).order_by('-creationdate')
#         cache.set(key,entries_for_date)
#     entries =  cache.get(key)
#     ....
