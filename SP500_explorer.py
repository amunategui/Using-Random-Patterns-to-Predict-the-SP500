from dateutil import parser 
from numpy import matrix
from decimal import *
from datetime import datetime as dts
from collections import defaultdict
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import copy, datetime, urllib,time, sys, collections

# for an explanation of what is going on here refer to:
# http://laurelhurstmanagement.wordpress.com/2013/05/09/using-random-patterns-to-predict-the-sp-500/

# constants to play around with
MULTIPLIER = 1000
MINCOUNT = 10 # minimum pattern count to qualify for library inclusion
THRESHOLD = 0.7 # percentage prediction rate between 0 and 1
TRAINING_START_DATE = 'Jan-1-2008'
TRAINING_END_DATE = 'Dec-31-2011'
TRADING_START_DATE = 'Jan-1-2011'
TRADING_END_DATE = 'Dec-31-2012'
#SYMBOLS_LIST_FILE = "sp5002012_short.txt"
SYMBOLS_LIST_FILE = "sp5002012.txt"

# global market data collections
highs_pattern=[]
lows_pattern=[]
opens_pattern=[]
closes_pattern=[]
date_list=[]
spy_moves_concatenated = []
totalcount = 0
successcount = 0

class Quote(object):
  # http://trading.cheno.net/downloading-yahoo-finance-historical-data-with-python/
  # Copyright (c) 2011, Mark Chenoweth
  # All rights reserved.
  DATE_FMT = '%Y-%m-%d'
  
  def __init__(self):
	self.symbol = ''
	self.date,self.time,self.open_,self.high,self.low,self.close,self.volume = ([] for _ in range(7))

  def append(self,dt,open_,high,low,close,volume):
    self.date.append(dt.date())
    self.time.append(dt.time())
    self.open_.append(float(open_))
    self.high.append(float(high))
    self.low.append(float(low))
    self.close.append(float(close))
    self.volume.append(int(volume))
       
class YahooQuote(Quote):
	# http://trading.cheno.net/downloading-yahoo-finance-historical-data-with-python/
	# Copyright (c) 2011, Mark Chenoweth
	# All rights reserved.
	''' Daily quotes from Yahoo. Date format='yyyy-mm-dd' '''
	# datetime.datetime.now().strftime("%Y-%m-%d")
	def __init__(self,symbols,start_date,end_date):
		#=datetime.datetime.now()):
		start_date_str = start_date.strftime("%Y-%m-%d")
		end_date_str = end_date.strftime("%Y-%m-%d")
		
		super(YahooQuote,self).__init__()
		for symbol in symbols:
			self.symbol = symbol.upper()
			start_year,start_month,start_day = start_date_str.split('-')
			start_month = str(int(start_month)-1)
			end_year,end_month,end_day = end_date_str.split('-')
			end_month = str(int(end_month)-1)
			url_string = "http://ichart.finance.yahoo.com/table.csv?s={0}".format(symbol)
			url_string += "&a={0}&b={1}&c={2}".format(start_month,start_day,start_year)
			url_string += "&d={0}&e={1}&f={2}".format(end_month,end_day,end_year)
			# http://ichart.finance.yahoo.com/table.csv?s=spy&a=0&b=01T00:00:00&c=2008&d=11&e=31T00:00:00&f=2009
			try:
				csv = urllib.urlopen(url_string).readlines()
				csv.reverse()
				for bar in xrange(0,len(csv)-1):
				  ds,open_,high,low,close,volume,adjc = csv[bar].rstrip().split(',')
				  open_,high,low,close,adjc = [float(x) for x in [open_,high,low,close,adjc]]
				  if close != adjc:
					factor = adjc/close
					open_,high,low,close = [x*factor for x in [open_,high,low,close]]
				  dt = datetime.datetime.strptime(ds,'%Y-%m-%d')
				  self.append(dt,open_,high,low,close,volume)
			except:
				next
		
