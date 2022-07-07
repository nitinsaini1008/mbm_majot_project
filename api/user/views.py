from django.shortcuts import render
import random
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer, UserGetSerializer
from .models import CustomUser
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login,logout
import re
import requests
import json

# Create your views here.
def generate_session_token(length=10):
    return ''.join(random.SystemRandom().choice([chr(i) for i in range(97,123)]
    + [str(i) for i in range(10)]) for _ in range(10))

@csrf_exempt
def signin(request):
    if not request.method == 'POST':
        return JsonResponse({'error':'Send a post  request with valid parameter'})

    username = request.POST['email']
    password = request.POST['password']

    if not re.match("[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?",username):
        return JsonResponse({'error':'Enter valid email'})
    
    if len(password)<3:
        return JsonResponse({'error':'password needs to be atleast 3 characters'})

    UserModel = get_user_model()

    try:
        user = UserModel.objects.get(email=username)
        if user.check_password(password):
            usr_dict = UserModel.objects.filter(email=username).values().first()
            usr_dict.pop('password')

            if user.session_token != '0':
                user.session_token = '0'
                user.save()
                return JsonResponse({'error':'Previous session exists'})

            token = generate_session_token()
            user.session_token = token
            user.save()

            login(request,user)
            return JsonResponse({'token':token,'user':usr_dict})
        else:
            return JsonResponse({'error':'Invalid password'})

    except UserModel.DoesNotExist:
        return JsonResponse({'error':'Invalid email'})


def signout(request,id):
    logout(request)

    UserModel = get_user_model()

    try:
        user = UserModel.objects.get(pk=id)
        user.session_token = '0'
        user.save()
    except:
        return JsonResponse({'error':'Invalid user id'})

    return JsonResponse({'success':'Logout successful'})


class UserViewSet(viewsets.ModelViewSet):
    permission_classes_by_action = {'create':[AllowAny]}

    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = UserSerializer

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

def google_login(request):
    code=request.GET['code']
    state=request.GET['state']

    url='https://oauth2.googleapis.com/token'
    data = {'grant_type':'authorization_code',
            'code':code,
            'redirect_uri':'http://127.0.0.1:8000/api/user/google-login/',
            'client_id':'296287171867-r0qicomfln1pfkhjcjdvlu8cmuses21o.apps.googleusercontent.com',
            'client_secret':'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'
            }
    r=requests.post(url,data=data)
    token=r.json()['access_token']
    id_token=r.json()['id_token']
    url='https://oauth2.googleapis.com/tokeninfo?id_token='+id_token
    url = "https://www.googleapis.com/oauth2/v2/userinfo?access_token="+token
    r = requests.get(url)
    data = r.json()
    # print( data['email'], data['name'], data['id'])
    username = data['email']
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(email=username)
    except:
        user = UserModel(email=username, name=username.split("@")[0])
        user.save()
        user.set_password(username+"1234")
        user.save()

    token = generate_session_token()
    user.session_token = token
    user.save()


    user_data = UserGetSerializer(user).data

    login(request,user)
    return JsonResponse({'token':token,'user':user_data})