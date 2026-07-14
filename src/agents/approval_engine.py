# -*- coding: utf-8 -*-
"""
ApprovalEngine - 审批域执行器
Phase 3.2: ApprovalEngine Core

处理报销申请的自动审批和人工审批流程
"""
import json
import logging
from src.monitoring import track_approval_metric, track_approval_duration_metric
from typing import Dict, Any, Optional
from datetime import datetime
from src.modules.module_5_langgraph.state import create_initial_state
from src.agents.approval_db_service import ApprovalDBService


logger = logging.getLogger(__name__)


class ApprovalEngine:
    """
    审批域执行器

    职责：
    1. 提取申请信息（目的地、天数、金额）
    2. 根据金额路由到自动审批或人工审批
    3. 发送飞书通知
    4. 更新工作记忆中的审批状态
    """

    def __init__(
        self,
        llm,
        memory_service,
        feishu_client,
        approval_graph,
        auto_approval_threshold: int = 1000,
        db_service: Optional[ApprovalDBService] = None
    ):
        """
        初始化审批引擎

        Args:
            llm: 语言模型实例
            memory_service: 记忆服务实例
            feishu_client: 飞书客户端实例
            approval_graph: LangGraph 审批工作流
            auto_approval_threshold: 自动审批阈值（元），默认1000
        """
        self.llm = llm
        self.memory_service = memory_service
        self.feishu_client = feishu_client
        self.approval_graph = approval_graph
        self.auto_approval_threshold = auto_approval_threshold
        self.db_service = db_service or ApprovalDBService()

        # 审批单号计数器（简单实现，生产环境应使用数据库）
        self._approval_counter = 0

    def execute(
        self,
        query: str,
        user_id: str,
        conversation_id: str
    ) -> str:
        """
        执行审批流程

        Args:
            query: 用户查询（报销申请）
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            审批结果消息字符串
        """
        logger.info(f"[ApprovalEngine] 处理审批请求: user_id={user_id}, query={query}")

        try:
            # 1. 提取申请信息
            approval_info = self._extract_application_info(query, user_id)

            # 2. 根据金额判断审批路径
            estimated_amount = approval_info.get("estimated_amount", 0)

            if estimated_amount < self.auto_approval_threshold:
                logger.info(f"[ApprovalEngine] 金额{estimated_amount}元 < 阈值{self.auto_approval_threshold}元，走自动审批")
                result = self._auto_approve(approval_info)
                return result["message"]  # 返回消息字符串
            else:
                logger.info(f"[ApprovalEngine] 金额{estimated_amount}元 >= 阈值{self.auto_approval_threshold}元，走人工审批")
                result = self._manual_approval(approval_info)
                return result["message"]  # 返回消息字符串

        except Exception as e:
            logger.error(f"[ApprovalEngine] 审批流程执行失败: {e}", exc_info=True)
            raise

    def _extract_application_info(
        self,
        query: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        从用户查询中提取申请信息

        Args:
            query: 用户查询
            user_id: 用户ID

        Returns:
            申请信息字典
        """
        logger.info(f"[ApprovalEngine] 提取申请信息: {query}")

        # 使用 LLM 提取结构化信息
        extraction_prompt = f"""从以下报销申请中提取信息，返回JSON格式：

用户申请：{query}

请提取以下字段（如果没有则为null）：
- destination: 出差目的地（城市名）
- days: 出差天数（整数）
- estimated_amount: 报销金额（整数，单位：元）

只返回JSON，不要其他内容。
格式示例：{{"destination": "北京", "days": 3, "estimated_amount": 800}}
"""

        try:
            response = self.llm.invoke(extraction_prompt)
            content = response.content.strip()

            # 移除可能的代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            extracted = json.loads(content.strip())

            # 构建完整的申请信息
            approval_info = {
                "approval_id": self._generate_approval_id(),
                "user_id": user_id,
                "destination": extracted.get("destination"),
                "days": extracted.get("days"),
                "estimated_amount": extracted.get("estimated_amount"),
                "query": query,
                "submit_time": datetime.now().isoformat(),
            }

            # 如果金额为空，尝试估算
            if approval_info["estimated_amount"] is None:
                logger.info("[ApprovalEngine] 金额未提供，尝试估算")
                approval_info["estimated_amount"] = self._estimate_amount(
                    approval_info["destination"],
                    approval_info["days"]
                )

            logger.info(f"[ApprovalEngine] 提取成功: {approval_info}")
            return approval_info

        except json.JSONDecodeError as e:
            logger.error(f"[ApprovalEngine] JSON解析失败: {e}, content={content}")
            raise ValueError(f"无法解析申请信息: {e}")
        except Exception as e:
            logger.error(f"[ApprovalEngine] 信息提取失败: {e}", exc_info=True)
            raise ValueError(f"申请信息提取失败: {e}")

    def _auto_approve(self, approval_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动审批流程（金额 < 阈值）

        Args:
            approval_info: 申请信息

        Returns:
            审批结果
        """
        approval_id = approval_info["approval_id"]
        logger.info(f"[ApprovalEngine] 执行自动审批: {approval_id}")

        try:
            # 1. persistent approval record to database
            self._save_to_db(approval_info, status="approved", approver="system", comment="auto approved")

            # 1. call LangGraph approval workflow (auto approve)
            initial_state = create_initial_state(
                query=approval_info.get("query", ""),
                max_iterations=3
            )
            # 设置审批状态为已通过
            initial_state["approval_status"] = "approved"

            graph_result = self.approval_graph.invoke(
                initial_state,
                config={"configurable": {"thread_id": approval_info["user_id"]}}
            )

            logger.info(f"[ApprovalEngine] LangGraph 执行结果: {graph_result}")

            # 2. 更新工作记忆（使用 memory_service 统一接口）
            # 首先添加初始审批记录
            approval_record = {
                **approval_info,
                "status": "pending"
            }
            working_memory = self.memory_service.working_memory_manager.get_or_create(
                approval_info["user_id"]
            )
            working_memory.add_approval(approval_record)

            # 然后更新为已批准状态
            self.memory_service.update_approval_status(
                user_id=approval_info["user_id"],
                conversation_id=approval_info["user_id"],  # 使用 user_id 作为 conversation_id
                approval_id=approval_id,
                status="approved",
                approver="system",
                comment="自动审批通过"
            )

            logger.info(f"[ApprovalEngine] 工作记忆已更新: {approval_id}")

            # 3. 发送飞书通知（不阻塞主流程）
            try:
                card_content = self._build_auto_approval_card(approval_info)
                self.feishu_client.send_card_message(
                    title="✅ 审批通过",
                    content=card_content,
                    card_type="success"
                )
                logger.info(f"[ApprovalEngine] 飞书通知已发送: {approval_id}")
            except Exception as e:
                logger.error(f"[ApprovalEngine] 飞书通知发送失败: {e}")
                # 继续执行，不阻塞审批流程

            # 4. 返回结果
            return {
                "status": "approved",
                "approval_id": approval_id,
                "message": f"您的报销申请已自动通过！金额：¥{approval_info['estimated_amount']}",
                "details": approval_record
            }

        except Exception as e:
            logger.error(f"[ApprovalEngine] 自动审批失败: {e}", exc_info=True)
            raise

    def _manual_approval(self, approval_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        人工审批流程（金额 >= 阈值）

        Args:
            approval_info: 申请信息

        Returns:
            审批结果（待审批状态）
        """
        approval_id = approval_info["approval_id"]
        logger.info(f"[ApprovalEngine] 执行人工审批: {approval_id}")

        try:
            # persist to database
            self._save_to_db(approval_info, status="pending", approver="pending", comment="manual approval pending")

            # 1. 更新工作记忆（待审批状态）- 使用 memory_service 统一接口
            # 首先添加初始审批记录
            approval_record = {
                **approval_info,
                "status": "pending"
            }
            working_memory = self.memory_service.working_memory_manager.get_or_create(
                approval_info["user_id"]
            )
            working_memory.add_approval(approval_record)

            # 使用 update 方法更新状态和审批人
            self.memory_service.update_approval_status(
                user_id=approval_info["user_id"],
                conversation_id=approval_info["user_id"],  # 使用 user_id 作为 conversation_id
                approval_id=approval_id,
                status="pending",
                approver="待分配",
                comment="等待审批人处理"
            )

            logger.info(f"[ApprovalEngine] 工作记忆已更新: {approval_id}")

            # 2. 发送飞书卡片给审批人（不阻塞主流程）
            try:
                # 使用带交互按钮的审批卡片
                self.feishu_client.send_approval_card(
                    approval_id=approval_id,
                    user_id=approval_info["user_id"],
                    applicant=approval_info.get("user_id", "未知用户"),
                    destination=approval_info.get("destination", "未知"),
                    days=approval_info.get("days", 0),
                    amount=approval_info.get("estimated_amount", 0)
                )
                logger.info(f"[ApprovalEngine] 飞书交互审批卡片已发送: {approval_id}")
            except Exception as e:
                logger.error(f"[ApprovalEngine] 飞书通知发送失败: {e}")
                # 继续执行，不阻塞审批流程

            # 3. 返回结果（待审批）
            return {
                "status": "pending",
                "approval_id": approval_id,
                "message": f"申请已提交，金额超过{self.auto_approval_threshold}元，需要人工审批，请等待审批人处理。",
                "details": approval_record
            }

        except Exception as e:
            logger.error(f"[ApprovalEngine] 人工审批流程失败: {e}", exc_info=True)
            raise

    def _generate_approval_id(self) -> str:
        """
        生成审批单号

        格式: APV + YYYYMMDD + 序列号

        Returns:
            审批单号
        """
        self._approval_counter += 1
        date_str = datetime.now().strftime("%Y%m%d")
        return f"APV{date_str}{self._approval_counter:03d}"

    def _estimate_amount(
        self,
        destination: Optional[str],
        days: Optional[int]
    ) -> int:
        """
        估算报销金额（简化实现）

        Args:
            destination: 目的地
            days: 天数

        Returns:
            估算金额（元）
        """
        # 简化实现：每天500元 * 天数
        # 实际应该调用 search_policy 工具查询差旅标准
        if days is None:
            days = 1

        estimated = days * 500
        logger.info(f"[ApprovalEngine] 估算金额: {destination} {days}天 = ¥{estimated}")
        return estimated


    def _save_to_db(
        self,
        approval_info: Dict[str, Any],
        status: str = "pending",
        approver: str = "system",
        comment: str = None,
    ):
        """Persist approval record to PostgreSQL (non-blocking, log warning on failure)"""
        try:
            self.db_service.save_approval_record(
                approval_info=approval_info,
                status=status,
                approver=approver,
                comment=comment,
            )
        except Exception as e:
            logger.warning(f"[ApprovalEngine] DB write failed (fallback): {e}")

    def _build_auto_approval_card(self, approval_info: Dict[str, Any]) -> str:
        """
        构建自动审批通知卡片内容

        Args:
            approval_info: 申请信息

        Returns:
            Markdown 格式的卡片内容
        """
        return f"""**审批单号**: {approval_info['approval_id']}

**目的地**: {approval_info['destination']}
**天数**: {approval_info['days']}天
**金额**: ¥{approval_info['estimated_amount']}

**审批结果**: ✅ 自动通过
**审批时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

您的报销申请已自动审批通过，祝您工作顺利！
"""

    def _build_manual_approval_card(self, approval_info: Dict[str, Any]) -> str:
        """
        构建人工审批通知卡片内容

        Args:
            approval_info: 申请信息

        Returns:
            Markdown 格式的卡片内容
        """
        return f"""**审批单号**: {approval_info['approval_id']}

**申请人**: {approval_info['user_id']}
**目的地**: {approval_info['destination']}
**天数**: {approval_info['days']}天
**金额**: ¥{approval_info['estimated_amount']}

**提交时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ 金额超过自动审批阈值，请及时处理。

**操作**: 请登录系统进行审批
"""

    def process_approval_result(
        self,
        approval_id: str,
        operation: str,
        approver_id: str
    ) -> Dict[str, Any]:
        """
        处理审批结果（审批人点击通过/拒绝按钮后调用）

        Args:
            approval_id: 审批单号
            operation: 操作类型 ("approve" or "reject")
            approver_id: 审批人ID

        Returns:
            处理结果字典
        """
        logger.info(
            f"[ApprovalEngine] 处理审批结果: "
            f"approval_id={approval_id}, operation={operation}, approver={approver_id}"
        )

        try:
            # 1. 从工作记忆或数据库获取审批记录
            approval_record = self._get_approval_record(approval_id)

            if not approval_record:
                raise ValueError(f"审批记录不存在: {approval_id}")

            # 检查审批状态
            current_status = approval_record.get("status")
            if current_status != "pending":
                logger.warning(f"[ApprovalEngine] 审批已处理: {current_status}")
                return {
                    "status": current_status,
                    "message": f"该审批已{current_status}，无需重复操作",
                    "applicant": approval_record.get("user_id", "未知"),
                    "amount": approval_record.get("estimated_amount", 0)
                }

            # 2. 更新审批状态
            new_status = "approved" if operation == "approve" else "rejected"
            approval_record["status"] = new_status
            approval_record["approver"] = approver_id
            approval_record["approval_time"] = datetime.now().isoformat()
            approval_record["comment"] = "审批人手动操作"

            # 3. 更新工作记忆
            user_id = approval_record["user_id"]
            working_memory = self.memory_service.working_memory_manager.get_or_create(user_id)
            working_memory.update_approval_status(approval_id, new_status)

            logger.info(f"[ApprovalEngine] 工作记忆已更新: {approval_id} -> {new_status}")

            # 4. 更新数据库
            try:
                self.db_service.update_approval_status(
                    approval_id=approval_id,
                    status=new_status,
                    approver=approver_id,
                    comment="审批人手动操作"
                )
            except Exception as e:
                logger.warning(f"[ApprovalEngine] DB更新失败: {e}")

            # 5. 通知申请人
            try:
                self._notify_applicant(approval_record, new_status)
            except Exception as e:
                logger.error(f"[ApprovalEngine] 通知申请人失败: {e}")

            # 6. 记录监控指标
            track_approval_metric(
                type="manual",
                status=new_status
            )

            # 7. 返回结果
            return {
                "status": new_status,
                "message": f"审批{'通过' if operation == 'approve' else '拒绝'}成功",
                "applicant": user_id,
                "amount": approval_record.get("estimated_amount", 0),
                "approval_id": approval_id
            }

        except Exception as e:
            logger.error(f"[ApprovalEngine] 处理审批结果失败: {e}", exc_info=True)
            raise

    def _get_approval_record(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """
        获取审批记录（优先从数据库，降级到工作记忆）

        Args:
            approval_id: 审批单号

        Returns:
            审批记录，不存在返回 None
        """
        # 1. 尝试从数据库获取
        try:
            record = self.db_service.get_approval_record(approval_id)
            if record:
                return record
        except Exception as e:
            logger.warning(f"[ApprovalEngine] DB查询失败，降级到工作记忆: {e}")

        # 2. 降级：遍历工作记忆查找
        # TODO: 需要优化，应该维护 approval_id -> user_id 的索引
        logger.warning(f"[ApprovalEngine] 从工作记忆查找审批记录（性能较差）")
        return None

    def _notify_applicant(self, approval_record: Dict[str, Any], status: str):
        """
        通知申请人审批结果

        Args:
            approval_record: 审批记录
            status: 审批状态 ("approved" or "rejected")
        """
        user_id = approval_record["user_id"]
        amount = approval_record.get("estimated_amount", 0)
        approval_id = approval_record["approval_id"]

        if status == "approved":
            message = f"✅ 您的出差报销申请已通过！\n\n审批单号: {approval_id}\n金额: ¥{amount}"
            card_type = "success"
        else:
            message = f"❌ 您的出差报销申请被拒绝\n\n审批单号: {approval_id}\n金额: ¥{amount}\n请联系审批人了解详情"
            card_type = "error"

        try:
            self.feishu_client.send_card_message(
                title="审批结果通知",
                content=message,
                card_type=card_type
            )
            logger.info(f"[ApprovalEngine] 已通知申请人: {user_id}")
        except Exception as e:
            logger.error(f"[ApprovalEngine] 飞书通知失败: {e}")


