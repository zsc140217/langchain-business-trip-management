"""
城市名翻译工具
支持中英文城市名互转（覆盖中国所有省会和主要城市）
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 中国城市名映射表（中文 ↔ 英文/拼音）
CHINA_CITIES = {
    # 直辖市
    "北京": ["Beijing", "beijing"],
    "上海": ["Shanghai", "shanghai"],
    "天津": ["Tianjin", "tianjin"],
    "重庆": ["Chongqing", "chongqing"],

    # 省会城市
    "哈尔滨": ["Harbin", "harbin"],
    "长春": ["Changchun", "changchun"],
    "沈阳": ["Shenyang", "shenyang"],
    "呼和浩特": ["Hohhot", "hohhot"],
    "石家庄": ["Shijiazhuang", "shijiazhuang"],
    "乌鲁木齐": ["Urumqi", "urumqi"],
    "兰州": ["Lanzhou", "lanzhou"],
    "西宁": ["Xining", "xining"],
    "西安": ["Xi'an", "Xian", "xian"],
    "银川": ["Yinchuan", "yinchuan"],
    "郑州": ["Zhengzhou", "zhengzhou"],
    "济南": ["Jinan", "jinan"],
    "太原": ["Taiyuan", "taiyuan"],
    "合肥": ["Hefei", "hefei"],
    "长沙": ["Changsha", "changsha"],
    "武汉": ["Wuhan", "wuhan"],
    "南京": ["Nanjing", "nanjing"],
    "成都": ["Chengdu", "chengdu"],
    "贵阳": ["Guiyang", "guiyang"],
    "昆明": ["Kunming", "kunming"],
    "南宁": ["Nanning", "nanning"],
    "拉萨": ["Lhasa", "lhasa"],
    "杭州": ["Hangzhou", "hangzhou"],
    "南昌": ["Nanchang", "nanchang"],
    "广州": ["Guangzhou", "guangzhou"],
    "福州": ["Fuzhou", "fuzhou"],
    "台北": ["Taipei", "taipei"],
    "海口": ["Haikou", "haikou"],
    "香港": ["Hong Kong", "HongKong", "hongkong"],
    "澳门": ["Macau", "Macao", "macau"],

    # 计划单列市
    "深圳": ["Shenzhen", "shenzhen"],
    "厦门": ["Xiamen", "xiamen"],
    "宁波": ["Ningbo", "ningbo"],
    "青岛": ["Qingdao", "qingdao"],
    "大连": ["Dalian", "dalian"],

    # 其他重要城市（按省份分组，100+城市）
    "苏州": ["Suzhou", "suzhou"],
    "无锡": ["Wuxi", "wuxi"],
    "常州": ["Changzhou", "changzhou"],
    "南通": ["Nantong", "nantong"],
    "扬州": ["Yangzhou", "yangzhou"],
    "徐州": ["Xuzhou", "xuzhou"],
    "镇江": ["Zhenjiang", "zhenjiang"],
    "连云港": ["Lianyungang", "lianyungang"],
    "淮安": ["Huai'an", "Huaian", "huaian"],
    "盐城": ["Yancheng", "yancheng"],
    "泰州": ["Taizhou", "taizhou"],
    "宿迁": ["Suqian", "suqian"],

    "温州": ["Wenzhou", "wenzhou"],
    "嘉兴": ["Jiaxing", "jiaxing"],
    "金华": ["Jinhua", "jinhua"],
    "绍兴": ["Shaoxing", "shaoxing"],
    "台州": ["Taizhou", "taizhou"],
    "湖州": ["Huzhou", "huzhou"],
    "丽水": ["Lishui", "lishui"],
    "衢州": ["Quzhou", "quzhou"],
    "舟山": ["Zhoushan", "zhoushan"],

    "珠海": ["Zhuhai", "zhuhai"],
    "佛山": ["Foshan", "foshan"],
    "东莞": ["Dongguan", "dongguan"],
    "中山": ["Zhongshan", "zhongshan"],
    "惠州": ["Huizhou", "huizhou"],
    "江门": ["Jiangmen", "jiangmen"],
    "湛江": ["Zhanjiang", "zhanjiang"],
    "汕头": ["Shantou", "shantou"],
    "潮州": ["Chaozhou", "chaozhou"],
    "揭阳": ["Jieyang", "jieyang"],
    "梅州": ["Meizhou", "meizhou"],
    "韶关": ["Shaoguan", "shaoguan"],
    "清远": ["Qingyuan", "qingyuan"],
    "肇庆": ["Zhaoqing", "zhaoqing"],
    "云浮": ["Yunfu", "yunfu"],
    "阳江": ["Yangjiang", "yangjiang"],
    "茂名": ["Maoming", "maoming"],
    "河源": ["Heyuan", "heyuan"],
    "汕尾": ["Shanwei", "shanwei"],

    "桂林": ["Guilin", "guilin"],
    "柳州": ["Liuzhou", "liuzhou"],
    "玉林": ["Yulin", "yulin"],
    "梧州": ["Wuzhou", "wuzhou"],
    "北海": ["Beihai", "beihai"],
    "钦州": ["Qinzhou", "qinzhou"],
    "贵港": ["Guigang", "guigang"],
    "防城港": ["Fangchenggang", "fangchenggang"],
    "崇左": ["Chongzuo", "chongzuo"],
    "百色": ["Baise", "baise"],
    "河池": ["Hechi", "hechi"],
    "来宾": ["Laibin", "laibin"],
    "贺州": ["Hezhou", "hezhou"],

    "洛阳": ["Luoyang", "luoyang"],
    "开封": ["Kaifeng", "kaifeng"],
    "安阳": ["Anyang", "anyang"],
    "新乡": ["Xinxiang", "xinxiang"],
    "焦作": ["Jiaozuo", "jiaozuo"],
    "南阳": ["Nanyang", "nanyang"],
    "许昌": ["Xuchang", "xuchang"],
    "信阳": ["Xinyang", "xinyang"],
    "平顶山": ["Pingdingshan", "pingdingshan"],
    "商丘": ["Shangqiu", "shangqiu"],
    "周口": ["Zhoukou", "zhoukou"],
    "驻马店": ["Zhumadian", "zhumadian"],
    "三门峡": ["Sanmenxia", "sanmenxia"],
    "漯河": ["Luohe", "luohe"],
    "鹤壁": ["Hebi", "hebi"],
    "濮阳": ["Puyang", "puyang"],
    "济源": ["Jiyuan", "jiyuan"],

    "济宁": ["Jining", "jining"],
    "烟台": ["Yantai", "yantai"],
    "潍坊": ["Weifang", "weifang"],
    "淄博": ["Zibo", "zibo"],
    "威海": ["Weihai", "weihai"],
    "临沂": ["Linyi", "linyi"],
    "德州": ["Dezhou", "dezhou"],
    "聊城": ["Liaocheng", "liaocheng"],
    "滨州": ["Binzhou", "binzhou"],
    "菏泽": ["Heze", "heze"],
    "枣庄": ["Zaozhuang", "zaozhuang"],
    "日照": ["Rizhao", "rizhao"],
    "泰安": ["Tai'an", "Taian", "taian"],
    "莱芜": ["Laiwu", "laiwu"],
    "东营": ["Dongying", "dongying"],

    "包头": ["Baotou", "baotou"],
    "鄂尔多斯": ["Ordos", "ordos"],
    "赤峰": ["Chifeng", "chifeng"],
    "通辽": ["Tongliao", "tongliao"],
    "呼伦贝尔": ["Hulunbuir", "hulunbuir"],
    "巴彦淖尔": ["Bayannur", "bayannur"],
    "乌兰察布": ["Ulanqab", "ulanqab"],
    "乌海": ["Wuhai", "wuhai"],
    "阿拉善": ["Alxa", "alxa"],
    "兴安": ["Xing'an", "Xingan", "xingan"],
    "锡林郭勒": ["Xilingol", "xilingol"],

    "大同": ["Datong", "datong"],
    "阳泉": ["Yangquan", "yangquan"],
    "长治": ["Changzhi", "changzhi"],
    "晋城": ["Jincheng", "jincheng"],
    "朔州": ["Shuozhou", "shuozhou"],
    "晋中": ["Jinzhong", "jinzhong"],
    "运城": ["Yuncheng", "yuncheng"],
    "忻州": ["Xinzhou", "xinzhou"],
    "临汾": ["Linfen", "linfen"],
    "吕梁": ["Lüliang", "Lvliang", "lvliang"],

    "唐山": ["Tangshan", "tangshan"],
    "秦皇岛": ["Qinhuangdao", "qinhuangdao"],
    "邯郸": ["Handan", "handan"],
    "邢台": ["Xingtai", "xingtai"],
    "保定": ["Baoding", "baoding"],
    "张家口": ["Zhangjiakou", "zhangjiakou"],
    "承德": ["Chengde", "chengde"],
    "沧州": ["Cangzhou", "cangzhou"],
    "廊坊": ["Langfang", "langfang"],
    "衡水": ["Hengshui", "hengshui"],
}

# 反向映射：英文 → 中文（用于快速查找）
_EN_TO_ZH_MAP = {}
for zh, en_list in CHINA_CITIES.items():
    for en in en_list:
        _EN_TO_ZH_MAP[en.lower()] = zh


def translate_to_chinese(city_name: str) -> Optional[str]:
    """
    将英文/拼音城市名翻译为中文

    Args:
        city_name: 英文或拼音城市名（如 "Beijing"）

    Returns:
        中文城市名（如 "北京"），未找到返回 None
    """
    if city_name in CHINA_CITIES:
        return city_name

    city_lower = city_name.lower().strip()
    if city_lower in _EN_TO_ZH_MAP:
        return _EN_TO_ZH_MAP[city_lower]

    logger.debug(f"城市名 '{city_name}' 未在映射表中找到")
    return None


def normalize_city_name(city_name: str, target_lang: str = "zh") -> str:
    """
    标准化城市名（统一转为目标语言）

    Args:
        city_name: 输入城市名
        target_lang: 目标语言，"zh"（中文）或 "en"（英文）

    Returns:
        标准化后的城市名，找不到时返回原值
    """
    if target_lang == "zh":
        result = translate_to_chinese(city_name)
        return result if result else city_name
    else:
        raise ValueError(f"当前仅支持翻译为中文，不支持: {target_lang}")


def is_supported_city(city_name: str) -> bool:
    """
    检查城市是否在支持列表中

    Args:
        city_name: 城市名（中文或英文）

    Returns:
        是否支持
    """
    return (city_name in CHINA_CITIES or
            city_name.lower() in _EN_TO_ZH_MAP)


# 导出统计信息
SUPPORTED_CITIES_COUNT = len(CHINA_CITIES)

if __name__ == "__main__":
    print(f"支持的城市数量: {SUPPORTED_CITIES_COUNT}")
    print(f"\n测试翻译:")
    print(f"Beijing -> {translate_to_chinese('Beijing')}")
    print(f"beijing -> {translate_to_chinese('beijing')}")
    print(f"UnknownCity -> {translate_to_chinese('UnknownCity')}")
    print(f"\n标准化测试:")
    print(f"normalize('Beijing', 'zh') -> {normalize_city_name('Beijing', 'zh')}")
    print(f"\n支持性检查:")
    print(f"is_supported('北京') -> {is_supported_city('北京')}")
    print(f"is_supported('Beijing') -> {is_supported_city('Beijing')}")
    print(f"is_supported('UnknownCity') -> {is_supported_city('UnknownCity')}")
