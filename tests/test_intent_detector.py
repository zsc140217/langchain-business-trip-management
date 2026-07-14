"""
IntentDetector 测试套件
测试第零层意图识别器的所有功能
"""
import pytest
from src.agents.intent_detector import IntentDetector


class TestIntentDetection:
    """测试意图检测功能"""

    def setup_method(self):
        """每个测试前初始化"""
        self.detector = IntentDetector()

    # ========== 单一意图：天气 ==========

    def test_weather_intent_basic(self):
        """测试基础天气查询"""
        assert self.detector.detect("北京天气怎么样") == "weather"
        assert self.detector.detect("上海天气") == "weather"

    def test_weather_intent_variations(self):
        """测试天气查询的各种表达"""
        queries = [
            "深圳会下雨吗",
            "杭州气温多少",
            "广州冷不冷",
            "明天北京天气如何",
            "上海需要带伞吗",
            "成都晴天还是阴天",
        ]
        for query in queries:
            assert self.detector.detect(query) == "weather", f"Failed: {query}"

    def test_weather_intent_with_forecast(self):
        """测试天气预报查询"""
        assert self.detector.detect("北京未来三天天气") == "weather"
        assert self.detector.detect("上海明天天气预报") == "weather"

    # ========== 单一意图：航班 ==========

    def test_flight_intent_basic(self):
        """测试基础航班查询"""
        assert self.detector.detect("北京到上海的航班") == "flight"
        assert self.detector.detect("查询机票") == "flight"

    def test_flight_intent_variations(self):
        """测试航班查询的各种表达"""
        queries = [
            "深圳到北京航班查询",
            "机票价格多少",
            "飞机几点起飞",
            "经济舱多少钱",
            "商务舱航班",
            "CA1234航班状态",
            "MU5678什么时候降落",
        ]
        for query in queries:
            assert self.detector.detect(query) == "flight", f"Failed: {query}"

    def test_flight_intent_with_date(self):
        """测试带日期的航班查询"""
        assert self.detector.detect("明天北京到上海的航班") == "flight"
        assert self.detector.detect("2024-06-15的机票") == "flight"

    # ========== 单一意图：酒店 ==========

    def test_hotel_intent_basic(self):
        """测试基础酒店查询"""
        assert self.detector.detect("北京酒店推荐") == "hotel"
        assert self.detector.detect("查询宾馆") == "hotel"

    def test_hotel_intent_variations(self):
        """测试酒店查询的各种表达"""
        queries = [
            "深圳有什么酒店",
            "500元以下的宾馆",
            "四星级住宿",
            "附近酒店推荐",
            "协议酒店查询",
            "预订房间",
            "入住哪里",
        ]
        for query in queries:
            assert self.detector.detect(query) == "hotel", f"Failed: {query}"

    def test_hotel_intent_with_filters(self):
        """测试带筛选条件的酒店查询"""
        assert self.detector.detect("北京500元以下的酒店") == "hotel"
        assert self.detector.detect("五星级宾馆推荐") == "hotel"

    # ========== 多意图冲突 ==========

    def test_multi_intent_conflict(self):
        """测试多意图冲突（应返回None）"""
        queries = [
            "去杭州出差，查天气并推荐酒店",  # 天气 + 酒店
            "查询航班和酒店",  # 航班 + 酒店
            "北京天气怎么样，顺便查查机票",  # 天气 + 航班
            "天气好的话就订酒店",  # 天气 + 酒店
        ]
        for query in queries:
            assert self.detector.detect(query) is None, f"Failed: {query}"

    # ========== 无明确意图 ==========

    def test_no_clear_intent_chitchat(self):
        """测试闲聊查询（无工具意图）"""
        queries = [
            "你好",
            "谢谢",
            "今天星期几",
            "你能做什么",
            "出差好累",
            "再见",
        ]
        for query in queries:
            assert self.detector.detect(query) is None, f"Failed: {query}"

    def test_no_clear_intent_policy(self):
        """测试政策查询（需要RAG）"""
        queries = [
            "差旅政策是什么",
            "北京住宿标准",  # 注意：不含"酒店"关键词
            "报销流程",
            "一线城市定义",
        ]
        for query in queries:
            assert self.detector.detect(query) is None, f"Failed: {query}"

    def test_no_clear_intent_empty(self):
        """测试空查询"""
        assert self.detector.detect("") is None
        assert self.detector.detect("   ") is None

    # ========== 边界情况 ==========

    def test_intent_with_negation(self):
        """测试否定句（应返回None或正确意图）"""
        # 否定句可能需要LLM理解，返回None进入下一层
        assert self.detector.detect("不要查天气") is None
        assert self.detector.detect("不想订酒店") is None

    def test_intent_with_context(self):
        """测试上下文相关查询"""
        # 缺少关键实体，可能返回意图或None
        result = self.detector.detect("天气怎么样")  # 缺少城市
        assert result in ["weather", None]  # 两种都可接受


