-- ============================================
-- 报销审批系统 - 完整数据模型
-- 基于发票识别功能的企业级报销流程
-- ============================================

-- 1. 报销申请主表
CREATE TABLE IF NOT EXISTS reimbursement_applications (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(50) UNIQUE NOT NULL,  -- 报销单号 (格式: REI20260723001)
    user_id VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,  -- 报销标题（如：2026年7月北京出差报销）

    -- 关联信息
    trip_destination VARCHAR(255),  -- 出差目的地
    trip_days INTEGER,  -- 出差天数
    trip_purpose TEXT,  -- 出差事由

    -- 金额汇总
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,  -- 报销总额
    invoice_count INTEGER NOT NULL DEFAULT 0,  -- 发票数量

    -- 状态管理
    status VARCHAR(20) NOT NULL DEFAULT 'draft',  -- draft/submitted/approving/approved/rejected/cancelled
    current_approver VARCHAR(50),  -- 当前审批人
    approval_level INTEGER DEFAULT 0,  -- 当前审批层级

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,  -- 提交时间
    approved_at TIMESTAMP,  -- 最终审批时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 超时控制
    expected_approval_time TIMESTAMP,  -- 预期审批完成时间
    is_timeout BOOLEAN DEFAULT FALSE,  -- 是否超时
    timeout_notified_at TIMESTAMP,  -- 超时通知时间

    -- 附加信息
    remarks TEXT,  -- 备注
    rejection_reason TEXT,  -- 拒绝原因
    pdf_url VARCHAR(500),  -- 生成的PDF报销单URL
    feishu_approval_code VARCHAR(100),  -- 飞书审批实例code

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 2. 发票明细表（关联发票识别结果）
CREATE TABLE IF NOT EXISTS reimbursement_invoices (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(50) NOT NULL,  -- 关联报销申请
    invoice_id VARCHAR(50) UNIQUE NOT NULL,  -- 发票唯一ID

    -- 发票基本信息（来自OCR识别）
    invoice_code VARCHAR(50),  -- 发票代码
    invoice_number VARCHAR(50),  -- 发票号码
    invoice_date DATE,  -- 开票日期
    invoice_type VARCHAR(50) DEFAULT '增值税专用发票',  -- 发票类型

    -- 金额信息
    amount NUMERIC(10, 2) NOT NULL,  -- 金额（不含税）
    tax NUMERIC(10, 2),  -- 税额
    total NUMERIC(10, 2) NOT NULL,  -- 价税合计
    tax_rate NUMERIC(5, 4),  -- 税率

    -- 购销双方
    seller_name VARCHAR(255),  -- 销售方名称
    seller_tax_id VARCHAR(50),  -- 销售方纳税人识别号
    buyer_name VARCHAR(255),  -- 购买方名称
    buyer_tax_id VARCHAR(50),  -- 购买方纳税人识别号

    -- 识别质量
    confidence NUMERIC(5, 3),  -- 识别置信度 (0-1)
    ocr_warnings TEXT[],  -- OCR警告信息
    need_manual_review BOOLEAN DEFAULT FALSE,  -- 是否需要人工复核

    -- 文件存储
    image_url VARCHAR(500),  -- 发票图片URL
    image_hash VARCHAR(64),  -- 图片SHA256哈希（防重复）

    -- 验证状态
    is_verified BOOLEAN DEFAULT FALSE,  -- 是否已验证
    is_duplicate BOOLEAN DEFAULT FALSE,  -- 是否重复报销
    verified_at TIMESTAMP,  -- 验证时间
    verified_by VARCHAR(50),  -- 验证人

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (application_id) REFERENCES reimbursement_applications(application_id) ON DELETE CASCADE
);

-- 3. 审批链配置表
CREATE TABLE IF NOT EXISTS approval_chain_config (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,  -- 规则名称
    department VARCHAR(100),  -- 部门（null表示全局规则）

    -- 金额区间
    min_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    max_amount NUMERIC(10, 2),  -- null表示无上限

    -- 审批链配置（JSON数组）
    -- 格式: [{"level": 1, "role": "direct_manager", "timeout_hours": 24}, ...]
    approval_chain JSONB NOT NULL,

    -- 审批模式
    approval_mode VARCHAR(20) DEFAULT 'sequential',  -- sequential/parallel/or_sign

    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,  -- 优先级（多个规则匹配时使用）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 审批记录表（增强版）
CREATE TABLE IF NOT EXISTS reimbursement_approvals (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(50) NOT NULL,
    approval_level INTEGER NOT NULL,  -- 审批层级

    -- 审批人信息
    approver_id VARCHAR(50) NOT NULL,
    approver_name VARCHAR(100),
    approver_role VARCHAR(50),  -- direct_manager/dept_manager/finance/executive

    -- 审批状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/approved/rejected/transferred/timeout
    decision VARCHAR(20),  -- approve/reject/transfer
    comment TEXT,  -- 审批意见

    -- 时间管理
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 分配时间
    deadline TIMESTAMP,  -- 审批截止时间
    responded_at TIMESTAMP,  -- 响应时间
    duration_minutes INTEGER,  -- 审批耗时（分钟）

    -- 超时处理
    is_timeout BOOLEAN DEFAULT FALSE,
    timeout_action VARCHAR(20),  -- auto_approve/escalate/transfer
    escalated_to VARCHAR(50),  -- 升级给谁

    -- 转派记录
    transferred_from VARCHAR(50),  -- 从谁转派来的
    transfer_reason TEXT,

    FOREIGN KEY (application_id) REFERENCES reimbursement_applications(application_id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(user_id)
);

-- 5. 超时通知记录表
CREATE TABLE IF NOT EXISTS timeout_notifications (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(50) NOT NULL,
    approver_id VARCHAR(50) NOT NULL,

    notification_type VARCHAR(20) NOT NULL,  -- reminder/escalation/auto_approve
    notification_channel VARCHAR(20) NOT NULL,  -- feishu/email/sms

    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_success BOOLEAN DEFAULT FALSE,
    error_message TEXT,

    FOREIGN KEY (application_id) REFERENCES reimbursement_applications(application_id) ON DELETE CASCADE
);

-- 6. 审批操作日志表
CREATE TABLE IF NOT EXISTS approval_audit_logs (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(50) NOT NULL,

    operation VARCHAR(50) NOT NULL,  -- create/submit/approve/reject/transfer/cancel/timeout
    operator_id VARCHAR(50),
    operator_name VARCHAR(100),

    before_status VARCHAR(20),
    after_status VARCHAR(20),

    details JSONB,  -- 详细信息
    ip_address VARCHAR(50),
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (application_id) REFERENCES reimbursement_applications(application_id) ON DELETE CASCADE
);

-- ============================================
-- 索引优化
-- ============================================

-- 报销申请表索引
CREATE INDEX IF NOT EXISTS idx_reimbursement_app_user_id ON reimbursement_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_reimbursement_app_status ON reimbursement_applications(status);
CREATE INDEX IF NOT EXISTS idx_reimbursement_app_submitted_at ON reimbursement_applications(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_reimbursement_app_timeout ON reimbursement_applications(is_timeout, status);
CREATE INDEX IF NOT EXISTS idx_reimbursement_app_current_approver ON reimbursement_applications(current_approver);

-- 发票明细表索引
CREATE INDEX IF NOT EXISTS idx_reimbursement_invoice_app_id ON reimbursement_invoices(application_id);
CREATE INDEX IF NOT EXISTS idx_reimbursement_invoice_hash ON reimbursement_invoices(image_hash);
CREATE INDEX IF NOT EXISTS idx_reimbursement_invoice_code_number ON reimbursement_invoices(invoice_code, invoice_number);
CREATE INDEX IF NOT EXISTS idx_reimbursement_invoice_need_review ON reimbursement_invoices(need_manual_review);

-- 审批链配置索引
CREATE INDEX IF NOT EXISTS idx_approval_chain_dept_amount ON approval_chain_config(department, min_amount, max_amount);

-- 审批记录表索引
CREATE INDEX IF NOT EXISTS idx_reimbursement_approval_app_id ON reimbursement_approvals(application_id);
CREATE INDEX IF NOT EXISTS idx_reimbursement_approval_approver ON reimbursement_approvals(approver_id, status);
CREATE INDEX IF NOT EXISTS idx_reimbursement_approval_timeout ON reimbursement_approvals(is_timeout, status);
CREATE INDEX IF NOT EXISTS idx_reimbursement_approval_deadline ON reimbursement_approvals(deadline);

-- 审计日志索引
CREATE INDEX IF NOT EXISTS idx_approval_audit_app_id ON approval_audit_logs(application_id);
CREATE INDEX IF NOT EXISTS idx_approval_audit_created_at ON approval_audit_logs(created_at DESC);

-- ============================================
-- 触发器
-- ============================================

-- 自动更新updated_at
CREATE TRIGGER update_reimbursement_app_updated_at
    BEFORE UPDATE ON reimbursement_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_approval_chain_config_updated_at
    BEFORE UPDATE ON approval_chain_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 初始审批链配置
-- ============================================

-- 规则1: 1000元以下 - 直属经理审批
INSERT INTO approval_chain_config (rule_name, min_amount, max_amount, approval_chain, approval_mode)
VALUES (
    '小额报销-直属经理审批',
    0,
    1000,
    '[
        {"level": 1, "role": "direct_manager", "timeout_hours": 24, "auto_approve_on_timeout": false}
    ]'::jsonb,
    'sequential'
) ON CONFLICT DO NOTHING;

-- 规则2: 1000-5000元 - 直属经理 + 部门经理
INSERT INTO approval_chain_config (rule_name, min_amount, max_amount, approval_chain, approval_mode)
VALUES (
    '中额报销-两级审批',
    1000,
    5000,
    '[
        {"level": 1, "role": "direct_manager", "timeout_hours": 24, "auto_approve_on_timeout": false},
        {"level": 2, "role": "dept_manager", "timeout_hours": 48, "auto_approve_on_timeout": false}
    ]'::jsonb,
    'sequential'
) ON CONFLICT DO NOTHING;

-- 规则3: 5000-20000元 - 直属经理 + 部门经理 + 财务
INSERT INTO approval_chain_config (rule_name, min_amount, max_amount, approval_chain, approval_mode)
VALUES (
    '大额报销-三级审批',
    5000,
    20000,
    '[
        {"level": 1, "role": "direct_manager", "timeout_hours": 24, "auto_approve_on_timeout": false},
        {"level": 2, "role": "dept_manager", "timeout_hours": 48, "auto_approve_on_timeout": false},
        {"level": 3, "role": "finance", "timeout_hours": 72, "auto_approve_on_timeout": false}
    ]'::jsonb,
    'sequential'
) ON CONFLICT DO NOTHING;

-- 规则4: 20000元以上 - 全链路审批（含高管）
INSERT INTO approval_chain_config (rule_name, min_amount, max_amount, approval_chain, approval_mode)
VALUES (
    '特大额报销-全链路审批',
    20000,
    NULL,
    '[
        {"level": 1, "role": "direct_manager", "timeout_hours": 24, "auto_approve_on_timeout": false},
        {"level": 2, "role": "dept_manager", "timeout_hours": 48, "auto_approve_on_timeout": false},
        {"level": 3, "role": "finance", "timeout_hours": 72, "auto_approve_on_timeout": false},
        {"level": 4, "role": "executive", "timeout_hours": 96, "auto_approve_on_timeout": false}
    ]'::jsonb,
    'sequential'
) ON CONFLICT DO NOTHING;

