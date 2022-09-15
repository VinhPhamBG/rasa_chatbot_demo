import calendar
import datetime
import json
import string
import time
from ast import Break

import pytz
import regex as re

REGEX_DATE = r"(3[01]|[12][0-9]|0?[1-9])[-\/:.|](1[0-2]|0?[1-9])([-\/:|.](2[0-1][0-9][0-9]))"
REGEX_DAY_MONTH = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|.](1[0-2]|0?[1-9])"
REGEX_MONTH_YEAR = r"(1[0-2]|0?[1-9])([-\/:|.](2[0-1][0-9][0-9]))"

with open("utils/number_str.json",encoding='utf-8') as f:
        number_str = json.load(f)


def regex_date(msg, timezone="Asia/Ho_Chi_Minh"):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz)
    date_str = []
    regex = REGEX_DATE
    regex_day_month = REGEX_DAY_MONTH
    regex_month_year = REGEX_MONTH_YEAR
    pattern = re.compile("(%s|%s|%s)" % (regex, regex_month_year, regex_day_month), re.UNICODE)
    matches = pattern.finditer(msg)
    for match in matches:
        _dt = match.group(0)
        _dt = _dt.replace("/", "-").replace("|", "-").replace(":", "-").replace("|", "-").replace(".", "-").replace("\\", "-")
        for i in range(len(_dt.split("-"))):
            if len(_dt.split("-")[i]) == 1:
                _dt = _dt.replace(_dt.split("-")[i], "0"+_dt.split("-")[i])
        if len(_dt.split("-")) == 2:
            pos1 = _dt.split("-")[0]
            pos2 = _dt.split("-")[1]
            if 0 < int(pos1) < 32 and 0 < int(pos2) < 13:
                _dt = pos1+"-"+pos2+"-"+str(now.year)
        date_str.append(_dt)
    print(date_str)
    return date_str

def preprocess_msg(msg):
    msg = msg.lower()
    special_punc = string.punctuation
    for punc in "-+/:|":
        special_punc = special_punc.replace(punc, '')
    msg = ''.join(c for c in msg if c not in special_punc)
    list_word = msg.split()
    for i in range(len(list_word)):
        if i > 0 and list_word[i].isnumeric() and list_word[i - 1] not in ["ngày", "tháng", "năm", "thứ"]:
            list_word.insert(i, "ngày")
        elif i == 0 and list_word[i].isnumeric():
            list_word.insert(i, "ngày")
    return list_word

def remove_token(words,token):
    if token in words:
        words.remove(token)
    return words

