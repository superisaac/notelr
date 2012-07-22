from django.contrib.auth.models import User
from enote.models import *


def install_sample():
    user = User.objects.create_user('zengke', 'zk@test.com')
    user.set_password('1111')
    user.save()
    auth_token = 'S=s1:U=276b7:E=13f8a96a364:C=13832e57764:P=1cd:A=en-devtoken:H=db9b23a7bc6d99da8531371fd0b36923'
    profile = ENoteProfile.objects.create(user=user, auth_token=auth_token)

if __name__ == '__main__':
    install_sample()
    