def translate_market_to_global_collection_patterns(startdate, enddate):
	global highs_pattern, lows_pattern, opens_pattern, closes_pattern, spy_moves_concatenated
	highs_pattern=[]
	lows_pattern=[]
	opens_pattern=[]
	closes_pattern=[]
	spy_moves_concatenated = []
	date_list=[]
	
	dt_start = dts.strptime(startdate, '%b-%d-%Y')
	dt_end = dts.strptime(enddate, '%b-%d-%Y')
	
	with open(SYMBOLS_LIST_FILE, 'r')as input:
		ls_symbols = (input.read().splitlines())
	ls_symbols.append('SPY')

	# spy list
	q_spy = YahooQuote(['SPY'],dt_start,dt_end)  
	closes = list(q_spy.close)
	closes_shift = list(closes)
	closes_shift.pop(0)
	spy_moves = [cmp(((i / j) - 1),0) for i, j in zip(closes, closes_shift)]
	del spy_moves[-1]
	
	# date list
	dates = list(q_spy.date)
	date_list = list(dates)
	date_list.pop(0)
	del date_list[-1]
		
	for symbol in ls_symbols:
		print symbol,
		sys.stdout.flush()
		time.sleep(0.01)	
		q = YahooQuote([symbol],dt_start,dt_end) 
		if len(set(q_spy.date).difference(set(q.date))) > 0:
			print 'error with: ',symbol,
			sys.stdout.flush()
			time.sleep(0.01)	
		else:
			# create highs pattern
			highs = list(q.high)
			highs_shift = list(highs)
			highs_shift.pop(0)
			# formula from the article: 
			# 	TRUNCATE (((current_price_point / previous_price_point) – 1) * 1000)
			temp = [int(((i / j) - 1) * MULTIPLIER) for i, j in zip(highs, highs_shift) if j !=0]
			temp.pop(0)
			highs_pattern += temp
			
			# create lows pattern
			lows = list(q.low)
			lows_shift = list(lows)
			lows_shift.pop(0)
			temp = [int(((i / j) - 1) * MULTIPLIER) for i, j in zip(lows, lows_shift) if j !=0]
			temp.pop(0)
			lows_pattern += temp
			
			# create opens pattern
			opens = list(q.open_)
			opens_shift = list(opens)
			opens_shift.pop(0)
			temp = [int(((i / j) - 1) * MULTIPLIER) for i, j in zip(opens, opens_shift) if j !=0]
			temp.pop(0)
			opens_pattern += temp
			
			# create closes pattern
			closes = list(q.close)
			closes_shift = list(closes)
			closes_shift.pop(0)
			temp = [int(((i / j) - 1) * MULTIPLIER) for i, j in zip(closes, closes_shift) if j !=0]
			temp.pop(0)
			closes_pattern += temp
			
			# concatenate a list of spy results to be same length as other lists
			spy_moves_concatenated += spy_moves
	 
		
def get_list_of_top_patterns(heardername, patternresults):
	pattern_list = {}
	return_list = {}
	
	# build pattern library by picking winning patterns
	pattFinderWithResults = collections.Counter(patternresults)
	 
	# only want directional patterns equal or larger than MINCOUNT
	subdictResults = dict((k, v) for k, v in pattFinderWithResults.iteritems()) # if v >= MINCOUNT)
	for patt in subdictResults: 
		patt_inv = patt[:-1] + (patt[-1]*-1,)
		orig_count = subdictResults[patt]
		inverse_count = 0
		
		# get count of other side total
		if patt_inv in subdictResults:
			try:
				inverse_count = subdictResults[patt_inv]
			except Exception, err:
				# acceptable eror if no pattern found for this direction 
				sys.stderr.write('ERROR: %s\n' % str(err))
				inverse_count = 0
		
		totalCount = orig_count + inverse_count
		if (totalCount >= MINCOUNT):
			if (orig_count > inverse_count):
				perc = orig_count/float(totalCount)
				#print perc
				if (perc > THRESHOLD):
					# does this lead to a positive or negative move
					direction = patt[-1]
					pattern_list[patt] = round(orig_count/float(totalCount),2) * float(direction)
					
		 
	return_list[heardername] = pattern_list
	return return_list

