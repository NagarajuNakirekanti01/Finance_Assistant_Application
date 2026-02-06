-- Finance Assistant Database Schema
-- Create database tables for comprehensive personal finance management

-- Users table with enhanced security features
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role ENUM('user', 'premium', 'admin') DEFAULT 'user',
    
    -- MFA fields
    mfa_secret VARCHAR(255) NULL,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    backup_codes TEXT NULL,
    
    -- Profile fields
    phone VARCHAR(20) NULL,
    date_of_birth DATETIME NULL,
    profile_picture VARCHAR(500) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    
    INDEX idx_email (email),
    INDEX idx_active (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Accounts table for bank accounts, credit cards, etc.
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Account details
    name VARCHAR(255) NOT NULL,
    account_type ENUM('checking', 'savings', 'credit_card', 'investment', 'loan') NOT NULL,
    institution_name VARCHAR(255) NOT NULL,
    account_number VARCHAR(255) NULL, -- Encrypted
    routing_number VARCHAR(255) NULL, -- Encrypted
    
    -- Balance information
    current_balance DECIMAL(15, 2) DEFAULT 0.00,
    available_balance DECIMAL(15, 2) DEFAULT 0.00,
    credit_limit DECIMAL(15, 2) NULL,
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    
    -- External integration
    plaid_account_id VARCHAR(255) NULL,
    plaid_access_token VARCHAR(500) NULL, -- Encrypted
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_synced TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_account_type (account_type),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    
    -- Transaction details
    amount DECIMAL(15, 2) NOT NULL,
    transaction_type ENUM('income', 'expense', 'transfer') NOT NULL,
    category ENUM(
        'salary', 'freelance', 'investment_income', 'other_income',
        'food_dining', 'shopping', 'transportation', 'entertainment',
        'bills_utilities', 'healthcare', 'education', 'travel',
        'insurance', 'taxes', 'other_expense',
        'transfer_in', 'transfer_out'
    ) NOT NULL,
    subcategory VARCHAR(100) NULL,
    
    -- Description and metadata
    description VARCHAR(500) NOT NULL,
    merchant_name VARCHAR(255) NULL,
    location VARCHAR(255) NULL,
    notes TEXT NULL,
    
    -- Transaction status
    is_pending BOOLEAN DEFAULT FALSE,
    is_recurring BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(3, 2) NULL, -- ML categorization confidence
    
    -- Dates
    transaction_date TIMESTAMP NOT NULL,
    posted_date TIMESTAMP NULL,
    
    -- External integration
    plaid_transaction_id VARCHAR(255) NULL,
    external_account_id VARCHAR(255) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    INDEX idx_account_id (account_id),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_category (category),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_merchant_name (merchant_name),
    INDEX idx_amount (amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Budgets table
CREATE TABLE IF NOT EXISTS budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Budget details
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    period ENUM('weekly', 'monthly', 'quarterly', 'yearly') NOT NULL,
    
    -- Status and tracking
    is_active BOOLEAN DEFAULT TRUE,
    alert_threshold DECIMAL(5, 2) DEFAULT 80.0, -- Alert at 80% of budget
    current_spent DECIMAL(15, 2) DEFAULT 0.00,
    
    -- Dates
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_category (category),
    INDEX idx_period (period),
    INDEX idx_start_date (start_date),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Goals table for financial goals
CREATE TABLE IF NOT EXISTS goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Goal details
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    goal_type ENUM('savings', 'debt_payoff', 'investment', 'emergency_fund', 'vacation', 'house_down_payment', 'other') NOT NULL,
    target_amount DECIMAL(15, 2) NOT NULL,
    current_amount DECIMAL(15, 2) DEFAULT 0.00,
    
    -- Timeline
    target_date TIMESTAMP NULL,
    monthly_contribution DECIMAL(15, 2) DEFAULT 0.00,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_achieved BOOLEAN DEFAULT FALSE,
    priority INT DEFAULT 1, -- 1=high, 2=medium, 3=low
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    achieved_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_goal_type (goal_type),
    INDEX idx_target_date (target_date),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat conversations table
CREATE TABLE IF NOT EXISTS chat_conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    message_type ENUM('user', 'bot') NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(100) NULL,
    confidence DECIMAL(3, 2) NULL,
    metadata JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Recurring transactions table
CREATE TABLE IF NOT EXISTS recurring_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_id INT NOT NULL,
    
    -- Transaction template
    amount DECIMAL(15, 2) NOT NULL,
    transaction_type ENUM('income', 'expense', 'transfer') NOT NULL,
    category ENUM(
        'salary', 'freelance', 'investment_income', 'other_income',
        'food_dining', 'shopping', 'transportation', 'entertainment',
        'bills_utilities', 'healthcare', 'education', 'travel',
        'insurance', 'taxes', 'other_expense',
        'transfer_in', 'transfer_out'
    ) NOT NULL,
    description VARCHAR(500) NOT NULL,
    merchant_name VARCHAR(255) NULL,
    
    -- Recurrence pattern
    frequency ENUM('daily', 'weekly', 'monthly', 'quarterly', 'yearly') NOT NULL,
    interval_value INT DEFAULT 1, -- Every X frequency units
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NULL,
    next_due_date TIMESTAMP NOT NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    auto_create BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_processed TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_account_id (account_id),
    INDEX idx_next_due_date (next_due_date),
    INDEX idx_frequency (frequency)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bill reminders table
CREATE TABLE IF NOT EXISTS bill_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Bill details
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    amount DECIMAL(15, 2) NULL,
    due_date TIMESTAMP NOT NULL,
    
    -- Reminder settings
    remind_days_before INT DEFAULT 3,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_frequency ENUM('monthly', 'quarterly', 'yearly') NULL,
    
    -- Status
    is_paid BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    paid_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_due_date (due_date),
    INDEX idx_is_paid (is_paid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Financial reports table
CREATE TABLE IF NOT EXISTS financial_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Report details
    report_type ENUM('monthly_summary', 'expense_analysis', 'budget_performance', 'goal_progress', 'net_worth') NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    
    -- Report data
    report_data JSON NOT NULL,
    file_path VARCHAR(500) NULL, -- For generated PDF/Excel files
    
    -- Date range
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    
    -- Status
    status ENUM('generating', 'completed', 'failed') DEFAULT 'generating',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_report_type (report_type),
    INDEX idx_start_date (start_date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit log table for security and compliance
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    
    -- Action details
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100) NULL,
    
    -- Request details
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    endpoint VARCHAR(255) NULL,
    method VARCHAR(10) NULL,
    
    -- Additional data
    old_values JSON NULL,
    new_values JSON NULL,
    metadata JSON NULL,
    
    -- Status
    status ENUM('success', 'failure', 'error') NOT NULL,
    error_message TEXT NULL,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_resource_type (resource_type),
    INDEX idx_created_at (created_at),
    INDEX idx_ip_address (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Session storage for JWT token blacklisting
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    device_info TEXT NULL,
    ip_address VARCHAR(45) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create views for common queries
CREATE OR REPLACE VIEW user_account_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.first_name,
    u.last_name,
    COUNT(a.id) as total_accounts,
    SUM(CASE WHEN a.account_type IN ('checking', 'savings') THEN a.current_balance ELSE 0 END) as total_cash,
    SUM(CASE WHEN a.account_type = 'credit_card' THEN a.current_balance ELSE 0 END) as total_credit_debt,
    SUM(CASE WHEN a.account_type = 'investment' THEN a.current_balance ELSE 0 END) as total_investments
FROM users u
LEFT JOIN accounts a ON u.id = a.user_id AND a.is_active = TRUE
WHERE u.is_active = TRUE
GROUP BY u.id, u.email, u.first_name, u.last_name;

-- Create view for monthly spending by category
CREATE OR REPLACE VIEW monthly_spending_by_category AS
SELECT 
    a.user_id,
    t.category,
    DATE_FORMAT(t.transaction_date, '%Y-%m') as month,
    SUM(t.amount) as total_amount,
    COUNT(t.id) as transaction_count,
    AVG(t.amount) as avg_amount
FROM transactions t
JOIN accounts a ON t.account_id = a.id
WHERE t.transaction_type = 'expense'
GROUP BY a.user_id, t.category, DATE_FORMAT(t.transaction_date, '%Y-%m');