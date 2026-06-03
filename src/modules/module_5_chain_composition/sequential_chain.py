"""
Sequential Chain - 顺序链
Execute operations in sequence: Policy Query → Weather → Itinerary

Design Pattern:
- Linear execution flow
- Each step depends on previous results
- Clear data transformation pipeline
- Easy to understand and debug

Performance Characteristic:
- Total time = sum of all step times
- Best for dependent operations
"""

from typing import Dict, Any, Optional, List
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatTongyi
from langsmith import traceable
import logging
import time

logger = logging.getLogger(__name__)


class SequentialChain:
    """
    Sequential chain that executes operations in order:
    1. Query policy rules
    2. Query weather information
    3. Generate itinerary based on policy and weather

    Use cases:
    - When later steps depend on earlier results
    - When operations must be ordered
    - When debugging requires step-by-step visibility

    Example:
        chain = SequentialChain(llm)
        result = chain.invoke({
            "destination": "Beijing",
            "category": "accommodation"
        })
    """

    def __init__(
        self,
        llm: Optional[ChatTongyi] = None,
        policy_data: Optional[str] = None
    ):
        """
        Initialize sequential chain

        Args:
            llm: Language model instance (uses default if None)
            policy_data: Policy rules text (uses default if None)
        """
        self.llm = llm or self._create_default_llm()
        self.policy_data = policy_data or self._load_default_policy()

        # Build the sequential chain
        self.chain = self._build_chain()

        logger.info("SequentialChain initialized")

    def _create_default_llm(self) -> ChatTongyi:
        """Create default LLM instance"""
        import os
        return ChatTongyi(
            model="qwen-plus",
            temperature=0.7,
            api_key=os.getenv("DASHSCOPE_API_KEY")
        )

    def _load_default_policy(self) -> str:
        """Load default policy data"""
        return """
出差政策规定：

住宿标准：
- 一线城市（北京、上海、深圳、广州）：不超过600元/晚
- 二线城市（杭州、成都、西安等）：不超过400元/晚
- 其他城市：不超过300元/晚

餐饮标准：
- 正餐：不超过100元/餐
- 工作餐：不超过50元/餐
- 招待餐需提前申请

交通标准：
- 市内交通：实报实销，优先公共交通
- 城际交通：2小时内高铁二等座，超过2小时可乘飞机经济舱
- 出租车：特殊情况可使用，需注明原因
"""

    def _build_chain(self) -> RunnableSequence:
        """
        Build sequential chain with three steps

        Chain structure:
        Input → Step1(Policy) → Step2(Weather) → Step3(Itinerary) → Output
        """

        # Step 1: Query policy rules
        policy_prompt = ChatPromptTemplate.from_template(
            """根据出差政策，回答以下问题：

政策内容：
{policy_data}

目的地城市：{destination}
查询类别：{category}

请简要说明该城市的{category}标准。
"""
        )

        policy_chain = (
            policy_prompt
            | self.llm
            | StrOutputParser()
        )

        # Step 2: Query weather (simulated)
        weather_prompt = ChatPromptTemplate.from_template(
            """请根据以下信息提供天气建议：

城市：{destination}

假设当前天气：{weather_info}

请给出简短的天气相关建议（衣物准备、行程安排等）。
"""
        )

        weather_chain = (
            weather_prompt
            | self.llm
            | StrOutputParser()
        )

        # Step 3: Generate itinerary
        itinerary_prompt = ChatPromptTemplate.from_template(
            """请根据以下信息生成出差行程建议：

目的地：{destination}

政策规定：
{policy_result}

天气建议：
{weather_result}

请生成包含以下内容的行程建议：
1. 住宿建议（符合政策标准）
2. 交通建议
3. 注意事项
"""
        )

        itinerary_chain = (
            itinerary_prompt
            | self.llm
            | StrOutputParser()
        )

        # Build sequential pipeline
        # Each step receives output from previous step
        def run_sequential(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Execute steps sequentially with timing"""
            start_time = time.time()
            results = {}

            # Step 1: Policy query
            logger.info("Step 1: Querying policy...")
            step1_start = time.time()
            policy_result = policy_chain.invoke({
                "policy_data": self.policy_data,
                "destination": inputs["destination"],
                "category": inputs.get("category", "accommodation")
            })
            step1_time = time.time() - step1_start
            results["policy_result"] = policy_result
            results["step1_time_ms"] = step1_time * 1000
            logger.info(f"Step 1 completed in {step1_time*1000:.0f}ms")

            # Step 2: Weather query (simulated)
            logger.info("Step 2: Querying weather...")
            step2_start = time.time()
            weather_info = self._get_simulated_weather(inputs["destination"])
            weather_result = weather_chain.invoke({
                "destination": inputs["destination"],
                "weather_info": weather_info
            })
            step2_time = time.time() - step2_start
            results["weather_result"] = weather_result
            results["step2_time_ms"] = step2_time * 1000
            logger.info(f"Step 2 completed in {step2_time*1000:.0f}ms")

            # Step 3: Generate itinerary
            logger.info("Step 3: Generating itinerary...")
            step3_start = time.time()
            itinerary_result = itinerary_chain.invoke({
                "destination": inputs["destination"],
                "policy_result": policy_result,
                "weather_result": weather_result
            })
            step3_time = time.time() - step3_start
            results["itinerary_result"] = itinerary_result
            results["step3_time_ms"] = step3_time * 1000
            logger.info(f"Step 3 completed in {step3_time*1000:.0f}ms")

            # Calculate total time
            total_time = time.time() - start_time
            results["total_time_ms"] = total_time * 1000
            results["execution_mode"] = "sequential"

            logger.info(f"Sequential chain completed in {total_time*1000:.0f}ms")

            return results

        return run_sequential

    def _get_simulated_weather(self, city: str) -> str:
        """Simulate weather data"""
        weather_map = {
            "北京": "晴天，温度25°C，风速3m/s，湿度60%",
            "beijing": "Sunny, 25°C, Wind: 3m/s, Humidity: 60%",
            "上海": "多云，温度22°C，风速2m/s，湿度70%",
            "shanghai": "Cloudy, 22°C, Wind: 2m/s, Humidity: 70%",
            "杭州": "晴天，温度24°C，风速2m/s，湿度65%",
            "hangzhou": "Sunny, 24°C, Wind: 2m/s, Humidity: 65%",
            "深圳": "小雨，温度26°C，风速3m/s，湿度85%",
            "shenzhen": "Light rain, 26°C, Wind: 3m/s, Humidity: 85%",
        }
        return weather_map.get(city.lower(), f"{city}：晴天，温度25°C（模拟数据）")

    @traceable(name="sequential_chain_invoke")
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute sequential chain

        Args:
            inputs: Dictionary with:
                - destination (str): Target city
                - category (str, optional): Policy category (default: "accommodation")

        Returns:
            Dictionary with:
                - policy_result: Policy query result
                - weather_result: Weather query result
                - itinerary_result: Final itinerary
                - step1_time_ms: Time for step 1
                - step2_time_ms: Time for step 2
                - step3_time_ms: Time for step 3
                - total_time_ms: Total execution time
                - execution_mode: "sequential"

        Raises:
            ValueError: Invalid inputs
            RuntimeError: Chain execution failed
        """
        if "destination" not in inputs:
            raise ValueError("Missing required field: destination")

        logger.info(f"Invoking sequential chain for: {inputs['destination']}")

        try:
            result = self.chain(inputs)
            return result
        except Exception as e:
            logger.error(f"Sequential chain failed: {e}")
            raise RuntimeError(f"Sequential chain execution failed: {e}") from e

    def get_performance_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate performance summary from result

        Args:
            result: Chain execution result

        Returns:
            Formatted performance summary string
        """
        step1_time = result.get("step1_time_ms", 0)
        step2_time = result.get("step2_time_ms", 0)
        step3_time = result.get("step3_time_ms", 0)
        total_time = result.get("total_time_ms", 0)

        summary = f"""
Sequential Chain Performance:
========================================
Step 1 (Policy Query):    {step1_time:>8.0f}ms
Step 2 (Weather Query):   {step2_time:>8.0f}ms
Step 3 (Itinerary):       {step3_time:>8.0f}ms
----------------------------------------
Total Time:               {total_time:>8.0f}ms
========================================

Execution Pattern: Step1 → Step2 → Step3
Total Time = Step1 + Step2 + Step3
"""
        return summary


# Example usage
if __name__ == "__main__":
    """Test sequential chain"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Sequential Chain Test")
    print("=" * 60)

    # Create chain
    chain = SequentialChain()

    # Test input
    test_input = {
        "destination": "北京",
        "category": "accommodation"
    }

    print(f"\nInput: {test_input}")
    print("\nExecuting sequential chain...\n")

    # Execute
    result = chain.invoke(test_input)

    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print("\n1. Policy Result:")
    print("-" * 60)
    print(result["policy_result"])

    print("\n2. Weather Result:")
    print("-" * 60)
    print(result["weather_result"])

    print("\n3. Itinerary Result:")
    print("-" * 60)
    print(result["itinerary_result"])

    # Performance summary
    print("\n" + chain.get_performance_summary(result))
