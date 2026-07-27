-- 初始化组织架构数据
-- 创建测试用户并建立上下级关系

-- 第一步：清理现有测试数据的manager_id（保留用户）
UPDATE users SET manager_id = NULL;

-- 第二步：创建CEO（最高层级）
INSERT INTO users (user_id, username, email, password_hash, full_name, department, position, is_executive, manager_id)
VALUES ('CEO001', 'ceo', 'ceo@company.com', '$2b$12$placeholder_hash', '张总经理', '总经办', 'CEO', true, NULL)
ON CONFLICT (user_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    is_executive = EXCLUDED.is_executive,
    manager_id = EXCLUDED.manager_id;

-- 第三步：创建副总级别（向CEO汇报）
INSERT INTO users (user_id, username, email, password_hash, full_name, department, position, is_executive, manager_id)
VALUES
('CFO001', 'cfo', 'cfo@company.com', '$2b$12$placeholder_hash', '李财务总监', '财务部', 'CFO', true, 'CEO001'),
('VP_SALES', 'vp_sales', 'vp_sales@company.com', '$2b$12$placeholder_hash', '王销售副总', '销售部', 'VP', true, 'CEO001'),
('VP_TECH', 'vp_tech', 'vp_tech@company.com', '$2b$12$placeholder_hash', '赵技术副总', '技术部', 'VP', true, 'CEO001')
ON CONFLICT (user_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    is_executive = EXCLUDED.is_executive,
    manager_id = EXCLUDED.manager_id;

-- 第四步：创建部门经理（向副总汇报）
INSERT INTO users (user_id, username, email, password_hash, full_name, department, position, is_executive, manager_id)
VALUES
('MGR_SALES_01', 'sales_mgr', 'sales_mgr@company.com', '$2b$12$placeholder_hash', '刘销售经理', '销售部', 'Manager', false, 'VP_SALES'),
('MGR_TECH_01', 'tech_mgr', 'tech_mgr@company.com', '$2b$12$placeholder_hash', '陈技术经理', '技术部', 'Manager', false, 'VP_TECH'),
('MGR_FIN_01', 'fin_mgr', 'fin_mgr@company.com', '$2b$12$placeholder_hash', '周财务经理', '财务部', 'Manager', false, 'CFO001')
ON CONFLICT (user_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    is_executive = EXCLUDED.is_executive,
    manager_id = EXCLUDED.manager_id;

-- 第五步：更新现有测试用户，建立上下级关系
-- employee (张三，销售专员) -> 向销售经理汇报
UPDATE users
SET manager_id = 'MGR_SALES_01',
    department = '销售部',
    position = '销售专员'
WHERE username = 'employee';

-- executive (李总) -> 保留为销售副总（如果不存在VP_SALES）
UPDATE users
SET manager_id = 'CEO001',
    department = '销售部',
    position = 'VP',
    full_name = '王销售副总'
WHERE username = 'executive';

-- admin (系统管理员) -> 向技术副总汇报
UPDATE users
SET manager_id = 'VP_TECH',
    department = 'IT部',
    position = '系统管理员'
WHERE username = 'admin';

-- testuser (测试工程师) -> 向技术经理汇报
UPDATE users
SET manager_id = 'MGR_TECH_01',
    department = '技术部',
    position = 'Software Engineer',
    full_name = '测试工程师'
WHERE user_id = 'test_user_001';

-- 第六步：创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users(manager_id);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);
CREATE INDEX IF NOT EXISTS idx_users_position ON users(position);

-- 验证数据
SELECT
    u1.user_id,
    u1.username,
    u1.full_name,
    u1.department,
    u1.position,
    u2.full_name AS manager_name,
    u2.position AS manager_position
FROM users u1
LEFT JOIN users u2 ON u1.manager_id = u2.user_id
ORDER BY
    CASE
        WHEN u1.position = 'CEO' THEN 1
        WHEN u1.position IN ('CFO', 'VP') THEN 2
        WHEN u1.position = 'Manager' THEN 3
        ELSE 4
    END,
    u1.department,
    u1.full_name;
