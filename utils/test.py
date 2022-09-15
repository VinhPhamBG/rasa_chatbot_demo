import datetime
import pytz
from price_parser import Price
from vi_nlp_core.ner.extractor import Extractor
extractor = Extractor()
# timezone="Asia/Ho_Chi_Minh"
# tz = pytz.timezone(timezone)
# now = datetime.datetime.now(tz=tz)
text = "tôi sinh vào ngày 21 tháng 3 năm 1997 bạn tôi sinh ngày 19 tháng 11 năm 2021"


# msg = input("Please enter: ")
# price = Price.fromstring(msg)
date = extractor.extract_date(text)
print(date.values())
#pip install lexnlp