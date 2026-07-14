"""MCP Server for trip tools (hotel/flight/weather)."""
import logging, os, sys
from typing import Optional
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
_env_path = os.path.join(_ROOT, ".env")
if os.path.exists(_env_path):
    for _line in open(_env_path, encoding="utf-8"):
        _line = _line.strip()
        if _line.startswith("#") or not _line:
            continue
        if "=" in _line:
            k, v = _line.split("=", 1)
            if k.isupper():
                os.environ.setdefault(k, v)
from src.tools.qweather_client import get_qweather_client
logger = logging.getLogger(__name__)
mcp = FastMCP("trip-tools", log_level="ERROR")

# Mock Hotels
MOCK_HOTELS = {
  "北京": [
    {"name":"北京希尔顿酒店","star":5,"price":800,"rating":4.7,"address":"朝阳区","facilities":["WiFi","健身房","游泳池","商务中心"]},
    {"name":"北京万豪酒店","star":5,"price":750,"rating":4.6,"address":"朝阳区建国路","facilities":["WiFi","健身房","餐厅","会议室"]},
    {"name":"北京诺富特酒店","star":4,"price":450,"rating":4.3,"address":"海淀区知春路","facilities":["WiFi","健身房","餐厅"]},
    {"name":"北京如家酒店","star":3,"price":280,"rating":4.2,"address":"西城区金融街","facilities":["WiFi","早餐"]},
    {"name":"北京汉庭酒店","star":3,"price":250,"rating":4.0,"address":"东城区王府井","facilities":["WiFi"]},
  ],
  "上海": [
    {"name":"上海浦东香格里拉酒店","star":5,"price":1200,"rating":4.8,"address":"浦东新区陆家嘴","facilities":["WiFi","健身房","游泳池","SPA","商务中心"]},
    {"name":"上海锦江饭店","star":5,"price":900,"rating":4.5,"address":"黄浦区茂名南路","facilities":["WiFi","健身房","餐厅","会议室"]},
    {"name":"上海亚朵酒店","star":4,"price":500,"rating":4.4,"address":"徐汇区漕溪北路","facilities":["WiFi","健身房","图书馆"]},
    {"name":"上海橘子酒店","star":3,"price":320,"rating":4.1,"address":"静安区南京西路","facilities":["WiFi","早餐"]},
  ],
  "深圳": [
    {"name":"深圳瑞吉酒店","star":5,"price":1500,"rating":4.9,"address":"福田区深南大道","facilities":["WiFi","健身房","游泳池","SPA","米其林餐厅"]},
    {"name":"深圳威斯汀酒店","star":5,"price":880,"rating":4.6,"address":"南山区科技园","facilities":["WiFi","健身房","游泳池","商务中心"]},
    {"name":"深圳维也纳酒店","star":3,"price":350,"rating":4.2,"address":"罗湖区东门","facilities":["WiFi","早餐"]},
  ],
  "杭州": [
    {"name":"杭州西湖国宾馆","star":5,"price":1000,"rating":4.8,"address":"西湖区杨公堤","facilities":["WiFi","健身房","游泳池","西湖景观"]},
    {"name":"杭州凯悦酒店","star":5,"price":780,"rating":4.5,"address":"江干区钱江新城","facilities":["WiFi","健身房","餐厅","会议室"]},
    {"name":"杭州全季酒店","star":3,"price":380,"rating":4.3,"address":"下城区武林广场","facilities":["WiFi","早餐"]},
  ],
  "广州": [
    {"name":"广州四季酒店","star":5,"price":1100,"rating":4.7,"address":"天河区","facilities":["WiFi","健身房","游泳池"]},
    {"name":"广州东浩酒店","star":4,"price":600,"rating":4.4,"address":"越秀区","facilities":["WiFi","健身房"]},
  ],
}

