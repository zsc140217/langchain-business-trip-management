-- 初始化数据库表结构
-- Module 4: 记忆系统
-- P0-1: 用户认证系统 (2026-07-15)

-- ============================================
-- P0-1: 用户认证表
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    position VARCHAR(100),
    is_executive BOOLEAN DEFAULT FALSE,  -- 是否高管（影响差旅标准和审批阈值）
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户会话表（用于Token管理）
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 用户认证索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

COMMENT ON TABLE users IS '用户表：存储用户基本信息和角色（P0-1）';
COMMENT ON COLUMN users.is_executive IS '是否高管：影响差旅交通等级和住宿标准';
COMMENT ON COLUMN users.is_admin IS '是否管理员：拥有系统管理权限';
COMMENT ON TABLE user_sessions IS '用户会话表：存储JWT Token会话信息';

-- ============================================
-- Module 4: 记忆系统
-- ============================================

-- 用户画像表（P0-3: 关联到users表）
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(50) PRIMARY KEY,
    preferences JSONB DEFAULT '{}',
    preferred_cities JSONB DEFAULT '{}',
    preferred_hotels JSONB DEFAULT '{}',
    frequent_customers JSONB DEFAULT '{}',
    common_intents TEXT[] DEFAULT '{}',
    conversation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
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

-- ============================================
-- P0-2: 会话管理系统 (2026-07-15)
-- ============================================

-- 会话表（对话持久化）
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    message_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
);

-- 会话管理索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message_at ON conversations(last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at ASC);

-- 会话更新时间戳触发器
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE conversations IS '会话表：存储用户对话会话（P0-2）';
COMMENT ON TABLE messages IS '消息表：存储对话消息历史（P0-2）';
COMMENT ON COLUMN messages.role IS '消息角色：user/assistant/system';
COMMENT ON COLUMN messages.metadata IS '消息元数据：可存储工具调用、引用文档等信息';

-- ============================================
-- P0-1: 插入测试用户数据
-- ============================================
-- 密码均为: test123456
-- 哈希值: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYCqr6vQXri

INSERT INTO users (user_id, username, email, password_hash, full_name, department, position, is_executive, is_active, is_admin, phone)
VALUES
    ('user_001', 'employee', 'employee@company.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYCqr6vQXri', '张三', '技术部', '工程师', FALSE, TRUE, FALSE, '13800138001'),
    ('user_002', 'manager', 'manager@company.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYCqr6vQXri', '李四', '技术部', '部门经理', FALSE, TRUE, FALSE, '13800138002'),
    ('user_003', 'executive', 'executive@company.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYCqr6vQXri', '王五', '管理层', '副总经理', TRUE, TRUE, TRUE, '13800138003')
ON CONFLICT (user_id) DO NOTHING;

-- 为测试用户创建用户画像
INSERT INTO user_profiles (user_id, preferences, conversation_count)
VALUES
    ('user_001', '{"role": "employee", "department": "技术部"}', 0),
    ('user_002', '{"role": "manager", "department": "技术部"}', 0),
    ('user_003', '{"role": "executive", "level": "高管"}', 0)
ON CONFLICT (user_id) DO NOTHING;

-- 测试用户说明
COMMENT ON TABLE users IS '用户表：已插入3个测试账户 (employee/manager/executive)，密码均为 test123456';
