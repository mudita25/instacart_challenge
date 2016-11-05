from django.db.models import Count
import datetime, collections

from .models import Shopper
from .utils import *

class FunnelError(Exception):
	'''
	Exception raised for errors in the funnel service.
	Attributes:
	    message - error message explanation
	'''
    def __init__(self, message):
        self.message = message

def generate_funnel_report(request_params):
 	start_date = None
 	end_date = None

 	# Check if the input dates are valid.
 	# Extract start and end date from funnel request and convert them from string to Date(YYYY-mm-dd)
	try:
		start_date_str = request_params['start_date']
		end_date_str = request_params['end_date']
		start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
		end_date = datetime.datetime.strptime(end_date_str , '%Y-%m-%d').date()	
	except Exception as e:
		logger.error("Error while parsing start and end dates. Error : %s", str(e))
		raise FunnelError("Input dates are invalid. Please check and try again. Input is start_date: " + start_date_str + ", end_date: " + end_date_str)

	# Check if start_date > end_date, then input is invalid. Start date should be less than or equal to end date
	if start_date > end_date:
		raise FunnelError("Input dates are invalid. start_date cannot be after end_date")		

	# OrderedDict to maintain the order of weeks
	funnel_metrics = collections.OrderedDict()
	all_weeks = get_funnel_all_weeks(start_date, end_date)	
	
	for week_start, week_end in all_weeks.iteritems():
		week_key = get_week_key(week_start, week_end)

		# Check if the key for the given week already exists in the cache. If yes, re-use it.
		weekly_workflow_stats = cache.get(week_key)
		if not weekly_workflow_stats:			
			# Cache miss: If the key is not found in cache, fetch the latest results from DB and update the cache.
			shoppers_states = Shopper.objects.filter(application_date__range=(week_start, week_end)).values('workflow_state').annotate(count=Count('workflow_state'))

			if shoppers_states:		
				weekly_workflow_stats = {}
				for state in shoppers_states:
					weekly_workflow_stats[state['workflow_state']] = state['count']

				# Set the entry in cache
				cache.set(week_key, weekly_workflow_stats)

		if weekly_workflow_stats:
			funnel_metrics[week_key] = weekly_workflow_stats

	return funnel_metrics

