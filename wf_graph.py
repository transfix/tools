"""This program is for consolidating transactions listed in wells fargo online
banking into a day to day +/- change and adding a running balance curve, then plotting
it using Qwt.
11/23/2013 - transfix@gmail.com

Change Log
----------
12/19/2013 - using stdin if no file specified
01/04/2013 - forcing stdin always and using qwt to plot the output
"""

import csv
import sys
import calendar
from datetime import datetime
from datetime import date
from datetime import timedelta
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *

def readcsv(csvreader):
    """This reads csv data and returns an array of days with
    amounts for each day"""
    days = {}
    for row in csvreader:
        if len(row) < 5:
            sys.stderr.write("Invalid row (columns < 5)\n")
            continue
        
        # split up the first column and make a date object out of it
        parts = row[0].split('/')

        #wells fargo dates are in m/d/y format, no padding
        if len(parts) != 3:
            sys.stderr.write("Invalid date!\n")
            continue

        month = parts[0]
        day = parts[1]
        year = parts[2]

        curdate = date(int(year), int(month), int(day))
        
        #the amount is the second column
        amount = float(row[1])
        
        if curdate not in days:
            days[curdate] = amount
        else:
            days[curdate] = days[curdate] + amount
    return days

class TimeScaleDraw(Qwt.QwtScaleDraw):
    def __init__(self):
        Qwt.QwtScaleDraw.__init__(self)
        self.setLabelAlignment(Qt.Qt.AlignLeft | Qt.Qt.AlignBottom)
        self.setLabelRotation(0)

    def label(self, value):
        return Qwt.QwtText(str(date.fromtimestamp(value)))

class MoneyPlot(Qwt.QwtPlot):

    def __init__(self, dates, amounts, balances, *args):
        Qwt.QwtPlot.__init__(self, *args)

	# make a QwtPlot widget
	self.setTitle('Cash Moneyz')
        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.RightLegend)
        
	# set axis titles
	self.setAxisTitle(Qwt.QwtPlot.xBottom, 'time -->')
	self.setAxisTitle(Qwt.QwtPlot.yLeft, 'amount -->')

        # set the time axis labels to show dates
        draw = TimeScaleDraw()
        self.setAxisScaleDraw(Qwt.QwtPlot.xBottom, draw)
        self.setAxisScale(Qwt.QwtPlot.xBottom, dates[0], dates[-1])
        
	# amounts curve
	daily_amount = Qwt.QwtPlotCurve('daily amount')
	daily_amount.setPen(Qt.QPen(Qt.Qt.red))
        daily_amount.attach(self)

	running_balance = Qwt.QwtPlotCurve('running balance')
	running_balance.setPen(Qt.QPen(Qt.Qt.blue))
        running_balance.attach(self)
        
	# initialize the data
	daily_amount.setData(dates, amounts)
	running_balance.setData(dates, balances)

	# insert a horizontal marker at y = 0
 	mY = Qwt.QwtPlotMarker()
        #mY.setLabel(Qwt.QwtText('amount = 0'))
        mY.setLabelAlignment(Qt.Qt.AlignRight | Qt.Qt.AlignTop)
        mY.setLineStyle(Qwt.QwtPlotMarker.HLine)
        mY.setYValue(0.0)
        mY.attach(self)

        #mark the start of each month with a vertical line
        [self.markMonth(x) for x in dates]

        # replot
        self.replot()

    # __init__()

    def markMonth(self, x_value):
        x_value_date = datetime.fromtimestamp(x_value)
        if x_value_date.day == 1:
            mX = Qwt.QwtPlotMarker()
            mX.setLineStyle(Qwt.QwtPlotMarker.VLine)
            mX.setXValue(x_value)
            mX.attach(self)

    # markMonth()

# class Plot

if len(sys.argv) < 2:
    print "Usage: ./wf_graph.py <target balance> < <csv file>\n"
    sys.exit(-1)

target_balance = float(sys.argv[1])

csvreader = csv.reader(sys.stdin)
days = readcsv(csvreader)
dateobjs = sorted(days.keys())
if len(dateobjs) == 0:
    sys.stderr.write("No dates!!!\n")
    sys.exit(-1)

mindate = dateobjs[0]
maxdate = dateobjs[-1]
oneday = timedelta(days=1)
curdate = mindate
balance = 0.0
date_array = []
amounts = []
balances = []
while curdate <= maxdate:
    amount = 0.0
    if curdate in days:
        amount = days[curdate]
    balance += amount
    #print curdate.strftime("%m/%d/%y") + "," + str(amount) + "," + str(balance)
    date_array.append(calendar.timegm(curdate.timetuple())) #convert back to unix time for the chart
    amounts.append(amount)
    balances.append(balance)
    curdate += oneday

#adjust the balances to hit the target by the end of the graph
difference = target_balance - balance
balances = [x+difference for x in balances]

#launch the plot
app = Qt.QApplication(sys.argv)
mp = MoneyPlot(date_array,amounts,balances)
mp.resize(640,480)
mp.show()
sys.exit(app.exec_())