# Mock Flights
MOCK_FLIGHTS = {
  ("北京","上海"): [{"flight_no":"CA1501","airline":"国航","departure":"07:30","arrival":"10:00","duration":"2h30m","price":850},{"flight_no":"MU5101","airline":"东航","departure":"09:15","arrival":"11:45","duration":"2h30m","price":780},{"flight_no":"CZ3001","airline":"南航","departure":"13:20","arrival":"15:50","duration":"2h30m","price":920},{"flight_no":"HU7601","airline":"海航","departure":"18:45","arrival":"21:15","duration":"2h30m","price":680}],
  ("上海","北京"): [{"flight_no":"CA1502","airline":"国航","departure":"08:00","arrival":"10:30","duration":"2h30m","price":880},{"flight_no":"MU5102","airline":"东航","departure":"12:30","arrival":"15:00","duration":"2h30m","price":820},{"flight_no":"CZ3002","airline":"南航","departure":"16:10","arrival":"18:40","duration":"2h30m","price":950}],
  ("北京","深圳"): [{"flight_no":"CA1301","airline":"国航","departure":"08:30","arrival":"12:00","duration":"3h30m","price":1200},{"flight_no":"CZ3101","airline":"南航","departure":"14:20","arrival":"17:50","duration":"3h30m","price":1150},{"flight_no":"HU7701","airline":"海航","departure":"19:00","arrival":"22:30","duration":"3h30m","price":980}],
  ("深圳","北京"): [{"flight_no":"CA1302","airline":"国航","departure":"07:45","arrival":"11:15","duration":"3h30m","price":1250},{"flight_no":"CZ3102","airline":"南航","departure":"13:15","arrival":"16:45","duration":"3h30m","price":1180}],
  ("北京","杭州"): [{"flight_no":"CA1801","airline":"国航","departure":"09:00","arrival":"11:20","duration":"2h20m","price":750},{"flight_no":"MU5201","airline":"东航","departure":"15:30","arrival":"17:50","duration":"2h20m","price":680}],
  ("上海","深圳"): [{"flight_no":"MU5301","airline":"东航","departure":"10:30","arrival":"13:10","duration":"2h40m","price":980},{"flight_no":"CZ3201","airline":"南航","departure":"16:45","arrival":"19:25","duration":"2h40m","price":920}],
}

# Mock Weather
MOCK_WEATHER = {
  "北京": ("晴","25","27","南风","3","45"),
  "上海": ("多云","28","30","东风","2","60"),
  "广州": ("晴","30","32","南风","4","75"),
  "深圳": ("多云","26","28","东风","2","50"),
  "杭州": ("阴","29","31","东南风","3","70"),
  "成都": ("小雨","22","24","北风","1","65"),
  "武汉": ("多云","27","29","东风","2","75"),
  "南京": ("晴","25","27","东风","2","55"),
  "重庆": ("阴","23","26","北风","2","50"),
  "西安": ("晴","24","26","东北风","2","55"),
}


@mcp.tool()
def search_hotels(city, min_price=None, max_price=None, min_star=None):
  """搜索城市酒店，支持价格和星级筛选。"""
  hotels = MOCK_HOTELS.get(city, [])
  if not hotels: return f"抱歉，暂无{city}的酒店信息"
  fh = [h for h in hotels if
    (min_price is None or h["price"] >= min_price) and
    (max_price is None or h["price"] <= max_price) and
    (min_star is None or h["star"] >= min_star)]
  if not fh: return f"抱歉，{city}没有符合条件的酒店"
  fh.sort(key=lambda x: x["rating"], reverse=True)
  parts = [f"📍 {city}酒店查询结果"]
  for i, h in enumerate(fh, 1):
    parts.append(f"{i}. {h['name']} ¥{h['price']}/晚 {h['star']}星 评分{h['rating']}")
  return "\n".join(parts)

@mcp.tool()
def get_hotel_details(city, hotel_name):
  """查询酒店的详细信息。"""
  hotels = MOCK_HOTELS.get(city, [])
  if not hotels: return f"暂无{city}的酒店信息"
  for h in hotels:
    if hotel_name in h["name"] or h["name"] in hotel_name: return f"{h['name']} ¥{h['price']}/晚 {h['star']}星 评分{h['rating']}\n{h['address']}"
  return f"未找到酒店：{hotel_name}"

