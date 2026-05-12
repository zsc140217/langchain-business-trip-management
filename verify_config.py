"""
API密钥配置验证脚本
检查所有必需的API密钥是否已正确配置
"""

import os
import sys
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


def check_api_keys():
    """检查API密钥配置"""
    print("=" * 60)
    print("API密钥配置验证")
    print("=" * 60)

    all_ok = True

    # 1. 检查DASHSCOPE_API_KEY（必需）
    print("\n[1/2] 检查 DASHSCOPE_API_KEY（必需）")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")

    if not dashscope_key:
        print("  [FAIL] 未找到DASHSCOPE_API_KEY")
        print("  提示: 请在.env文件中配置")
        all_ok = False
    elif dashscope_key == "your_api_key_here":
        print("  [FAIL] DASHSCOPE_API_KEY使用默认值，未配置")
        print("  提示: 请替换为真实的API密钥")
        all_ok = False
    else:
        print(f"  [OK] DASHSCOPE_API_KEY已配置")
        print(f"       密钥前缀: {dashscope_key[:10]}...")

    # 2. 检查QWEATHER_API_KEY（可选）
    print("\n[2/2] 检查 QWEATHER_API_KEY（可选）")
    qweather_key = os.getenv("QWEATHER_API_KEY")

    if not qweather_key:
        print("  [SKIP] 未找到QWEATHER_API_KEY（可选，仅天气功能需要）")
    elif qweather_key == "your_weather_api_key_here":
        print("  [SKIP] QWEATHER_API_KEY使用默认值（可选）")
    else:
        print(f"  [OK] QWEATHER_API_KEY已配置")
        print(f"       密钥前缀: {qweather_key[:10]}...")

    print("\n" + "=" * 60)

    return all_ok, dashscope_key


def test_llm_connection(api_key):
    """测试LLM连接"""
    print("\n测试LLM连接...")
    print("-" * 60)

    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.models.llm import get_llm

        print("正在连接通义千问...")
        llm = get_llm()

        print("发送测试消息...")
        response = llm.invoke("你好，请用一句话介绍你自己")

        print(f"\n[OK] LLM连接成功！")
        print(f"响应: {response[:100]}...")
        return True

    except Exception as e:
        print(f"\n[FAIL] LLM连接失败")
        print(f"错误: {e}")
        print("\n可能的原因:")
        print("1. API密钥无效或已过期")
        print("2. 网络连接问题")
        print("3. API额度不足")
        return False


def show_next_steps(has_dashscope):
    """显示后续步骤"""
    print("\n" + "=" * 60)
    print("后续步骤")
    print("=" * 60)

    if not has_dashscope:
        print("\n[FAIL] 缺少必需的API密钥")
        print("\n请按以下步骤配置:")
        print("1. 复制.env.example为.env")
        print("   cp .env.example .env")
        print("\n2. 获取通义千问API密钥")
        print("   访问: https://dashscope.aliyun.com/")
        print("\n3. 编辑.env文件，填入API密钥")
        print("   DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx")
        print("\n4. 重新运行此脚本验证")
        print("   python verify_config.py")
        print("\n详细说明请查看: docs/API_KEY_SETUP.md")
    else:
        print("\n[SUCCESS] API密钥配置完成！")
        print("\n可以开始测试:")
        print("\n1. 测试记忆系统（无需密钥）")
        print("   python tests/test_memory_system.py")
        print("\n2. 测试RAG系统（需要密钥）")
        print("   python tests/test_rag.py")
        print("\n3. 启动服务（需要密钥）")
        print("   python src/main.py")


def main():
    """主函数"""
    # 检查.env文件
    if not os.path.exists(".env"):
        print("[WARNING] 未找到.env文件")
        print("\n建议:")
        print("1. 复制示例文件: cp .env.example .env")
        print("2. 编辑.env文件，填入API密钥")
        print("3. 重新运行此脚本")
        print("\n详细说明: docs/API_KEY_SETUP.md")
        return

    # 检查API密钥
    all_ok, dashscope_key = check_api_keys()

    # 如果配置了DASHSCOPE_API_KEY，测试连接
    if all_ok and dashscope_key and dashscope_key != "your_api_key_here":
        test_llm_connection(dashscope_key)

    # 显示后续步骤
    show_next_steps(all_ok)


if __name__ == "__main__":
    main()
