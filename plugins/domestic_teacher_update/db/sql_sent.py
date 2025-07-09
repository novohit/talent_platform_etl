SINGLE_TEACHER_SQL = """
SELECT 
    dt.*,
    rt.link
FROM 
    derived_teacher_data dt
JOIN 
    raw_teacher_data rt 
ON 
    dt.raw_data_id = rt.id
WHERE 
    dt.is_valid = 1
    AND rt.id = {teacher_id}
LIMIT 1;"""

ALL_TEACHERS_SQL = """
SELECT 
    dt.*,        -- 选择derived_teacher_data表的所有字段
    rt.link      -- 选择raw_teacher_data表的link字段
FROM 
    derived_teacher_data dt
JOIN 
    raw_teacher_data rt 
ON 
    dt.raw_data_id = rt.id  -- 连接条件
WHERE 
	dt.is_valid = 1
"""
