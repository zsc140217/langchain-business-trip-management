#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境验证脚本 - 检查所有依赖和配置

运行方式:
    python verify_environment.py
"""
import sys
import os
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_python_version():
    """检查 Python 版本"""
    print_section("Python 版本检查")
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 11:
        print("[PASS] Python 版本符合要求 (>= 3.11)")
        return True
    else:
        print("[FAIL] Python 版本过低，需要 >= 3.11")
        return False


def check_dependencies():
    """检查核心依赖"""
    print_section("核心依赖检查")
    
    dependencies = [
        ("langchain", "LangChain 核心库"),
        ("langchain_community", "LangChain 社区库"),
        ("fastapi", "FastAPI"),
        ("langserve", "LangServe"),
        ("uvicorn", "Uvicorn"),
        ("faiss", "FAISS 向量存储"),
    ]
    
    all_ok = True
    for package, description in dependencies:
        try:
            __import__(package)
            print(f"[PASS] {description:30s} ({package})")
        except ImportError:
            print(f"[FAIL] {description:30s} ({package}) - 未安装")
            all_ok = False
    
    return all_ok


def check_optional_dependencies():
    """检查可选依赖"""
    print_section("可选依赖检查")
    
    optional = [
        ("sentence_transformers", "Sentence Transformers (Module 2)"),
        ("jieba", "Jieba 中文分词 (Module 2)"),
        ("langgraph", "LangGraph (Module 4)"),
        ("redis", "Redis (缓存)"),
    ]
    
    for package, description in optional:
        try:
            __import__(package)
            print(f"[PASS] {description:40s} ({package})")
        except ImportError:
            print(f"[SKIP] {description:40s} ({package}) - 未安装（可选）")


def check_environment_variables():
    """检查环境变量"""
    print_section("环境变量检查")
    
    required = [
        ("DASHSCOPE_API_KEY", "通义千问 API 密钥", True),
    ]
    
    optional = [
        ("LANGCHAIN_API_KEY", "LangSmith API 密钥", False),
        ("LANGCHAIN_TRACING_V2", "LangSmith 追踪开关", False),
        ("LANGCHAIN_PROJECT", "LangSmith 项目名", False),
    ]
    
    all_ok = True
    
    for var, description, is_required in required:
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else value
            print(f"[PASS] {description:30s} ({var}): {masked}")
        else:
            if is_required:
                print(f"[FAIL] {description:30s} ({var}): 未设置 [必需]")
                all_ok = False
            else:
                print(f"[SKIP] {description:30s} ({var}): 未设置 [可选]")
    
    for var, description, is_required in optional:
        value = os.getenv(var)
        if value:
            print(f"[PASS] {description:30s} ({var}): {value}")
        else:
            print(f"[SKIP] {description:30s} ({var}): 未设置 [可选]")
    
    return all_ok


def check_project_structure():
    """检查项目结构"""
    print_section("项目结构检查")
    
    project_root = Path(__file__).parent
    
    required_dirs = [
        "src/modules/module_1_simple_rag",
        "src/modules/module_2_advanced_rag",
        "src/modules/module_3_react_agent",
        "src/modules/module_4_multi_agent",
        "src/modules/module_5_chain_composition",
        "src/modules/module_6_memory",
        "src/modules/module_7_production",
        "src/api",
        "tests/unit",
        "tests/integration",
        "docs",
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"[PASS] {dir_path}")
        else:
            print(f"[FAIL] {dir_path} - 不存在")
            all_ok = False
    
    return all_ok


def check_module_imports():
    """检查模块导入"""
    print_section("模块导入检查")
    
    # 添加 src 到路径
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))
    
    modules = [
        ("modules.module_1_simple_rag", "Module 1: Simple RAG"),
        ("modules.module_2_advanced_rag.chain", "Module 2: Advanced RAG"),
        ("modules.module_3_react_agent.agent", "Module 3: ReAct Agent"),
        ("modules.module_6_memory", "Module 6: Memory System"),
        ("api.chains", "API Chains"),
    ]
    
    all_ok = True
    for module, description in modules:
        try:
            __import__(module)
            print(f"[PASS] {description:30s} ({module})")
        except ImportError as e:
            print(f"[FAIL] {description:30s} ({module})")
            print(f"       错误: {e}")
            all_ok = False
        except Exception as e:
            print(f"[WARN] {description:30s} ({module})")
            print(f"       警告: {e}")
    
    return all_ok


def print_summary(results):
    """打印总结"""
    print_section("验证总结")
    
    checks = [
        ("Python 版本", results["python"]),
        ("核心依赖", results["dependencies"]),
        ("环境变量", results["env_vars"]),
        ("项目结构", results["structure"]),
        ("模块导入", results["imports"]),
    ]
    
    all_passed = all(result for _, result in checks)
    
    for check_name, passed in checks:
        status = "[PASS] 通过" if passed else "[FAIL] 失败"
        print(f"{check_name:20s} {status}")
    
    print(f"\n{'='*60}")
    if all_passed:
        print("SUCCESS: 所有检查通过！环境配置正确。")
        print("\n下一步:")
        print("  1. 启动 API: ./run_api.sh")
        print("  2. 访问文档: http://localhost:8000/docs")
        print("  3. 查看指南: cat QUICK_START.md")
    else:
        print("WARNING: 部分检查失败，请根据上述提示修复问题。")
        print("\n常见问题:")
        print("  - 依赖缺失: pip install -r requirements.txt")
        print("  - 环境变量: set DASHSCOPE_API_KEY=your-key")
        print("  - 模块导入: set PYTHONPATH=%PYTHONPATH%;%CD%\src")
    print(f"{'='*60}\n")
    
    return all_passed


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  差旅管理系统 - 环境验证脚本")
    print("="*60)
    
    results = {
        "python": check_python_version(),
        "dependencies": check_dependencies(),
        "env_vars": check_environment_variables(),
        "structure": check_project_structure(),
    }
    
    check_optional_dependencies()
    
    # 模块导入检查放最后（可能失败但不影响其他检查）
    results["imports"] = check_module_imports()
    
    all_passed = print_summary(results)
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
