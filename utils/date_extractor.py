import calendar
import json
import string
import time
import datetime
import regex as re
import pytz



REGEX_DATE = r"(3[01]|[12][0-9]|0?[1-9])[-\/:.|](1[0-2]|0?[1-9])([-\/:|.](2[0-1][0-9][0-9]))"
REGEX_DAY_MONTH = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|.](1[0-2]|0?[1-9])"
REGEX_MONTH_YEAR = r"(1[0-2]|0?[1-9])([-\/:|.](2[0-1][0-9][0-9]))"
number_str = { "mùng một" : 1,"một": 1, "mùng hai": 2, "hai": 2, "mùng ba": 3, "ba": 3, "mùng bốn": 4, "bốn": 4,"tư": 4, "mùng năm": 5, "năm": 5, "mùng sáu": 6, "sáu": 6, "mùng bảy": 7, "bảy": 7, "mùng tám": 8, "tám": 8, "mùng chín": 9, "chín": 9,"mùng mười": 10, "mười": 10,"mười một": 11,"mười hai": 12,"mười ba": 13,"mười bốn": 14,"rằm": 15, "mười lăm": 15,"mười sáu": 16,"mười bảy": 17,"mười tám": 18,"mười chín": 19,
    "hai mươi": 20,"hai mươi mốt": 21, "hai mốt": 21, "hai mươi hai": 22, "hai hai": 22, "hai mươi ba": 23, "hai ba": 23, "hai mươi bốn": 24, "hai bốn": 24, "hai tư": 24, "hai mươi tư": 24,"hai mươi lăm": 25, "hai lăm": 24, "hai mươi sáu": 26, "hai sáu": 26,"hai mươi bảy": 27, "hai bảy": 27,"hai mươi tám": 28, "hai tám": 28,"hai mươi chín": 29, "hai chín": 29,"ba mươi": 30,"ba mươi mốt": 31, "ba mốt": 31}

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
    #words.append(words.pop(words.index("đến")))      
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
            if data[token] in ["nextyear", "lastyear", "thisyear", "lastmonth", "thismonth", "nextmonth", "aftertomorrow"]:
                tokens.append({data[token]:token})
                remove_token(words,token)
                continue
            if data[token] == "year":
                if words[i - 1] not in ["tháng", "ngày"]:
                    tokens.append({data[token]: words[i]})
                    remove_token(words,token)
                    remove_token(words,words[i - 1])
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
    return tokens