def tokenize(msg):
    words = preprocess_msg(msg)
    with open("utils/synonyms.json",encoding='utf-8') as jsonFile:
        data = json.load(jsonFile)
    tokens = []
    n_grams = (10,9,8,7,6,5,4,3,2,1)
    i = 0      
    while i < len(words):
        has_gram = False
        token = None
        for n_gram in n_grams:
            token = ' '.join(words[i:i + n_gram])
            if token in data:
                w = words[i] if i > 0 else ''
                W = words[i+n_gram] if i < len(words) - n_gram else ''
                i += n_gram
                has_gram = True
                break
        if has_gram is False:
            token = words[i]
            i += 1
        if token in data:
            if data[token] in ["mon","tue","wed","thu","fri","sat","sun","today","daysago", "nextday","nextweek","lastweek","thisweek"]:
                if w in number_str.keys():
                    tokens.append({data[token]: str(number_str[w]) + " " + token})
                    words.remove(w)
                    remove_token(words,token)
                elif w.isnumeric():
                    tokens.append({data[token]: w + " " + token})
                    words.remove(w)
                    remove_token(words,token)
                else:
                    tokens.append({data[token]: token})
                    remove_token(words,token)
                continue
            if data[token].startswith('month'):
                tokens.append({data[token]: token})
                remove_token(words,token)
                continue
            if data[token] == "between":
                tokens.append({data[token]:token})
                #remove_token(words,token)
                continue
            if data[token] == "end":
                if words[i] in ["năm", "tháng"]:
                    tokens.append({data[token]:token})
                elif words[i].isnumeric():
                    tokens.append({data[token]:token})
                    tokens.append({"year":words[i]})
                #remove_token(words,token)
                continue
            if data[token] == "start":
                if words[i] in ["năm", "tháng"]:
                    tokens.append({data[token]:token})
                elif words[i].isnumeric():
                    tokens.append({data[token]:token})
                    tokens.append({"year":words[i]})
                #remove_token(words,token)
                continue
            if data[token] in ["nextyear", "lastyear", "thisyear", "lastmonth", "thismonth", "nextmonth", "aftertomorrow"]:
                tokens.append({data[token]:token})
                remove_token(words,token)
                continue
            if data[token] == "year":
                if words[i - 1] not in ["tháng", "ngày"]:
                    tokens.append({data[token]: words[i]})
                    remove_token(words,token) 
                    words.remove(words[i - 1])               
                    continue
                else:
                    continue
            if data[token] == "day":
                if words[i].isnumeric():
                    tokens.append({data[token]: words[i]})
                    remove_token(words,token)
                    continue
                elif len(words[i]) and i < len(words) - 1:
                    temp = words[i] + " " + words[i + 1]
                    if (temp + " " + words[i + 2]) in number_str.keys():
                        tokens.append({data[token]: str(number_str[temp + " " + words[i + 2]])})
                        remove_token(words,token)
                        continue
                    elif temp in number_str.keys():
                        tokens.append({data[token]: str(number_str[temp])}) 
                        remove_token(words,token)
                        continue 
                    else:
                        tokens.append({data[token]: str(number_str[words[i]])})
                        remove_token(words,token)
                        continue
            if data[token] == "nextyear":
                tokens.append({data[token]:token})  
                continue  
    print(tokens)
    return tokens

def get_weekday(day):
    days  = ["mon","tue","wed","thu","fri","sat","sun"]
    return days.index(day) + 1

def get_next_dayofweek_datetime(date_time, dayofweek):
    start_time_w = date_time.isoweekday()
    target_w = get_weekday(dayofweek)
    if start_time_w < target_w:
      day_diff = target_w - start_time_w
    else:
        day_diff = 7 - (start_time_w - target_w)

    return date_time + datetime.timedelta(days=day_diff)

def get_next_n_weekends_dates(date_time, weekday, n):
  days_list = []
  week_date_time = date_time
  while n > 0:
      week_date_time = get_next_dayofweek_datetime(week_date_time, weekday)
      days_list.append(week_date_time)
      n = n -1
  return  days_list

