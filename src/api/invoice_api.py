"""
发票识别 API 路由
基于百度千帆 qianfan-ocr 的端到端发票识别

功能：
- 单张发票识别
- 批量发票识别（最多10张）
- 健康检查
- 支持 JPG/PNG/PDF 格式
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到 sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.multimodal.dual_engine_recognizer import DualEngineInvoiceRecognizer

# 创建路由
router = APIRouter(prefix="/invoice", tags=["发票识别"])

# 初始化识别器（单例模式）
_recognizer_instance = None


def get_recognizer() -> DualEngineInvoiceRecognizer:
    """获取双引擎识别器单例（自动检测发票版本并分流）"""
    global _recognizer_instance
    if _recognizer_instance is None:
        api_key = os.getenv(
            "QIANFAN_API_KEY",
            "REPLACE_WITH_ENV_VAR"
        )
        _recognizer_instance = DualEngineInvoiceRecognizer(
            api_key=api_key,
            model="qianfan-ocr",
            enable_thinking=True,
            confidence_threshold=0.8
        )
    return _recognizer_instance


async def process_single_file(file: UploadFile) -> Dict[str, Any]:
    """
    处理单个文件的通用逻辑

    Args:
        file: 上传的文件对象

    Returns:
        识别结果字典

    Raises:
        HTTPException: 文件格式不支持或处理失败
    """
    # 检查文件格式
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
        raise HTTPException(400, f"不支持的文件格式: {file_ext}")

    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # PDF 转图片
        if file_ext == '.pdf':
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(tmp_path)
                if len(doc) == 0:
                    raise HTTPException(400, "PDF文件为空")

                # 只处理第一页
                page = doc[0]
                pix = page.get_pixmap(dpi=200)
                jpg_path = tmp_path.replace('.pdf', '.jpg')
                pix.save(jpg_path)
                doc.close()

                # 删除原 PDF，使用转换后的 JPG
                os.unlink(tmp_path)
                tmp_path = jpg_path
            except ImportError:
                raise HTTPException(
                    500,
                    "PDF处理功能不可用，请安装 pymupdf: pip install pymupdf"
                )
            except Exception as e:
                raise HTTPException(500, f"PDF转换失败: {str(e)}")

        # 调用识别器
        recognizer = get_recognizer()
        result = recognizer.recognize(tmp_path)

        # 添加原始文件名
        result['filename'] = file.filename

        return result

    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/recognize", summary="识别单张发票")
async def recognize_invoice(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    识别单张发票

    支持格式：JPG, PNG, PDF

    返回字段：
    - invoice_code: 发票代码
    - invoice_number: 发票号码
    - date: 开票日期 (YYYY-MM-DD)
    - amount: 金额（不含税）
    - tax: 税额
    - tax_rate: 税率（小数形式）
    - total: 价税合计
    - seller_name: 销售方名称
    - seller_tax_id: 销售方纳税人识别号
    - buyer_name: 购买方名称
    - confidence: 置信度 (0-1)
    - warnings: 警告列表
    - need_review: 是否需要人工复核
    - model: 使用的模型名称
    - invoice_version: 发票版本（electronic/old/unknown）
    - engine_type: 使用的识别引擎
    - classification_confidence: 版本分类置信度
    - classification_evidence: 分类依据列表
    """
    try:
        result = await process_single_file(file)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"识别失败: {str(e)}")


@router.post("/batch", summary="批量识别发票")
async def batch_recognize(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """
    批量识别发票（最多10张）

    返回：
    - total: 总文件数
    - success: 成功识别数
    - failed: 失败数
    - results: 识别结果列表
    """
    if len(files) > 10:
        raise HTTPException(400, "最多上传10个文件")

    results = []
    success_count = 0
    failed_count = 0

    for file in files:
        try:
            result = await process_single_file(file)
            results.append({
                "status": "success",
                "data": result
            })
            success_count += 1
        except HTTPException as e:
            results.append({
                "status": "error",
                "filename": file.filename,
                "error": e.detail
            })
            failed_count += 1
        except Exception as e:
            results.append({
                "status": "error",
                "filename": file.filename,
                "error": str(e)
            })
            failed_count += 1

    return {
        "total": len(files),
        "success": success_count,
        "failed": failed_count,
        "results": results
    }


@router.get("/health", summary="健康检查")
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点

    检查项：
    - 识别器状态
    - API Key 配置
    - 模型信息
    """
    try:
        recognizer = get_recognizer()
        return {
            "status": "healthy",
            "model": recognizer.model,
            "enable_thinking": recognizer.enable_thinking,
            "confidence_threshold": recognizer.confidence_threshold,
            "api_configured": bool(recognizer.api_key)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
