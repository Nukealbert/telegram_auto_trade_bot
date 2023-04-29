import configparser
import datetime
import json
import re
import urllib.request
import xlwings as xw
#(changes)import pandas as pd
import pyotp
from smartapi import SmartConnect
from telethon.errors import SessionPasswordNeededError
from telethon import TelegramClient, events, sync
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (PeerChannel)
#Expiry date of shares
from datetime import date, datetime
from dateutil.relativedelta import relativedelta, TH , TU
import datetime
#Added
import requests

#date Weekly Expiries
todayDate = date.today()
print("today's detected date: ", todayDate)
nextThrus = todayDate + relativedelta(weekday=TH(1))
nextTues = todayDate + relativedelta(weekday=TU(1))
y = nextTues.strftime("%d%b%y")
x= nextThrus.strftime("%d%b%y")

print("Next tuesday         : ", nextTues)
print("Next thrusday        : ", nextThrus)

  
#date Monthly Expiries (Non Nifty / Thrudays )
todayte = date.today()
cmon = todayte.month

#Holiday-Cases
holidayArray = ["15Aug23","2Oct23", "26Jan23" ]
for i in range(1, 6):
    lastThursday = todayte + relativedelta(weekday=TH(i))

    if lastThursday.month != cmon:
        # since t is exceeded we need last one  which we can get by subtracting -2 since it is already a Thursday.
        lastThursday = lastThursday + relativedelta(weekday=TH(-2))
        lastThursdayFormat= lastThursday.strftime("%d%b%y")
        print("Month_last_thrus_expiry : ", lastThursdayFormat)
        if lastThursdayFormat in holidayArray: #if holiday subract 1
            lastThursday =  lastThursday - datetime.timedelta(days=1)
            print("Change of exipiry : Month_last_thrus_expiry:", lastThursday)
        if x in holidayArray:
            nextThrus =  nextThrus - datetime.timedelta(days=1)
            x=nextThrus.strftime("%d%b%y")
            print("Change of exipiry : Next_thrus_expiry:", x)
        if y in holidayArray:
            nextTues =  nextTues - datetime.timedelta(days=1)
            y=nextTues.strftime("%d%b%y")
            print("Change of exipiry : Next_tueday_expiry:", y)
        break



if date.today() > lastThursday:
    lastThursday=lastThursday + datetime.timedelta(days=10)
    for i in range(1, 6):
        lastThursday = todayte + relativedelta(weekday=TH(i))
        if lastThursday.month != cmon:
            # since t is exceeded we need last one  which we can get by subtracting -2 since it is already a Thursday.
            lastThursday = lastThursday + relativedelta(weekday=TH(-2))
            lastThursdayFormat= lastThursday.strftime("%d%b%y")
            if lastThursdayFormat in holidayArray:
                lastThursday =  lastThursday - datetime.timedelta(days=1)
            
lastThursdayFormat= lastThursday.strftime("%d%b%y") 
print("(Change) last_thurs_crossed + Holiday : Month_last_thrus_expiry", lastThursdayFormat )


#Reading config file
config = configparser.ConfigParser()
config.read("config.ini")

#Telegram api id and api hash
api_id=config['Bot']['api_id']
api_hash=config['Bot']['api_hash']
chats=["Bankniftyjackpothub"]  #You can add channel username or link here 
client = TelegramClient('test2022', api_id, api_hash)

#AngelOne Creds
apikey=config['Bot']['api_key']
totp=config['Bot']['totp']
username=config['Bot']['angel_user']
pwd=config['Bot']['MPIN']



#Extracting Stock Price, Buying Price, and StopLoss from telegram message
def sum_method(first, second):
    return str(int(first) + int(second))


stock_name = ""
qty = 1
entry_price = 0


