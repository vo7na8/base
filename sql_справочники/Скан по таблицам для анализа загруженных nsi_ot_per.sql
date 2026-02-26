DECLARE @sql NVARCHAR(MAX) = N'';

SELECT @sql = @sql + 
    'SELECT DISTINCT CAST(nsi_ot_per AS NVARCHAR(MAX)) AS nsi_ot_per, ' + 
    '''' + QUOTENAME(t.TABLE_SCHEMA) + '.' + QUOTENAME(t.TABLE_NAME) + ''' AS table_name ' +
    'FROM ' + QUOTENAME(t.TABLE_SCHEMA) + '.' + QUOTENAME(t.TABLE_NAME) + ' UNION ALL '
FROM INFORMATION_SCHEMA.TABLES t
INNER JOIN INFORMATION_SCHEMA.COLUMNS c 
    ON t.TABLE_CATALOG = c.TABLE_CATALOG 
    AND t.TABLE_SCHEMA = c.TABLE_SCHEMA 
    AND t.TABLE_NAME = c.TABLE_NAME
WHERE t.TABLE_TYPE = 'BASE TABLE'
  AND c.COLUMN_NAME = 'nsi_ot_per'
  AND t.TABLE_CATALOG = 'nsi'  -- укажите имя вашей БД
ORDER BY t.TABLE_NAME;

-- Убираем последний ' UNION ALL '
IF LEN(@sql) > 0
BEGIN
    SET @sql = LEFT(@sql, LEN(@sql) - 10) + ' ORDER BY table_name, nsi_ot_per;';
    EXEC sp_executesql @sql;
END
ELSE
    PRINT 'Нет таблиц с колонкой nsi_ot_per.';