class TestEntityExtraction:
    """测试实体提取功能"""

    def setup_method(self):
        """每个测试前初始化"""
        self.detector = IntentDetector()

    # ========== 天气实体提取 ==========

    def test_extract_weather_city(self):
        """测试天气查询提取城市"""
        entities = self.detector.extract_entities("北京天气怎么样", "weather")
        assert entities["city"] == "北京"

        entities = self.detector.extract_entities("上海会下雨吗", "weather")
        assert entities["city"] == "上海"

    def test_extract_weather_no_city(self):
        """测试无城市的天气查询（使用默认值）"""
        entities = self.detector.extract_entities("天气怎么样", "weather")
        assert "city" in entities
        assert entities["city"] is not None  # 应有默认值

    def test_extract_weather_multiple_cities(self):
        """测试多城市（取第一个）"""
        entities = self.detector.extract_entities("北京和上海的天气", "weather")
        assert entities["city"] in ["北京", "上海"]

    # ========== 航班实体提取 ==========

    def test_extract_flight_cities(self):
        """测试航班查询提取出发/到达城市"""
        entities = self.detector.extract_entities("北京到上海的航班", "flight")
        assert entities["departure_city"] == "北京"
        assert entities["arrival_city"] == "上海"

    def test_extract_flight_date(self):
        """测试航班查询提取日期"""
        entities = self.detector.extract_entities("明天北京到上海的航班", "flight")
        assert "date" in entities
        # 日期可以是None或解析后的值

    def test_extract_flight_no_cities(self):
        """测试无城市的航班查询（使用默认值）"""
        entities = self.detector.extract_entities("查询航班", "flight")
        assert "departure_city" in entities
        assert "arrival_city" in entities

    def test_extract_flight_number(self):
        """测试提取航班号"""
        entities = self.detector.extract_entities("CA1234航班状态", "flight")
        assert "flight_no" in entities or "departure_city" in entities
        # 航班号查询可能需要特殊处理

    # ========== 酒店实体提取 ==========

    def test_extract_hotel_city(self):
        """测试酒店查询提取城市"""
        entities = self.detector.extract_entities("北京酒店推荐", "hotel")
        assert entities["city"] == "北京"

    def test_extract_hotel_price(self):
        """测试酒店查询提取价格"""
        entities = self.detector.extract_entities("500元以下的酒店", "hotel")
        assert entities.get("max_price") == 500

        entities = self.detector.extract_entities("300到600元的宾馆", "hotel")
        assert entities.get("min_price") == 300
        assert entities.get("max_price") == 600

    def test_extract_hotel_star(self):
        """测试酒店查询提取星级"""
        entities = self.detector.extract_entities("四星级酒店", "hotel")
        assert entities.get("min_star") == 4

        entities = self.detector.extract_entities("五星级宾馆", "hotel")
        assert entities.get("min_star") == 5

    def test_extract_hotel_combined(self):
        """测试酒店查询提取多个实体"""
        entities = self.detector.extract_entities("北京500元以下的四星级酒店", "hotel")
        assert entities["city"] == "北京"
        assert entities.get("max_price") == 500
        assert entities.get("min_star") == 4

    def test_extract_hotel_no_entities(self):
        """测试无实体的酒店查询（使用默认值）"""
        entities = self.detector.extract_entities("推荐酒店", "hotel")
        assert "city" in entities
        assert entities["city"] is not None  # 应有默认值


class TestEdgeCases:
    """测试边界情况"""

    def setup_method(self):
        """每个测试前初始化"""
        self.detector = IntentDetector()

    def test_mixed_case_query(self):
        """测试大小写混合查询"""
        # 中文通常不区分大小写，但测试英文部分
        assert self.detector.detect("CA1234航班") == "flight"

    def test_query_with_punctuation(self):
        """测试带标点符号的查询"""
        assert self.detector.detect("北京天气怎么样？") == "weather"
        assert self.detector.detect("查询航班。") == "flight"

    def test_query_with_numbers(self):
        """测试带数字的查询"""
        entities = self.detector.extract_entities("500元酒店", "hotel")
        assert entities.get("max_price") == 500

    def test_long_query(self):
        """测试长查询"""
        query = "我想知道明天去北京出差的时候天气怎么样，需要带伞吗"
        assert self.detector.detect(query) == "weather"

    def test_ambiguous_query(self):
        """测试模糊查询（可能返回None）"""
        # "附近"可能是酒店、餐厅等，取决于实现
        result = self.detector.detect("附近有什么")
        # 可以返回None或hotel，测试灵活性
        assert result in [None, "hotel"]


class TestPerformance:
    """测试性能"""

    def setup_method(self):
        """每个测试前初始化"""
        self.detector = IntentDetector()

    def test_detect_performance(self):
        """测试检测性能（应 < 5ms）"""
        import time

        queries = [
            "北京天气",
            "上海到深圳航班",
            "500元酒店",
            "你好",
        ]

        total_time = 0
        for query in queries:
            start = time.time()
            self.detector.detect(query)
            elapsed = (time.time() - start) * 1000  # ms
            total_time += elapsed

        avg_time = total_time / len(queries)
        print(f"\n平均检测时间: {avg_time:.2f}ms")
        assert avg_time < 5, f"检测时间过长: {avg_time:.2f}ms"

    def test_extract_performance(self):
        """测试实体提取性能（应 < 10ms）"""
        import time

        start = time.time()
        self.detector.extract_entities("北京500元以下的四星级酒店", "hotel")
        elapsed = (time.time() - start) * 1000  # ms

        print(f"\n实体提取时间: {elapsed:.2f}ms")
        assert elapsed < 10, f"提取时间过长: {elapsed:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