@mcp.tool()
def search_flights(departure_city, arrival_city, date=None):
  """搜索航班。"""
  if not date: date = datetime.now().strftime("%Y-%m-%d")
  flights = MOCK_FLIGHTS.get((departure_city, arrival_city), [])
  if not flights: return f"暂无{departure_city}到{arrival_city}的航班"
  flights.sort(key=lambda x: x["price"])
  parts = [f"🛫 {departure_city} → {arrival_city} 航班"]
  for i, f in enumerate(flights, 1):
    parts.append(f"{i}. {f['flight_no']} {f['departure']}-{f['arrival']} ¥{f['price']}")
  return "\n".join(parts)

@mcp.tool()
def get_flight_price(departure_city, arrival_city, cls="经济舱"):
  """查询航线价格。"""
  flights = MOCK_FLIGHTS.get((departure_city, arrival_city), [])
  if not flights: return "暂无航班信息"
  cm = {"经济舱":1,"商务舱":2.5,"头等舱":4.5}
  mul = cm.get(cls, 1)
  prices = [f["price"]*mul for f in flights]
  c = flights[prices.index(min(prices))]
  return f"¥{int(min(prices))}-¥{int(max(prices))} 推荐：{c['flight_no']}"

@mcp.tool()
def query_weather(city):
  """查询指定城市的当前天气情况。"""
  client = get_qweather_client()
  if not client.is_ready:
    d = MOCK_WEATHER.get(city, ("晴","22","24","微风","2","50"))
    return f"🌤 {city} 天气：{d[0]} 温度：{d[1]}°C 体感：{d[2]}°C {d[3]}{d[4]}级（模拟）"
  try:
    now = client.weather_by_city(city)
    if not now: return f"抱歉，未找到{city}的天气信息"
    return f"🌤 {city} 天气：{now["text"]} 温度：{now["temp"]}°C 体感：{now["feelsLike"]}°C {now["windDir"]} {now["windScale"]}级 湿度：{now["humidity"]}%"
  except Exception as ex:
    return f"查询{city}天气失败：{str(ex)}"
@mcp.tool()
def get_weather_forecast(city, days=3):
  """查询指定城市未来几天的天气预报。"""
  days = max(1, min(days, 7))
  client = get_qweather_client()
  if not client.is_ready:
    now = datetime.now()
    wk = ["周一","周二","周三","周四","周五","周六","周日"]
    fc = [("晴","28","18"),("多云","26","17"),("阴","24","19")]
    parts = [f"{city}未来{days}天预报（模拟）"]
    for i in range(days):
      d = now + timedelta(days=i)
      wt, tx, tn = fc[i % len(fc)]
      parts.append(f"{d.strftime('%m/%d')} {wk[d.weekday()]} {wt} {tn}-{tx}°C")
    return "\n".join(parts)
  try:
    daily_list = client.forecast_by_city(city, days)
    if not daily_list: return f"抱歉，未找到{city}的天气预报"
    wk = ["周一","周二","周三","周四","周五","周六","周日"]
    parts = [f"{city}未来{days}天天气预报"]
    for daily in daily_list[:days]:
      dt = datetime.strptime(daily["fxDate"], "%Y-%m-%d")
      parts.append(f"\n{dt.strftime('%m/%d')} {wk[dt.weekday()]}")
      parts.append(f"  白天：{daily['textDay']} 夜间：{daily['textNight']}")
      parts.append(f"  温度：{daily['tempMin']}°C ~ {daily['tempMax']}°C")
      parts.append(f"  降水：{daily.get('precip', '0')}mm  风向：{daily['windDirDay']} {daily['windScaleDay']}级")
    return "\n".join(parts)
  except Exception as e:
    return f"查询{city}天气预报失败：{str(e)}"

if __name__ == "__main__":
  mcp.run(transport="stdio")