def get_date(tokens,timezone,dates = []):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz).date()
    i = 0
    while i < len(tokens):
        tok_key = list(tokens[i].keys())[0]
        tok_value = list(tokens[i].values())[0]
        if tok_key == 'today':
            date = now.strftime("%d-%m-%Y")
            dates.append(date)
        if tok_key == 'aftertomorrow':
            date = (now + datetime.timedelta(days=2)).strftime("%d-%m-%Y")
            dates.append(date)
        if tok_key == 'nextday':
            if tok_value.split()[0].isnumeric():
                num_days = int(tok_value.split()[0])
                date = (now + datetime.timedelta(days=num_days)).strftime("%d-%m-%Y")
                dates.append(date)
            else:
                date = (now + datetime.timedelta(days=(1))).strftime("%d-%m-%Y")
                dates.append(date)
        if tok_key == 'daysago':
            if tok_value.split()[0].isnumeric():
                num_days = -int(tok_value.split()[0])
                date = (now + datetime.timedelta(days=num_days)).strftime("%d-%m-%Y")
                dates.append(date)
            else:
                date = (now + datetime.timedelta(days=(-1))).strftime("%d-%m-%Y")
                dates.append(date)
                
        # if tok_key == 'nextweek':
        #     if list(tokens[i - 1].keys())[0] in ['mon','tue','wed','thu','fri','sat','sun']:
        #         for day in tokens:
        #             token_day = list(day.keys())[0]
        #             if token_day in ['mon','tue','wed','thu','fri','sat','sun']:
        #                 day_w = now.isoweekday()
        #                 target_w = get_weekday(token_day)
        #                 if day_w >= target_w:
        #                     date = get_next_n_weekends_dates(now, token_day,1)
        #                     date = date[0].strftime("%d-%m-%Y")
        #                     dates.append(date)
        #                 else:
        #                     date = get_next_n_weekends_dates(now, token_day, 2)
        #                     date = date[1].strftime("%d-%m-%Y")
        #                     dates.append(date)
        #     else:
        #         startdate = now + datetime.timedelta(days=-now.weekday(), weeks=1)
        #         dates.append(startdate.strftime("%d-%m-%Y"))
        #         for n in range(1,7):
        #             day = (startdate + datetime.timedelta(days=(n))).strftime("%d-%m-%Y")
        #             dates.append(day)

        # if tok_key == 'lastweek':
        #     if list(tokens[i - 1].keys())[0] in ['mon','tue','wed','thu','fri','sat','sun']:
        #         for day in tokens:
        #             token_day = list(day.keys())[0]
        #             if token_day in ['mon','tue','wed','thu','fri','sat','sun']:
        #                 day_w = now.isoweekday()
        #                 target_w = get_weekday(token_day)
        #                 if day_w >= target_w:
        #                     date = get_next_n_weekends_dates(now, token_day,1)
        #                     date = date[0].strftime("%d-%m-%Y")
        #                     dates.append(date)
        #                 else:
        #                     date = get_next_n_weekends_dates(now, token_day, 2)
        #                     date = date[1].strftime("%d-%m-%Y")
        #                     dates.append(date)
        #     else:
        #         startdate = now + datetime.timedelta(days=-now.weekday(), weeks=-1)
        #         dates.append(startdate.strftime("%d-%m-%Y"))
        #         for n in range(1,7):
        #             day = (startdate + datetime.timedelta(days=(n))).strftime("%d-%m-%Y")
        #             dates.append(day)
        
        if tok_key == 'lastweek':
            temp = []
            startdate = now - datetime.timedelta(days=now.weekday() + 7)
            temp.append(startdate.strftime("%d-%m-%Y"))
            for n in range(1,7):
                day = (startdate + datetime.timedelta(days=(n))).strftime("%d-%m-%Y")
                temp.append(day)
            weekdays = ['mon','tue','wed','thu','fri','sat','sun']
            prev_key = list(tokens[i - 1].keys())[0]
            if prev_key in weekdays:
                if prev_key == "mon":
                    dates.append(temp[0])
                elif prev_key == "tue":
                    dates.append(temp[1])
                elif prev_key == "wed":
                    dates.append(temp[2])
                elif prev_key == "thu":
                    dates.append(temp[3])
                elif prev_key == "fri":
                    dates.append(temp[4])
                elif prev_key == "sat":
                    dates.append(temp[5])
                elif prev_key == "sun":
                    dates.append(temp[6])
            else:
               dates.append(temp) 
        
        if tok_key == 'nextweek':
            temp = []
            startdate = now - datetime.timedelta(days=now.weekday() - 7)
            temp.append(startdate.strftime("%d-%m-%Y"))
            for n in range(1,7):
                day = (startdate + datetime.timedelta(days=(n))).strftime("%d-%m-%Y")
                temp.append(day)
            weekdays = ['mon','tue','wed','thu','fri','sat','sun']
            prev_key = list(tokens[i - 1].keys())[0]
            if prev_key in weekdays:
                if prev_key == "mon":
                    dates.append(temp[0])
                elif prev_key == "tue":
                    dates.append(temp[1])
                elif prev_key == "wed":
                    dates.append(temp[2])
                elif prev_key == "thu":
                    dates.append(temp[3])
                elif prev_key == "fri":
                    dates.append(temp[4])
                elif prev_key == "sat":
                    dates.append(temp[5])
                elif prev_key == "sun":
                    dates.append(temp[6])
            else:
               dates.append(temp) 
                    
        if tok_key == 'allofnextweek':
            startdate = now + datetime.timedelta(days=-now.weekday(), weeks=1)
            dates.append(startdate.strftime("%d-%m-%Y"))
            for i in range(1,7):
                day = (startdate + datetime.timedelta(days=(i))).strftime("%d-%m-%Y")
                dates.append(day)
                
        if tok_key == 'thisweek':
            temp = []
            startdate = now - datetime.timedelta(days=now.weekday())
            temp.append(startdate.strftime("%d-%m-%Y"))
            for n in range(1,7):
                day = (startdate + datetime.timedelta(days=(n))).strftime("%d-%m-%Y")
                temp.append(day)
            weekdays = ['mon','tue','wed','thu','fri','sat','sun']
            prev_key = list(tokens[i - 1].keys())[0]
            if prev_key in weekdays:
                if prev_key == "mon":
                    dates.append(temp[0])
                elif prev_key == "tue":
                    dates.append(temp[1])
                elif prev_key == "wed":
                    dates.append(temp[2])
                elif prev_key == "thu":
                    dates.append(temp[3])
                elif prev_key == "fri":
                    dates.append(temp[4])
                elif prev_key == "sat":
                    dates.append(temp[5])
                elif prev_key == "sun":
                    dates.append(temp[6])
            else:
               dates.append(temp)
                
        if tok_key.startswith('month') and list(tokens[i - 1].keys())[0] not in ["end", "start"]:
            day_key = list(tokens[i - 1].keys())[0]
            if day_key != "day" and list(tokens[i - 1].keys())[0] not in ["end", "start"]:
                month = int(tok_key.split("month")[1])
                year_key = list(tokens[i + 1].keys())[0]
                year_val = list(tokens[i + 1].values())[0]
                if year_key == "year":
                    year = int(year_val)
                elif year_key == "nextyear":
                    year = now.year + 1
                elif year_key == "lastyear":
                    year = now.year - 1
                else:
                    year = now.year
                num_days = calendar.monthrange(year, month)[1]
                days = [datetime.date(year, month, day) for day in range(1, num_days+1)]
                for day in days:
                    day = day.strftime("%d-%m-%Y")
                    dates.append(day)
            
        if tok_key == 'thismonth' and list(tokens[i - 1].keys())[0] not in ["end", "start"]:
            month = now.month
            year = now.year
            num_days = calendar.monthrange(year, month)[1]
            days = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
            for day in days:
                day = day.strftime("%d-%m-%Y")
                dates.append(day)
                
        if tok_key == 'nextmonth' and list(tokens[i - 1].keys())[0] not in ["end", "start"]:
            day_key = list(tokens[i - 1].keys())[0]
            day_val = list(tokens[i - 1].values())[0]
            if day_key != "day":
                month = now.month + 1
                year = now.year
                if month > 12:
                    year = year + 1
                    month = 1
                num_days = calendar.monthrange(year, month)[1]
                days = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
                for day in days:
                    day = day.strftime("%d-%m-%Y")
                    dates.append(day)
        if tok_key == 'lastmonth' and list(tokens[i - 1].keys())[0] not in ["end", "start"]:
            day_key = list(tokens[i - 1].keys())[0]
            day_val = list(tokens[i - 1].values())[0]
            if day_key != "day":
                month = now.month - 1
                year = now.year
                if month < 0:
                    year = year - 1
                    month = 12
                num_days = calendar.monthrange(year, month)[1]
                days = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
                for day in days:
                    day = day.strftime("%d-%m-%Y")
                    dates.append(day)
        if tok_key == 'year':
            if i == 0:
                year = tok_value
                dates.append("00-00-" + year)
            else:
                month_key = list(tokens[i - 1].keys())[0]
                month_val = list(tokens[i - 1].values())[0]
                if month_key.startswith("month") == False and month_key not in ["end", "start"]:
                    year = tok_value
                    dates.append("00-00-" + year)
                    
        if tok_key == 'nextyear':
            month_key = list(tokens[i - 1].keys())[0]
            if month_key.startswith("month") == False and month_key not in ["end", "start"]:
                year = str(now.year + 1)
                dates.append("00-00-" + year)
                
        if tok_key == 'lastyear':
            month_key = list(tokens[i - 1].keys())[0]
            if month_key.startswith("month") == False and month_key not in ["end", "start"]:
                year = str(now.year - 1)
                dates.append("00-00-" + year)
            
        if tok_key == 'thisyear':
            month_key = list(tokens[i - 1].keys())[0]
            if month_key.startswith("month") == False and month_key not in ["end", "start"]:
                year = str(now.year)
                dates.append("00-00-" + year)
                
        if tok_key == 'day':
            day = tok_value
            print('day')
            if i + 1 >= len(tokens):
                dates.append(day + "-" + str(now.month) + "-" + str(now.year))
            else:
                next_key = list(tokens[i + 1].keys())[0]
                if next_key.startswith("month"):
                    month = next_key.split("month")[1]
                    if month.isnumeric():
                        month = month
                    else:
                        if month in number_str.keys():
                            month = str(number_str[month])
                        else:
                            month = "0"
                elif next_key == "nextmonth":
                    month = str(now.month + 1)
                elif next_key == "lastmonth":
                    month = str(now.month - 1)
                else:
                    month = str(now.month)
                    
                if (i + 2) >= len(tokens):
                    year = str(now.year)
                else:
                    year_key = list(tokens[i + 2].keys())[0]
                    year_val = list(tokens[i + 2].values())[0]
                    if year_key == "year":
                        year = year_val
                    elif year_key == "nextyear":
                        year = str(now.year + 1)
                    elif year_key == "lastyear":
                        year = str(now.year - 1)
                    else:
                        year = str(now.year)
                dates.append(day + "-" + month + "-" + year)
        if len(dates) >  1 and tok_key == 'between':
            
            start_d = datetime.datetime.strptime(dates[0],"%d-%m-%Y").date()
            end_d = datetime.datetime.strptime(dates[1],"%d-%m-%Y").date()
            days = [start_d + datetime.timedelta(days=x) for x in range((end_d-start_d).days + 1)]
            for day in days:
                day = day.strftime("%d-%m-%Y")
                if day not in dates:
                    dates.append(day)
                    
        if tok_key == "end":
            next_key = list(tokens[i + 1].keys())[0]
            next_val = list(tokens[i + 1].values())[0]
            if next_key == "year":
                dates.append("31-12-" + next_val)
            elif next_key == "thisyear":
                dates.append("31-12-" + str(now.year))
            elif next_key == "nextyear":
                dates.append("31-12-" + str(now.year + 1))
            elif next_key == "lastyear":
                dates.append("31-12-" + str(now.year - 1))
            elif next_key == "thismonth":
                day = calendar.monthrange(now.year, now.month)[1]
                i += 1
                dates.append(str(day) +"-"+ str(now.month) +"-"+ str(now.year))
            elif next_key == "lastmonth":
                month = now.month
                if month == 1:
                    month = 12
                    day = calendar.monthrange(now.year - 1, month)[1]
                    i += 1
                    dates.append(str(day) +"-"+ str(month) +"-"+ str(now.year - 1))
                else:
                    day = calendar.monthrange(now.year, month - 1)[1]
                    i += 1
                    dates.append(str(day) +"-"+ str(month - 1) +"-"+ str(now.year))
            elif next_key == "nextmonth":
                month = now.month
                if month == 12:
                    month = 1
                    day = calendar.monthrange(now.year + 1, month)[1]
                    i += 1
                    dates.append(str(day) +"-"+ str(month) +"-"+ str(now.year + 1))
                else:
                    day = calendar.monthrange(now.year, month + 1)[1]
                    i += 1
                    dates.append(str(day) +"-"+ str(month + 1) +"-"+ str(now.year))
            elif next_key.startswith("month"):
                month = next_key.split("month")[1]
                if len(tokens) > 2:
                    year_key = list(tokens[i + 2].keys())[0]
                    year_val = list(tokens[i + 2].values())[0]
                    if year_key == "year":
                        day = calendar.monthrange(int(year_val), int(month))[1]
                        i += 1
                        dates.append(str(day) +"-"+ month +"-"+ str(year_val))
                        
                    elif year_key == "nextyear":
                        day = calendar.monthrange(int(now.year + 1), int(month))[1]
                        i+=1
                        dates.append(str(day) +"-"+ month +"-"+ str(now.year + 1))
                        
                    elif year_key == "lastyear":
                        day = calendar.monthrange(int(now.year - 1), int(month))[1]
                        i+=1
                        dates.append(str(day) +"-"+ month +"-"+ str(now.year - 1))
                        
                    elif year_key == "thisyear":
                        day = calendar.monthrange(now.year, int(month))[1]
                        i+=1
                        dates.append(str(day) +"-"+ month +"-"+ str(now.year))
                        
                    else:
                        day = calendar.monthrange(now.year, int(month))[1]
                        dates.append(str(day) +"-"+ month +"-"+ str(now.year))
                else:
                    day = calendar.monthrange(now.year, int(month))[1]
                    dates.append(str(day) +"-"+ month +"-"+ str(now.year))
        if tok_key == 'start':
            next_key = list(tokens[i + 1].keys())[0]
            next_val = list(tokens[i + 1].values())[0]
            if next_key == "year":
                dates.append("01-01-" + next_val)
            elif next_key == "thisyear":
                dates.append("01-01-" + str(now.year))
            elif next_key == "nextyear":
                dates.append("01-01-" + str(now.year + 1))
            elif next_key == "lastyear":
                dates.append("01-01-" + str(now.year - 1))
            elif next_key == "thismonth":
                dates.append("01-" + str(now.month) + "-" + str(now.year))
            elif next_key == "lastmonth":
                if now.month == 1:
                    dates.append("01-12" + "-" + str(now.year - 1))
                else:
                    dates.append("01-" + str(now.month - 1) + "-" + str(now.year))
            elif next_key == "nextmonth":
                if now.month == 12:
                    dates.append("01-01" + "-" + str(now.year + 1))
                else:
                    dates.append("01-" + str(now.month + 1) + "-" + str(now.year))
            elif next_key.startswith("month"):
                month = next_key.split("month")[1]
                if len(tokens) > 2:
                    year_key = list(tokens[i + 2].keys())[0]
                    year_val = list(tokens[i + 2].values())[0]
                    if year_key == "year":
                        i += 1
                        dates.append("01-"+ month +"-"+ str(year_val))
                        
                    elif year_key == "nextyear":
                        i+=1
                        dates.append("01-"+ month +"-"+ str(now.year + 1))
                        
                    elif year_key == "lastyear":
                        i+=1
                        dates.append("01-"+ month +"-"+ str(now.year - 1))
                        
                    elif year_key == "thisyear":
                        i+=1
                        dates.append("01-"+ month +"-"+ str(now.year))
                        
                    else:
                        dates.append("01-"+ month +"-"+ str(now.year))
                else:
                    dates.append("01-"+ month +"-"+ str(now.year))
        i = i + 1      
    return dates

def check_list(list):
    dates  = []
    temp = []
    for x in list:
        if x not in dates:
            dates.append(x)
    for d in dates:
        if d.startswith("00-00"):
            temp.append(d)
            dates.pop(dates.index(d))
    dates_sort = [datetime.datetime.strptime(x,'%d-%m-%Y') for x in dates]
    dates = [x.strftime('%d-%m-%Y') for x in dates_sort]
    result = dates + temp
    return result

def date_extractor(msg):
    dates = regex_date(msg)
    tokens = tokenize(msg)
    dates += get_date(tokens,'Asia/Ho_Chi_Minh',dates)
    dates = check_list(dates)
    return dates

msg = input("msg : ")

print(date_extractor(msg))