def tokenize_2(msg,file):
    words = preprocess_msg(msg)
    with open(file, encoding='utf-8') as jsonFile:
        data = json.load(jsonFile)
    tokens = []
    n_grams = (8, 7, 6, 5, 4, 3, 2, 1)
    i = 0
    while i < len(words):
        has_gram = False
        token = None
        for n_gram in n_grams:
            token = ' '.join(words[i:i + n_gram])
            if token in data:
                w = words[i - 1] if i > 0 else ''
                W = words[i + n_gram] if i < len(words) - n_gram else ''
                i += n_gram
                has_gram = True
                break
        if has_gram is False:
            token = words[i]
            i += 1
        if token in data:
            tokens.append({data[token]: token})

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
    for i in range(len(tokens)):
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
        if tok_key == 'nextweek':
            if tok_value.split()[0].isnumeric():
                num_weeks = int(tok_value.split()[0])
                for day in tokens:
                    token_day = list(day.keys())[0]
                    if token_day in ['mon','tue','wed','thu','fri','sat','sun']:
                        day_w = now.isoweekday()
                        target_w = get_weekday(token_day)
                        if day_w >= target_w:
                            date = get_next_n_weekends_dates(now, token_day, num_weeks)
                            date = date[num_weeks-1].strftime("%d-%m-%Y")
                            dates.append(date)
                        else:
                            date = get_next_n_weekends_dates(now, token_day, num_weeks+1)
                            date = date[num_weeks].strftime("%d-%m-%Y")
                            dates.append(date)
            else:
                for day in tokens:
                    token_day = list(day.keys())[0]
                    if token_day in ['mon','tue','wed','thu','fri','sat','sun']:
                        day_w = now.isoweekday()
                        target_w = get_weekday(token_day)
                        if day_w >= target_w:
                            date = get_next_n_weekends_dates(now, token_day,1)
                            date = date[0].strftime("%d-%m-%Y")
                            dates.append(date)
                        else:
                            date = get_next_n_weekends_dates(now, token_day, 2)
                            date = date[1].strftime("%d-%m-%Y")
                            dates.append(date)
        if tok_key == 'allofnextweek':
            startdate = now + datetime.timedelta(days=-now.weekday(), weeks=1)
            dates.append(startdate.strftime("%d-%m-%Y"))
            for i in range(1,7):
                day = (startdate + datetime.timedelta(days=(i))).strftime("%d-%m-%Y")
                dates.append(day)
        if tok_key == 'thisweek':
            startdate = now - datetime.timedelta(days=now.weekday())
            dates.append(startdate.strftime("%d-%m-%Y"))
            for i in range(1,7):
                day = (startdate + datetime.timedelta(days=(i))).strftime("%d-%m-%Y")
                dates.append(day)
                
        if tok_key.startswith('month'):
            day_key = list(tokens[i - 1].keys())[0]
            day_val = list(tokens[i - 1].values())[0]
            if day_key != "day":
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
            else:
                continue
        if tok_key == 'thismonth':
            month = now.month
            year = now.year
            num_days = calendar.monthrange(year, month)[1]
            days = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
            for day in days:
                day = day.strftime("%d-%m-%Y")
                dates.append(day)
                
        if tok_key == 'nextmonth':
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
        if tok_key == 'lastmonth':
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
            month_key = list(tokens[i - 1].keys())[0]
            month_val = list(tokens[i - 1].values())[0]
            if month_key.startswith("month"):
                continue
            else:
                year = tok_value
                dates.append("01-01-" + year)
        
        if tok_key == 'nextyear':
            month_key = list(tokens[i - 1].keys())[0]
            month_val = list(tokens[i - 1].values())[0]
            if month_key.startswith("month"):
                continue
            else:
                year = str(now.year + 1)
                dates.append("01-01-" + year)
                
        if tok_key == 'lastyear':
            month_key = list(tokens[i - 1].keys())[0]
            month_val = list(tokens[i - 1].values())[0]
            if month_key.startswith("month"):
                continue
            else:
                year = str(now.year - 1)
                dates.append("01-01-" + year)
                
        if tok_key == 'day':
            day = tok_value
            
            if i + 1 >= len(tokens):
                dates.append(day + "-" + str(now.month) + "-" + str(now.year))
                continue
            else:
                month_key = list(tokens[i + 1].keys())[0]
                month_val = list(tokens[i + 1].values())[0]
                if month_key.startswith("month"):
                    month = month_key.split("month")[1]
                    if month.isnumeric():
                        month = month
                    else:
                        if month in number_str.keys():
                            month = str(number_str[month])
                        else:
                            month = 0
                elif month_key == "nextmonth":
                    month = str(now.month + 1)
                elif month_key == "lastmonth":
                    month = str(now.month - 1)
                else:
                    continue 
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
   
    return dates

def check_list(list):
    dates  = []
    for x in list:
        if x not in dates:
            dates.append(x)
    dates_sort = [datetime.datetime.strptime(x,'%d-%m-%Y') for x in dates]
    dates = [x.strftime('%d-%m-%Y') for x in dates_sort]
    return dates
def get_change_token(msg):
    tokens = tokenize_2(msg,"data/change.json")
    change = []
    for token in tokens:
        tok_key = list(token.keys())[0]
        change.append(tok_key)
    return change
def summary_date(msg):
    
    dates = regex_date(msg)
    tokens = tokenize(msg)
    dates += get_date(tokens,'Asia/Ho_Chi_Minh',dates)
    dates = check_list(dates)
    return dates
t = time.time()
for i in range(0, 1000000):
    print(i)
    print(summary_date('20-03-2022 đến ngày 28/03-2022'))
print(time.time() - t)
#print(summary_date('ngày 5 tháng ba đến ngày 10 tháng ba'))
#print(summary_date('02/02/2013 đi đến ngày 2 tháng 3 ngày mùng một tháng chạp năm 2022 và ngày rằm tháng năm năm 2022 và ngày hai mươi chín tháng 5 năm 2022'))
#print(summary_date('hôm nay và ngày mai'))
#print(summary_date('ngày 20 tháng 3 năm 2022 đến ngày 28 tháng 3 năm 2022'))
#print(summary_date('tháng ba năm sau'))
#print(summary_date('ngày ba mươi mốt tháng năm năm sau tôi đi chơi ngày 22 tháng 11 năm nay'))
#print(summary_date('ngày tôi đi chới 23 tháng ba năm sau'))
#print(summary_date('ngày hai mươi đến ngày 23 tháng 6'))

#print(summary_date("thứ 2 tuần sau và thứ 3 tuần sau"))
#print(summary_date('20/02|2020 19:02:2002'))
