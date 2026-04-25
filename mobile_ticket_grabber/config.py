# -- Appium & App Info --
APPIUM_SERVER_URL = 'http://127.0.0.1:4723'
DEVICE_NAME = '127.0.0.1:16384'
APP_PACKAGE = 'com.sankuai.movie'
APP_ACTIVITY = 'com.sankuai.movie.MovieMainActivity'

# -- Ticket Info --
TARGET_DATE_TEXT = ["2025-09-27 周六 19:30"]
TARGET_TICKET_TEXT = ['内场至尊VIP ¥2000', '内场VIP ¥1800', '内场 ¥1600', '看台 ¥1300', '看台 ¥1000', '看台 ¥800', '看台 ¥600']

# -- Keywords for Actions --
INITIAL_BUTTON_KEYWORDS = ["立即预订", "立即购买", "已预约", "本人已阅读并同意"]
SELECTION_CONFIRM_KEYWORDS = ["确认", "选好了"]
ORDER_CONFIRM_KEYWORDS = ["提交订单"]
PAYMENT_KEYWORDS = ["立即支付", "确认支付"]
REFRESH_KEYWORDS = ["刷新"]
RESERVATION_KEYWORDS = ["已预约", "预约成功"]
COUNTDOWN_KEYWORDS = ["天", "时", "分", "秒"]
