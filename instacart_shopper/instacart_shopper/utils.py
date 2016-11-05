import random, string, time, datetime
from collections import OrderedDict 
from django.core.cache import cache
import logging

from .models import Shopper

logger = logging.getLogger('instacart_shopper')

# List of workflow_states to pick from for seed data
WORKFLOW_STATES = ["applied", "quiz_started", "quiz_completed", "onboarding_requested", "onboarding_completed", "hired", "rejected"]

# List of some locations to pick from for seed data
SERVICE_LOCATION_CHOICES = {'Atlanta':'GA', 'Scottdale' : 'GA', 'San Francisco': 'CA', 'San Jose': 'CA', 'Menlo Park' : 'CA','Denver': 'CO', 'Chicago': 'IL', 'Indianapolis' : 'IN', 'Cambridge': 'MA','New York' : 'NY' }

def get_closest_prev_monday(date):
	return (date - datetime.timedelta(days=int(date.weekday())))

def get_closest_next_sunday(date):
	return (date + datetime.timedelta(days=6-int(date.weekday())))

def get_funnel_all_weeks(start_date, end_date):
    closest_prev_monday = get_closest_prev_monday(start_date)
    closest_next_sunday = get_closest_next_sunday(end_date)
    
    weekly_dict = OrderedDict()
    curr_date = closest_prev_monday
    while curr_date <= closest_next_sunday:
    	#Dictionary here contains kv pairs of {Monday, next Sunday}
    	weekly_dict[curr_date] = curr_date + datetime.timedelta(days=6)
        #Increment it to the next monday (+7 days)
        curr_date += datetime.timedelta(days=7)
        
    return weekly_dict

def get_week_key(week_start, week_end):
	return str(week_start) + "-" + str(week_end)

def invalidate_cache(date):
	'''
	If an application comes for the current week, invalidate the week's entry from cache
	'''
	closest_prev_monday = get_closest_prev_monday(date)
	closest_next_sunday = get_closest_next_sunday(date)
	key = get_week_key(closest_prev_monday.strftime("%Y-%m-%d"), closest_next_sunday.strftime("%Y-%m-%d"))
	logger.info("Invalidating the cache key : %s", key)
	cache.delete(key)

def generate_random_string(length):
	return ''.join(random.choice(string.lowercase) for i in range(length))

def generate_random_location():
	return random.choice(list(SERVICE_LOCATION_CHOICES.keys()))

def generate_random_number(length):
	return int(''.join(random.choice(string.digits) for i in range(length)))

def generate_random_date():
	# 01 Jan 2010 00:00:01 GMT
	start_time = 1262304001  
	# 31 Dec 2014 23:59 59 GMT
	end_time = 1420070399  
	time_val = random.randint(start_time, end_time)
	return time.strftime('%Y-%m-%d', time.localtime(time_val))

def generate_random_status():
	return random.choice(WORKFLOW_STATES)

def generate_seed_data_populate_db(count):
	# count of users saved in db
	registeredCount = 0
	# upperLimitCount is the max number of tries to insert seed data in case random function generates duplicat phone/ email
	upperLimitCount = 2 * count
	
	for i in range(upperLimitCount):
		# If we have generated given count of test shoppers, break
		if registeredCount == count:
			break

		name = generate_random_string(10)
		email = generate_random_string(10) + '@gmail.com'
		phone = generate_random_number(10)
		city = generate_random_location()
		state = SERVICE_LOCATION_CHOICES[city]
		date_applied = generate_random_date()
		status = generate_random_status()
		shopper = Shopper(name=name, email=email, phone=phone, city=city, state=state, application_date=date_applied, workflow_state=status)

		# Verify that same email or phone numbers are not inserted again
		if not Shopper.objects.filter(email=email).exists() and not Shopper.objects.filter(phone=phone).exists():
			registeredCount += 1
			shopper.save()


