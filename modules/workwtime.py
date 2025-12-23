from datetime import datetime, timedelta, tzinfo
import json
import sys

class kztimezone(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=5)
	
	def dst(self, dt):
		return timedelta(hours=1)
	
class workwtime:
	@staticmethod
	def current_date():
		return datetime.now(kztimezone())	

	@staticmethod
	def delta(date: str, measure: str = ""):
		mod = 1
		diff = int((workwtime.current_date() - datetime.fromisoformat(date)).total_seconds())

		match measure:
			case "d":
				mod = (pow(60, 2) * 12) * 2
			case "h":
				mod = 60 * 60
			case "m":
				mod = 60	

		return ((workwtime.current_date() - datetime.fromisoformat(date)).total_seconds()) // mod

	@staticmethod
	def mongo_filter(h: int = 1, limit: int = 10000):
		date_filter = {
    		"filter": {
        		"datetime": {
            		"$gte": str(workwtime.current_date() - timedelta(hours=h)),
            		"$lte": str(workwtime.current_date())
        		}
    		},
    		"limit": limit
		}
	
		return date_filter
