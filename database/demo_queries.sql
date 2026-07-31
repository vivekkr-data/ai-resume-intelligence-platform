-- AI Resume Intelligence Platform: PostgreSQL demo queries

-- 1. Table sizes
SELECT 'analysis_records' AS table_name, COUNT(*) AS rows FROM analysis_records
UNION ALL
SELECT 'analysis_feedback', COUNT(*) FROM analysis_feedback
UNION ALL
SELECT 'job_postings', COUNT(*) FROM job_postings;

-- 2. Average fit by target role
SELECT
    job_title,
    COUNT(*) AS analyses,
    ROUND(AVG(overall_score)::numeric, 2) AS average_fit,
    ROUND(AVG(semantic_score)::numeric, 2) AS average_semantic,
    ROUND(AVG(skill_score)::numeric, 2) AS average_skill_coverage
FROM analysis_records
GROUP BY job_title
ORDER BY analyses DESC, average_fit DESC;

-- 3. Recent high-fit analyses
SELECT id, created_at, filename, job_title, overall_score, model_used, processing_ms
FROM analysis_records
WHERE overall_score >= 70
ORDER BY created_at DESC
LIMIT 20;

-- 4. Model usage and performance
SELECT
    model_used,
    COUNT(*) AS analyses,
    ROUND(AVG(overall_score)::numeric, 2) AS average_fit,
    ROUND(AVG(processing_ms)::numeric, 0) AS average_processing_ms
FROM analysis_records
GROUP BY model_used
ORDER BY analyses DESC;

-- 5. Human feedback rate
SELECT
    COUNT(*) FILTER (WHERE helpful) AS helpful,
    COUNT(*) FILTER (WHERE NOT helpful) AS not_helpful,
    COUNT(*) AS total,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE helpful) / NULLIF(COUNT(*), 0),
        2
    ) AS helpful_percentage
FROM analysis_feedback;

-- 6. Active job catalog
SELECT id, title, company, location, skills
FROM job_postings
WHERE is_active = TRUE
ORDER BY title;
