from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib import messages
from django.template import Context
from django.utils import timezone
import time, json

from .models import Shopper
from .utils import *
from .funnel import *


def home(request):
	'''
		/home is the landing page of the application
	'''
	return render(request,'instacart_shopper/home.html')


def register(request):
	'''
	POST API which receives the request for shopper registration.
	This API verifies that email and phone number don't match with any other existing applicant,  
	sets the user session details and redirects the user to background check page.
	'''

	if request.POST:
		#Obtain form data from the request and store in session variables so they can be accessed across functions
		user_info = request.POST
		is_valid_user = True

		if Shopper.objects.filter(email = user_info['email']).exists():
			is_valid_user = False
			error_message = "This email is already registered!"
			logger.error("This email is already registered. Email : %s", user_info['email'])
			messages.add_message(request, messages.ERROR, error_message)			

		if Shopper.objects.filter(phone = user_info['phone']).exists():
			is_valid_user = False
			error_message = "This phone number is already registered!"
			logger.error("This phone number is already registered. Phone : %s", user_info['phone'])
			messages.add_message(request, messages.ERROR, error_message)
		
		if not is_valid_user:			
			return render(request, 'instacart_shopper/home.html')

		# If the user is valid, set the user session details
		request.session['name'] = user_info['name']
		request.session['email'] = user_info['email']
		request.session['phone'] = user_info['phone']
		request.session['city'] = user_info['city']
		request.session['state'] = user_info['state']

		# Redirect the user to background check consent form
		return render(request,'instacart_shopper/background_check.html')				

	
def confirmation(request):
	'''
	POST API which saves the user credentials from request.session.
	Once the user is registered, session objects are cleared except for email.
	'''	
	if request.POST:
		# Check if the user is already registered 
		shopper = Shopper.objects.filter(email=request.session['email'])
		if shopper:
			context = Context({'shopper': shopper[0]})
			return render(request,'instacart_shopper/confirmation_page.html',context)

		# Invalidate the cache for current week for funnel metrics as we got a new applicant
		invalidate_cache(timezone.now())

		# Register the user and save user information in database
		name = request.session['name']
		email = request.session['email']
		phone = request.session['phone']
		city = request.session['city']
		state = request.session['state']
		shopper = Shopper(name=name, email=email, phone=phone, city=city, state=state)
		shopper.save()
		context = Context({'shopper' : shopper})
		
		# Delete all user's session data except for 'email' which is used to maintain user-session
		del request.session['name'] 
		del request.session['phone'] 
		del request.session['city']
		del request.session['state'] 

		logger.info("New shopper registered. Email : %s", email)

		# Redirect user to the registration confirmation page
		return render(request,'instacart_shopper/confirmation_page.html',context)


def login(request):
	'''
	This POST API lets the user track an existing application
	'''
	if request.POST:
		email = request.POST['email']
		if not email:
			error_message = "Please enter a valid email."
			logger.error(error_message)
			messages.add_message(request, messages.ERROR, error_message)
			return render(request,'instacart_shopper/home.html')
		else:
			if(Shopper.objects.filter(email=email).exists()):
				shopper = Shopper.objects.filter(email=email)[0]

				# Set the user's email in session
				request.session['email'] = shopper.email
				context = Context({'shopper': shopper})
				return render(request,'instacart_shopper/login.html', context)
			else:
				logger.error("No application found for email : %s", email)
				messages.add_message(request, messages.ERROR, "Sorry, there is no application with this email.")
				return render(request,'instacart_shopper/home.html')


def edit(request):	
	shopper = Shopper.objects.filter(email=request.session['email'])
	context = Context({'shopper': shopper[0]})
	return render(request,'instacart_shopper/edit_application.html', context)


def update(request):
	'''
	This POST API updates the user credentials.
	'''

	# Fetch the user details from db based on session.email key
	shopper = Shopper.objects.filter(email=request.session['email'])[0]

	'''
	2 Users cannot have same phone number.
	If the input phone number is different from the registered phone:
		check if the new phone number is not registered with another existing user
	''' 
	if shopper.phone != int(request.POST['phone']) and Shopper.objects.filter(phone = int(request.POST['phone'])).exists():
		logger.error("Phone number already registered with a different user. Phone no. : %s", request.POST['phone'])
 		messages.add_message(request, messages.ERROR, "Phone number already registered with a different user")
 		context = Context({'shopper': shopper})
 		return render(request,'instacart_shopper/edit_application.html',context)
	
	shopper.name = request.POST['name']
	shopper.phone = request.POST['phone']
	shopper.city = request.POST['city']
	shopper.state = request.POST['state']
	shopper.save()
	context = Context({'shopper': shopper})
	return render(request,'instacart_shopper/login.html',context)


def logout(request):
	'''
	This POST API clears user's session and redirects user to home page of the application.
	'''
	try:
		del request.session['email']
	except Exception as e:
		logger.error("Failed to delete session. Email : %s, Error : %s", request.session['email'], str(e))
	return render(request,'instacart_shopper/home.html')


def funnel_metrics(request):
	'''
	This GET API takes the start_date and end_date as query params.
	Generates the workflow_states with count of applicants grouped by the week in which they applied.
	'''
	try:		
		request_params = request.GET
		if len(request_params) != 2:
			logger.error("Input params are invalid. API expects 2 params. Provided " + str(len(request_params)) + " params")
			raise Exception("Input params are invalid. API expects 2 params. Provided " + str(len(request_params)) + " params")

		start_time = time.time()
		funnel_report = generate_funnel_report(request_params)
		logger.info("Total time taken to generate the funnel report : %s secs", (time.time()-start_time)/1000000)
		return HttpResponse(json.dumps(funnel_report), content_type="application/json")
	except Exception as e:		
		logger.error("Failed to fetch the funnel report. Error : %s", str(e))
		return HttpResponseBadRequest(e.message)		


def insert_seed_data(request,count):
	'''
	This GET API is the helper method to generated some seed data to test funnel_metrics API.
	It takes a count as input and generates that many applicants with random seed data.
	'''
	generate_seed_data_populate_db(int(count))
	return HttpResponse('Seed data loaded successfully!')









