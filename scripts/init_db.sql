-- 初始化数据库表结构
-- Module 4: 记忆系统

-- 用户画像表
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    preferences JSONB DEFAULT '{}',
    preferred_cities JSONB DEFAULT '{}',
    preferred_hotels JSONB DEFAULT '{}',
    frequent_customers JSONB DEFAULT '{}',
    common_intents TEXT[] DEFAULT '{}',
    conversation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 历史查询表
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    thread_id VARCHAR(255),
    query TEXT NOT NULL,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 实体提取表（工作记忆持久化）
CREATE TABLE IF NOT EXISTS extracted_entities (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- person, location, date, amount
    entity_value TEXT NOT NULL,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_thread_id ON query_history(thread_id);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_entities_thread_id ON extracted_entities(thread_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON extracted_entities(entity_type);

-- 更新时间戳触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入测试数据（可选）
INSERT INTO user_profiles (user_id, preferences)
VALUES ('system', '{"initialized": true}')
ON CONFLICT (user_id) DO NOTHING;

COMMENT ON TABLE user_profiles IS '用户画像表 - 存储长期记忆';
COMMENT ON TABLE query_history IS '历史查询表 - 用于检索相似查询';
COMMENT ON TABLE extracted_entities IS '实体提取表 - 工作记忆持久化';

-- Phase 4 P1: 审批记录表
CREATE TABLE IF NOT EXISTS approval_records (
    id SERIAL PRIMARY KEY,
    approval_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    destination VARCHAR(255),
    days INTEGER,
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approver VARCHAR(255) DEFAULT 'system',
    comment TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_records_user_id ON approval_records(user_id);
CREATE INDEX IF NOT EXISTS idx_approval_records_status ON approval_records(status);
CREATE INDEX IF NOT EXISTS idx_approval_records_submitted_at ON approval_records(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_approval_records_approval_id ON approval_records(approval_id);

CREATE TRIGGER update_approval_records_updated_at
    BEFORE UPDATE ON approval_records
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE approval_records IS '审批记录表 - Phase 4 P1 持久化审批申请';
COMMENT ON COLUMN approval_records.approval_id IS '审批单号 (格式: APVYYYYMMDDXXX)';
COMMENT ON COLUMN approval_records.status IS '审批状态: pending/approved/rejected';
COMMENT ON COLUMN approval_records.approver IS '审批人 (自动审批为 system)';
COMMENT ON COLUMN approval_records.submitted_at IS '提交时间';
COMMENT ON COLUMN approval_records.approved_at IS '审批完成时间';