def get_stats(header, resultpatterns, symbol):
	global totalcount, successcount
	
	for x in range(0, len(resultpatterns)):
		# find a pattern match
		keys = patterns[header].keys()
		keytype = len(header)
		for k in keys:
			if keytype == 1:
				if k[0] == resultpatterns[x][0]:
					totalcount += 1
					# found match
					if k == resultpatterns[x]:
						successcount += 1
			elif keytype == 2:
				if (k[0] == resultpatterns[x][0]) and (k[1] == resultpatterns[x][1]):
					totalcount += 1
					# found match
					if k == resultpatterns[x]:
						successcount += 1
			elif keytype == 3:
				if (k[0] == resultpatterns[x][0]) and (k[1] == resultpatterns[x][1]) and (k[2] == resultpatterns[x][2]):
					totalcount += 1
					# found match
					if k == resultpatterns[x]:
						successcount += 1
			else:
				#print k, " len = ", keytype
				if (k[0] == resultpatterns[x][0]) and (k[1] == resultpatterns[x][1]) and (k[2] == resultpatterns[x][2]) and (k[3] == resultpatterns[x][3]):
					totalcount += 1
					# found match
					if k == resultpatterns[x]:
						successcount += 1
			
		
# Creating an object of the dataaccess class with Yahoo as the source.
if __name__ == '__main__':
	
	#--------------------------------------------
	# prep training data with market data from range
	#--------------------------------------------
	print '\r\n'
	print '\r*************************************'
	print '  building training patterns'
	print '\r*************************************'
	print '\r\n'
	translate_market_to_global_collection_patterns(TRAINING_START_DATE, TRAINING_END_DATE)
	date_list = []
		
	#--------------------------------------------
	# create patterns by building each combination
	#--------------------------------------------
	Hresults = zip(highs_pattern, spy_moves_concatenated)
	Lresults = zip(lows_pattern, spy_moves_concatenated)
	Oresults = zip(opens_pattern, spy_moves_concatenated)
	Cresults = zip(closes_pattern, spy_moves_concatenated)
	HLresults = zip(highs_pattern,lows_pattern, spy_moves_concatenated)
	HOresults = zip(highs_pattern, opens_pattern, spy_moves_concatenated)
	HCresults = zip(highs_pattern, closes_pattern, spy_moves_concatenated)
	LOresults = zip(lows_pattern, opens_pattern, spy_moves_concatenated)
	LCresults = zip(lows_pattern, closes_pattern, spy_moves_concatenated)
	OCresults = zip(opens_pattern, closes_pattern, spy_moves_concatenated)
	HLOresults = zip(highs_pattern, lows_pattern, opens_pattern)
	HLCresults = zip(highs_pattern, lows_pattern, closes_pattern, spy_moves_concatenated)
	HOCresults = zip(highs_pattern, opens_pattern, closes_pattern, spy_moves_concatenated)
	LOCresults = zip(lows_pattern, opens_pattern, closes_pattern, spy_moves_concatenated)
	HLOCresults = zip(highs_pattern, lows_pattern, opens_pattern, closes_pattern, spy_moves_concatenated)

	#--------------------------------------------
	# cull best patterns for each combination
	#--------------------------------------------
	patterns = {}
	resultpatters = [Hresults,Lresults,Oresults,Cresults,HLresults,\
		HOresults,HCresults,LOresults,LCresults,OCresults,HLOresults,\
		HLCresults,HOCresults,LOCresults,HLOCresults]
		
	patternheaders = ['H','L','O','C','HL','HO','HC','LO','LC','OC','HLO','HLC','HOC','LOC','HLOC']
	
	for header in patternheaders:
		patterns.update(get_list_of_top_patterns (header, resultpatters[patternheaders.index(header)]))
  
	#--------------------------------------------
	# check number of patterns found from training data
	#--------------------------------------------
	t = 0
	for x in patterns:
		t += len(patterns[x])
	print '\r\n'
	print '\r*************************************'	
	print '\rtraining from %s to %s' % (TRAINING_START_DATE, TRAINING_END_DATE)
	print 'total patterns found:',t
	print 'for MULTIPLIER = %i, MINCOUNT = %i,THRESHOLD= %f' % (MULTIPLIER, MINCOUNT, THRESHOLD)
	print '\r*************************************'
	print '\r\n'
	
	#--------------------------------------------
	# load trading data
	#-------------------------------------------- 
	print '\r\n'
	print '\r*************************************'
	print '  building trading patterns'
	print '\r*************************************'
	print '\r\n'
	
	translate_market_to_global_collection_patterns(TRADING_START_DATE, TRADING_END_DATE)
	 
	#--------------------------------------------
	# create patterns by building each combination
	#--------------------------------------------
	Hresults = zip(highs_pattern, spy_moves_concatenated)
	Lresults = zip(lows_pattern, spy_moves_concatenated)
	Oresults = zip(opens_pattern, spy_moves_concatenated)
	Cresults = zip(closes_pattern, spy_moves_concatenated)
	HLresults = zip(highs_pattern,lows_pattern, spy_moves_concatenated)
	HOresults = zip(highs_pattern, opens_pattern, spy_moves_concatenated)
	HCresults = zip(highs_pattern, closes_pattern, spy_moves_concatenated)
	LOresults = zip(lows_pattern, opens_pattern, spy_moves_concatenated)
	LCresults = zip(lows_pattern, closes_pattern, spy_moves_concatenated)
	OCresults = zip(opens_pattern, closes_pattern, spy_moves_concatenated)
	HLOresults = zip(highs_pattern, lows_pattern, opens_pattern)
	HLCresults = zip(highs_pattern, lows_pattern, closes_pattern, spy_moves_concatenated)
	HOCresults = zip(highs_pattern, opens_pattern, closes_pattern, spy_moves_concatenated)
	LOCresults = zip(lows_pattern, opens_pattern, closes_pattern, spy_moves_concatenated)
	HLOCresults = zip(highs_pattern, lows_pattern, opens_pattern, closes_pattern, spy_moves_concatenated) 
	
	#--------------------------------------------
	# loop through each trading and through each pattern
	# track how well pattern library did on trading segment
	#--------------------------------------------
	
	resultpatterns = [Hresults,Lresults,Oresults,Cresults,HLresults,\
		HOresults,HCresults,LOresults,LCresults,OCresults,HLOresults,\
		HLCresults,HOCresults,LOCresults,HLOCresults]
	
	print '\r\n'
	print '\r*************************************'	
	print '\rtrading from %s to %s' % (TRADING_START_DATE, TRADING_END_DATE)
	print 'total patterns found:',t
	print '\r*************************************'
	print '\r\n'
		
	#--------------------------------------------
	# trade
	#-------------------------------------------- 
	print '\r\n'
	print '\r*************************************'
	print '  trading - this is slow!'
	print '\r*************************************'
	print '\r\n'	
	
	for header in patternheaders:
		print '\r\n'
		print 'comparing:', header,
		sys.stdout.flush()
		time.sleep(0.01)
		get_stats(header, resultpatterns[patternheaders.index(header)], 'SPY')
		
	print '\r\n'		
	if totalcount > 0:
		print 'successcount = %i, totalcount = %i' % (successcount , totalcount)
		print ("%.2f" % (successcount / float(totalcount))) + '%'
	
	print '\r\n'
	print '\r*************************************'
	print '  done'
	print '\r*************************************'
	print '\r\n'