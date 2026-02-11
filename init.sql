-- ============================================================================
-- INIT.SQL - SKIN CANCER ANALYZER
-- Script de inicialização do banco de dados PostgreSQL
-- ============================================================================

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TABELA: users
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABELA: analyses
-- ============================================================================
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    image_filename VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    prediction_class VARCHAR(100),
    confidence FLOAT,
    predictions JSONB,
    metadata JSONB,
    processing_time FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABELA: audit_log
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ÍNDICES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);

-- ============================================================================
-- FUNÇÃO: updated_at trigger
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_analyses_updated_at ON analyses;
CREATE TRIGGER update_analyses_updated_at
    BEFORE UPDATE ON analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- DADOS INICIAIS (Opcional)
-- ============================================================================
-- Inserir usuário admin padrão (senha: admin123 - ALTERAR EM PRODUÇÃO!)
-- Hash gerado com bcrypt
INSERT INTO users (username, email, password_hash, is_admin)
VALUES (
    'admin',
    'admin@skincancer.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY0wcZZ4FnI9Raa',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- VIEWS (Opcional)
-- ============================================================================
CREATE OR REPLACE VIEW analysis_stats AS
SELECT
    DATE(created_at) as analysis_date,
    COUNT(*) as total_analyses,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
    AVG(processing_time) as avg_processing_time,
    AVG(confidence) as avg_confidence
FROM analyses
GROUP BY DATE(created_at)
ORDER BY analysis_date DESC;

-- ============================================================================
-- GRANTS (Ajustar conforme necessário)
-- ============================================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO skin_cancer_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO skin_cancer_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO skin_cancer_user;

-- ============================================================================
-- INFORMAÇÕES
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Skin Cancer Analyzer - Database Initialized';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Tables created: users, analyses, audit_log';
    RAISE NOTICE 'Default admin user: admin@skincancer.local';
    RAISE NOTICE 'Default admin password: admin123';
    RAISE NOTICE 'IMPORTANT: Change admin password in production!';
    RAISE NOTICE '============================================';
END $$;
