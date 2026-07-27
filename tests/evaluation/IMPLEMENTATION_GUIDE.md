# 评估系统实施指南

## 📋 目录

1. [环境配置检查清单](#环境配置检查清单)
2. [测试用例扩充指南](#测试用例扩充指南)
3. [半自动化流程说明](#半自动化流程说明)
4. [故障排查指南](#故障排查指南)
5. [性能调优建议](#性能调优建议)
6. [评测周期建议](#评测周期建议)

---

## 环境配置检查清单

### 1. Python环境

```bash
# 检查Python版本（需要3.9+）
python --version

# 验证虚拟环境
python -c "import sys; print(sys.prefix)"

# 检查关键依赖
python -c "import langchain; print(langchain.__version__)"
python -c "import dashscope; print('DashScope installed')"
python -c "import psycopg2; print('PostgreSQL driver installed')"
```

**预期输出：**
- Python 3.9+ 
- 虚拟环境路径（非系统Python）
- 所有依赖成功导入

---

### 2. API凭证配置

#### 检查环境变量文件

```bash
# 复制示例配置
cp .env.example .env

# 验证必需变量
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_keys = [
    'DASHSCOPE_API_KEY',
    'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'
]


missing = [k for k in required_keys if not os.getenv(k)]
if missing:
    print(f'ERROR: Missing keys: {missing}')
else:
    print('SUCCESS: All required environment variables configured')
"
```

**常见问题：**

| 问题 | 解决方案 |
|------|---------|
| `DASHSCOPE_API_KEY` 未设置 | 访问 https://dashscope.console.aliyun.com/ 获取API Key |
| 数据库连接失败 | 检查 PostgreSQL 是否运行：`pg_isready -h localhost -p 5432` |
| `.env` 文件不生效 | 确认文件在项目根目录，检查文件编码为UTF-8无BOM |

---

### 3. 数据库配置

#### 初始化数据库

```bash
# 检查PostgreSQL服务状态
pg_isready -h localhost -p 5432

# 连接数据库
psql -h localhost -p 5432 -U postgres -d business_trip

# 验证必需表存在
psql -h localhost -U postgres -d business_trip -c "\dt"
```

**预期表清单：**
- `travel_policies` - 差旅政策文档
- `approval_records` - 审批记录
- `user_profiles` - 用户信息（包含职级、部门）

#### 数据库初始化脚本

```bash
# 如果表不存在，运行初始化脚本
psql -h localhost -U postgres -d business_trip -f scripts/init_db.sql
```

---

### 4. 向量数据库配置

#### 检查ChromaDB持久化目录

```bash
# 检查向量数据库目录
ls -la chroma_db/

# 验证集合存在
python -c "
import chromadb
client = chromadb.PersistentClient(path='chroma_db')
collections = client.list_collections()
print(f'Collections: {[c.name for c in collections]}')
"
```

**预期输出：**
```
Collections: ['travel_policies_bge', 'travel_policies_dashscope']
```

**如果集合不存在：**

```bash
# 重建向量数据库
python scripts/build_vector_db.py
```

---

### 5. 微调模型路径

#### 验证本地微调模型

```bash
# 检查微调模型文件
ls -la learning/models/bge-large-zh-travel-finetuned/

# 验证模型可加载
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('learning/models/bge-large-zh-travel-finetuned')
print(f'Model loaded: {model}')
"
```

**预期文件：**
- `config.json`
- `pytorch_model.bin` 或 `model.safetensors`
- `tokenizer.json`
- `tokenizer_config.json`

**如果模型不存在：**

```bash
# 重新训练微调模型
cd learning/T2_LLM_Finetuning/embedding_finetune
python train_bge_model.py
```

---

### 6. 完整环境验证脚本

创建 `tests/evaluation/verify_environment.py`：

```python
#!/usr/bin/env python
"""环境配置验证脚本"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print("✓ Python版本: {}.{}.{}".format(version.major, version.minor, version.micro))
        return True
    else:
        print("✗ Python版本过低: {}.{}.{} (需要3.9+)".format(version.major, version.minor, version.micro))
        return False

def check_env_vars():
    """检查环境变量"""
    load_dotenv()
    required = ['DASHSCOPE_API_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD']
    missing = [k for k in required if not os.getenv(k)]
    
    if not missing:
        print(f"✓ 环境变量: {len(required)}/{len(required)} 已配置")
        return True
    else:
        print(f"✗ 环境变量缺失: {missing}")
        return False

def check_dependencies():
    """检查依赖库"""
    deps = ['langchain', 'dashscope', 'psycopg2', 'chromadb', 'sentence_transformers']
    failed = []
    
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            failed.append(dep)
    
    if not failed:
        print(f"✓ 依赖库: {len(deps)}/{len(deps)} 已安装")
        return True
    else:
        print(f"✗ 依赖库缺失: {failed}")
        return False

def check_database():
    """检查数据库连接"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME', 'business_trip'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        conn.close()
        print("✓ 数据库连接: 成功")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

def check_vector_db():
    """检查向量数据库"""
    try:
        import chromadb
        client = chromadb.PersistentClient(path='chroma_db')
        collections = client.list_collections()
        print(f"✓ 向量数据库: {len(collections)} 个集合")
        return True
    except Exception as e:
        print(f"✗ 向量数据库错误: {e}")
        return False

def check_finetuned_model():
    """检查微调模型"""
    model_path = Path('learning/models/bge-large-zh-travel-finetuned')
    if model_path.exists() and (model_path / 'config.json').exists():
        print(f"✓ 微调模型: {model_path}")
        return True
    else:
        print(f"✗ 微调模型不存在: {model_path}")
        return False

def main():
    print("=" * 50)
    print("评估系统环境验证")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_env_vars,
        check_dependencies,
        check_database,
        check_vector_db,
        check_finetuned_model
    ]
    
    results = [check() for check in checks]
    
    print("=" * 50)
    if all(results):
        print("✓ 所有检查通过，环境配置正确")
        return 0
    else:
        print(f"✗ {sum(not r for r in results)}/{len(results)} 项检查失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

**运行验证：**

```bash
python tests/evaluation/verify_environment.py
```

---


## 测试用例扩充指南

### 当前测试用例统计

**现有测试用例数量：**
- test_data/test_cases.json: 10条
- test_cases/approval_test_cases.json: 2条
- test_cases/rag_test_cases.json: 2条
- test_cases/routing_test_cases.json: 2条
- **总计：16条，目标：100+条**

### 扩充策略

#### 1. 维度分析法

按复杂度、场景、难度三个维度系统化生成：

- **复杂度**：Simple(60条) / Medium(50条) / Complex(20条)
- **场景**：Booking(20) / Policy(25) / Approval(15) / Weather(10) / Complex(30)
- **难度**：Easy(35) / Medium(40) / Hard(25)

#### 2. 模板生成法

使用参数化模板批量生成测试用例：

```python
# 查询模板示例
templates = [
    "帮我查询{date}从{origin}到{destination}的{class}机票",
    "{position}能坐{flight_class}吗？",
    "去{city}出差住宿标准是多少？"
]

# 参数值
params = {
    "date": ["明天", "后天", "下周一"],
    "origin": ["北京", "上海", "广州"],
    "destination": ["上海", "北京", "成都"],
    "class": ["经济舱", "商务舱"]
}

# 生成笛卡尔积 -> 生成多条测试用例
```

运行：`python tests/evaluation/generate_test_cases_batch.py`

#### 3. 边界用例（手动添加）

- 预算临界值测试
- 同义词挑战（魔都→上海）
- 多跳推理
- 对抗样本（超出范围的查询）

#### 4. 扩充清单

- [ ] 模板生成 → +54条
- [ ] 边界用例 → +20条
- [ ] 同义词 → +10条
- [ ] 多跳推理 → +10条
- [ ] 对抗样本 → +10条
- [ ] 真实用户查询 → +30条

**目标：150条**

---

## 半自动化流程说明

### 三层评分架构

```
Layer 1: Code-based（自动化100%）
  - 工具调用准确性
  - 政策合规性检查
  - 输出格式验证
  时间: <10ms/case  成本: ¥0

Layer 2: Model-based（半自动化）
  - Correctness（需人工校准）
  - Relevance（自动化）
  - Groundedness（自动化）
  时间: ~2s/case  成本: ~¥0.02/case

Layer 3: Human（10-20%抽样）
  - 边界案例复审
  - 模型评分校准
  - 新场景标注
  时间: ~30s/case
```

### 自动化环节（无需人工）

**1. Code-based检查**

```bash
# 批量运行确定性检查
python tests/evaluation/run_code_based_eval.py --test-set test_cases/all.json
```

检查项：
- 工具调用准确性
- 预算超标检测
- 舱位等级违规
- 关键词检查

**2. Model-based自动化维度**

```bash
# 仅运行自动化维度
python tests/evaluation/run_model_eval.py \
  --dimensions relevance,groundedness \
  --auto-mode
```

### 半自动化环节（需人工校准）

**Correctness评分校准流程：**

1. LLM初步评分
2. 识别低置信度case（confidence < 0.7）
3. 人工审核10-20%
4. 使用人工标注校准模型
5. 重新评分全量

**人工审核界面：**

```bash
python tests/evaluation/human_review_ui.py
# 访问 http://localhost:5001/review
```

### 自动化程度总结

| 环节 | 自动化 | 人工工作量 |
|------|--------|-----------|
| Code-based | 100% | 0小时 |
| Relevance | 100% | 0小时 |
| Groundedness | 100% | 0小时 |
| Correctness | 80% | 1-2小时/100cases |
| 新场景标注 | 0% | 0.5-1小时/10cases |
| 边界复审 | 0% | 2-3小时/100cases |

**总体：70-80%自动化，人工3-6小时/100cases**

---

## 故障排查指南

### 1. 环境错误

**ModuleNotFoundError**
```bash
pip install -r requirements.txt
```

**数据库连接失败**
```bash
pg_isready -h localhost -p 5432
psql -h localhost -U postgres -d business_trip
```

**向量数据库未初始化**
```bash
python scripts/build_vector_db.py
```

### 2. 评估执行错误

**测试用例格式错误**
```python
# 验证JSON格式
python -c "
import json
with open('test_cases/my_cases.json') as f:
    cases = json.load(f)
    for c in cases:
        assert 'task_id' in c
        assert 'user_query' in c
        assert 'expected_tools' in c
"
```

**API限流**
```python
# 添加限流装饰器
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=60)
def call_llm_eval(case):
    return evaluator.eval(case)
```

### 3. 评分异常

**评分过于宽松**

调整提示词增加严格性，明确评分标准。

**False positive过多**

使用语义相似度而非精确匹配：

```python
from difflib import SequenceMatcher

def fuzzy_match(keyword, text):
    return any(
        SequenceMatcher(None, keyword, word).ratio() > 0.8 
        for word in text.split()
    )
```

### 4. 性能问题

**评估耗时过长**

启用并行处理：

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(eval_single_case, test_cases))
```

预期加速：5-10倍

### 调试工具

```bash
# 单条用例调试
python tests/evaluation/debug_single_case.py --case-id simple_001 --verbose

# 日志分析
python tests/evaluation/analyze_eval_logs.py --log-file eval_results.json

# 结果对比
python tests/evaluation/compare_eval_results.py --baseline v1.json --current v2.json
```

---


## 性能调优建议

### 1. 并行化执行

**问题：** 串行评估耗时过长

**解决方案：**
- 使用ThreadPoolExecutor并行评估
- max_workers=10，预期加速6倍
- 从30分钟降至5分钟/100cases

### 2. 成本优化

**当前成本（100条用例）：¥6**
- Code-based: ¥0
- Model-based: ¥6（Relevance + Groundedness + Correctness）

**优化策略：**

1. **分层评估**：Code-based失败直接跳过LLM → 节省30%
2. **混合模型**：便宜模型(qwen-turbo)做简单评估 → 节省75%
3. **采样评估**：开发阶段仅评估20% → 节省80%

### 3. 缓存策略

- 首次运行：5分钟
- 缓存命中：<10秒
- 加速比：30x

### 4. 数据库优化

使用批量查询预加载数据：
- 优化前：100次查询，~5秒
- 优化后：2次批量查询，~0.5秒
- 加速比：10x

---

## 评测周期建议

### 推荐评测计划

| 评测类型 | 频率 | 用例数 | 耗时 | 成本 | 触发条件 |
|---------|------|--------|------|------|---------|
| 快速冒烟测试 | 每次commit | 20条 | 2分钟 | ¥0.5 | Git hook |
| 标准评测 | 每周1次 | 100条 | 10分钟 | ¥6 | 定时任务 |
| 深度评测 | 每月1次 | 100条+人工 | 3小时 | ¥6 | 手动 |
| 基准测试 | 每季度1次 | 200条 | 5小时 | ¥12 | 版本发布 |

### 自动化触发

**Git Hook（开发阶段）：**



**CI/CD（测试/生产）：**



### 告警规则

- 通过率下降>5% → Critical告警
- 存在CRITICAL违规 → High告警
- 成本增加>50% → Medium告警

---

## 总结

### 实施步骤（5-6天）

1. **环境配置**（1天）
   - 运行 verify_environment.py
   - 配置依赖和数据库

2. **测试用例扩充**（2-3天）
   - 模板生成 → +54条
   - 手动补充 → +50条
   - 达到100+条

3. **自动化流程**（1天）
   - 配置CI/CD
   - 设置告警

4. **首次基准评估**（1天）
   - 全量评估
   - 人工校准
   - 保存基准

5. **持续迭代**
   - 每周标准评测
   - 每月深度评测

### 关键指标

- **自动化率**：70-80%
- **人工工作量**：3-6小时/100cases
- **评估成本**：¥6/100cases
- **评估耗时**：10分钟/100cases（并行）
- **通过率目标**：≥80%

---

**文档版本**：v1.0  
**最后更新**：2026-07-25  
**评估系统开发团队**
