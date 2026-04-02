from django.urls import path

from . import views

urlpatterns = [path("index.html", views.index, name="index"),
	       path('Login.html', views.Login, name="Login"), 
	       path('Register.html', views.Register, name="Register"),
	       path('Signup', views.Signup, name="Signup"),
	       path('UserLogin', views.UserLogin, name="UserLogin"),
	       path('PostTopic.html', views.PostTopic, name="PostTopic"),
	       path('PostMyTopic', views.PostMyTopic, name="PostMyTopic"),	       
	       path('AdminLogin.html', views.AdminLogin, name="AdminLogin"),
	       path('AdminLoginAction', views.AdminLoginAction, name="AdminLoginAction"),
	       path('ViewOffensive', views.ViewOffensive, name="ViewOffensive"),	
	       path('BlockUser', views.BlockUser, name="BlockUser"),	
	       path('TrainML', views.TrainML, name="TrainML"),	
]