-- ============================================
-- 注释说明
-- ============================================

COMMENT ON TABLE reimbursement_applications IS '报销申请主表 - 存储报销单据基本信息';
COMMENT ON TABLE reimbursement_invoices IS '发票明细表 - 存储OCR识别的发票信息';
COMMENT ON TABLE approval_chain_config IS '审批链配置表 - 根据金额和部门配置审批流程';
COMMENT ON TABLE reimbursement_approvals IS '审批记录表 - 记录每一级审批的详细信息';
COMMENT ON TABLE timeout_notifications IS '超时通知记录表 - 审批超时催办记录';
COMMENT ON TABLE approval_audit_logs IS '审批操作日志表 - 完整审计追踪';

COMMENT ON COLUMN reimbursement_applications.application_id IS '报销单号 格式:REI+YYYYMMDD+3位序号';
COMMENT ON COLUMN reimbursement_applications.status IS 'draft:草稿 submitted:已提交 approving:审批中 approved:已通过 rejected:已拒绝 cancelled:已取消';
COMMENT ON COLUMN reimbursement_applications.feishu_approval_code IS '飞书审批实例code,用于状态同步';
COMMENT ON COLUMN reimbursement_invoices.image_hash IS '发票图片SHA256哈希,用于防止重复报销';
COMMENT ON COLUMN reimbursement_invoices.confidence IS 'OCR识别置信度,低于0.8建议人工复核';
COMMENT ON COLUMN approval_chain_config.approval_mode IS 'sequential:依次审批 parallel:并行审批(会签) or_sign:或签(任一通过即可)';
COMMENT ON COLUMN reimbursement_approvals.timeout_action IS 'auto_approve:自动通过 escalate:升级上级 transfer:转派他人';