def detect_values(message):
    message = message.replace("\n", " ").strip().split(" ")
    message = list(filter(lambda value: value != "", message))
    
    share_name_start_index = -1
    stop_loss_start_index = -1
    entry_point_start_index = -1
    tp_start_index = -1
    entry_price_found_after_pe_or_ce = False
    isNifty = True


    for i, word in enumerate(message):
        if "nifty" in word.lower() or "banknifty" in word.lower():
            #(changes)if share_name_start_index == -1:
                share_name_start_index = i
        if "stoploss" in word.lower() or "sl" in word.lower():
            #(changes)if stop_loss_start_index == -1:
             stop_loss_start_index = i + 1
        if "target" in word.lower() or "tgt" in word.lower():
                 tp_start_index = i + 1
        if "ce" == word.lower() or "pe" == word.lower():
                entry_point_start_index = i+1

    print("share name start index",share_name_start_index)
    if share_name_start_index == -1:
        print("nifty not found")
        isNifty = False
        share_name_start_index = entry_point_start_index - 3
    
    print("entry point start index",entry_point_start_index)
    print("entry point start value",message[entry_point_start_index])
    if message[entry_point_start_index].isdigit() == True:
        entry_price_found_after_pe_or_ce = True
        entry_price = message[entry_point_start_index]
    
    if message[entry_point_start_index].isdigit() == False and "-" in message[entry_point_start_index]:
         tempArray = message[entry_point_start_index].split("-")
         print("i am here")
         entry_price = tempArray[0]
         entry_price_found_after_pe_or_ce = True

    stock1= message[share_name_start_index]  
    stock2=message[share_name_start_index + 1:share_name_start_index+3]
    st1="".join(stock1)
    print('                              ', st1)
    st2="".join(stock2)
    print('                              ', st2)
    



    if isNifty == False:
        stock_name= st1.upper() + lastThursdayFormat.upper() +st2.upper()
        print('                              ', lastThursdayFormat )
    elif (st1.upper()=="FINNIFTY"):
        stock_name= st1.upper() + y.upper() +st2.upper()
        print('                              ', y)
    else:
        stock_name= st1.upper() + x.upper() +st2.upper()
        print('                              ', x)


    #__________________________EDIT_VALUE______________________________
    fixed_stoploss_value = -90

    global stoploss 

    if entry_price_found_after_pe_or_ce == False:
        #Entry price detect
        entry_price = message[share_name_start_index + 4]
        #Entry price Range cases: Ex: (70-72) 
        if "-" in entry_price:
            tempArray = entry_price.split("-")
            entry_price = tempArray[0]

        #check if entry detected valid if invalid go to next index
        ep_digitcheck = entry_price.isdigit()
        if ep_digitcheck == False:
            entry_price = message[share_name_start_index + 5]
            #Entry price Range cases: Ex: (70-72) 
            if "-" in entry_price:
                tempArray = entry_price.split("-")
                entry_price = tempArray[0]

    if stop_loss_start_index == -1:
         stoploss = str(sum_method(entry_price, fixed_stoploss_value)) 
    else: 
         stoploss = message[stop_loss_start_index]
   
    
    target = ""
    
    
    #target are multiples separated with comma Ex: target 55,80
    if tp_start_index !=-1:
        target = message[tp_start_index]
        if "," in target:
            tempArray = target.split(",")
            target = tempArray[0]
    

    print('                              ', stock_name)
    print('                               Entry Price     :',entry_price)
    print('                               SL              :',stoploss)
    
    
    
    sl_digitcheck = stoploss.isdigit() 
    print('                               SL_Value_check  :',sl_digitcheck)

    if sl_digitcheck == False:
        stoploss = sum_method(entry_price, fixed_stoploss_value)
      
    
    print('                               SL              :',stoploss)
    print('                               Target          :', target)

    #__________________________EDIT_VALUE______________________________
    fixed_tp_value = 25 

    tp_digitcheck = target.isdigit() 
    print('                               TP_Value_check  :', tp_digitcheck)

    if tp_digitcheck == False or target == '0':
        target = sum_method(entry_price, fixed_tp_value)
        print('                               Target          :', target)
    
   
    
    
    
   
    
    #__________________________EDIT_VALUE______________________________
    entryprice= int(entry_price) + 10
    print("Entry price changed to : ", entryprice, "(For Limit Order)")
    print("Message entry price ",entry_price)
    
    
   
     # Open the JSON file LOCALLY
    with open("C:\\Users\\Office\\Downloads\\OpenAPIScripMaster.json", "r") as json_file:
    # Load the JSON data from the file
     data = json.load(json_file)
    #data = json.loads(response.read())

  
    for i in data:
        if(i['symbol']==stock_name):
            symbol_token=i['token']
            min_lot=i['lotsize']

    print('                                 Min_Qty       : ', min_lot )
    print('                            Entry_price       : ', entry_price )
    print('                            Entry_price       : ', entry_price )
    print('                            Entry_price type      : ', type(entry_price) )
    

    if int(entry_price) < 50:
        ACC = 5000
        stopl = entry_price
        tp = 0.5 * int(entry_price)

    elif 50 <= int(entry_price) <= 100:
         ACC = 10000
         stopl = 0.5 * int(entry_price)
         tp = 0.3 * int(entry_price)

    else:
        ACC = 30000
        stopl = 80
        tp = 0.1 * int(entry_price)

  
    
    lot_price = int(min_lot)* int(entryprice)

    divide = ACC // lot_price
    buy_qty = int(divide) * int(min_lot)
    #print("print info of lots : ", buy_qty)
    
    qty = str(buy_qty)
    print("                         No of lots Orderd(qty): ", qty)

    #points or %

    
    
  

    obj=SmartConnect(api_key=apikey)
   
    data = obj.generateSession(username,pwd,pyotp.TOTP(totp).now())
    
    refreshToken= data['data']['refreshToken']

    feedToken=obj.getfeedToken()
    userProfile= obj.getProfile(refreshToken)
    
   
    
    try:
        orderparams = {
            "variety": "ROBO",
            "tradingsymbol": stock_name,
            "symboltoken": symbol_token,
            "transactiontype": "BUY",
            "exchange": "NFO",
            "ordertype": "LIMIT",
            "producttype": "BO",
            "duration": "DAY",
            "price": entryprice ,
            "squareoff": tp,
            "stoploss": stopl,
            "quantity": qty
            }
        orderId=obj.placeOrder(orderparams)
        print("                            The order id is: {}".format(orderId)) 

        #cancelled_order_ID = obj.cancelOrder(orderId, 'ROBO')
        #print("                           Cancelled order id is: {}".format(cancelled_order_ID)) 
           

        
    except Exception as e:
        print("Order placement failed: {}".format(e.message))

       

@client.on(events.NewMessage(chats= "Bankniftyjackpothub"))
# -1001765735266 (Test id) VR_ID -1001795805407
async def my_event_handler(event):
    print(event.raw_text)

    print(" message length : ",len(event.raw_text))
    if(len(event.raw_text)<=71 and len(event.raw_text)>=10):
        detect_values(event.raw_text)
                     
client.start()
client.run_until_disconnected()
