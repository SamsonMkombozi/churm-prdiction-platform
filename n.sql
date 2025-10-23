-- SQL Script to Fix Predictions Table
-- fix_predictions.sql
-- 
-- Run this script directly in your SQLite database to add missing columns

-- Add missing columns to predictions table
ALTER TABLE predictions ADD COLUMN confidence VARCHAR(20) DEFAULT 'medium';
ALTER TABLE predictions ADD COLUMN model_version VARCHAR(50) DEFAULT '1.0.0';
ALTER TABLE predictions ADD COLUMN model_type VARCHAR(100) DEFAULT 'RandomForest';
ALTER TABLE predictions ADD COLUMN risk_factors TEXT;
ALTER TABLE predictions ADD COLUMN feature_values TEXT;
ALTER TABLE predictions ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Update any existing records to have default values
UPDATE predictions 
SET confidence = 'medium' 
WHERE confidence IS NULL;

UPDATE predictions 
SET model_version = '1.0.0' 
WHERE model_version IS NULL;

UPDATE predictions 
SET model_type = 'RandomForest' 
WHERE model_type IS NULL;

UPDATE predictions 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- Add churn prediction columns to customers table if they don't exist
ALTER TABLE customers ADD COLUMN churn_risk VARCHAR(20);
ALTER TABLE customers ADD COLUMN churn_probability FLOAT;
ALTER TABLE customers ADD COLUMN last_prediction_date DATETIME;

-- Verify the changes
SELECT name FROM pragma_table_info('predictions') 
WHERE name IN ('confidence', 'model_version', 'model_type', 'risk_factors', 'feature_values', 'updated_at');

-- Show table structure
.schema predictions