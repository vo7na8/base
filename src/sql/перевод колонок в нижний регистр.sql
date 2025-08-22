DECLARE @table_schema NVARCHAR(MAX), @table_name NVARCHAR(MAX), @column_name NVARCHAR(MAX), @new_column_name NVARCHAR(MAX);
DECLARE @sql_command NVARCHAR(MAX);

DECLARE col_cursor CURSOR FOR
SELECT s.name, t.name, c.name
FROM sys.columns c
INNER JOIN sys.tables t ON c.object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE c.name COLLATE Latin1_General_CS_AS <> LOWER(c.name) COLLATE Latin1_General_CS_AS
    AND t.type = 'U';

OPEN col_cursor;
FETCH NEXT FROM col_cursor INTO @table_schema, @table_name, @column_name;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @new_column_name = LOWER(@column_name);
    SET @sql_command = 
        'EXEC sp_rename ''' 
        + QUOTENAME(@table_schema) + '.' + QUOTENAME(@table_name) 
        + '.' + QUOTENAME(@column_name) + ''', ''' 
        + @new_column_name 
        + ''', ''COLUMN'';';

    PRINT @sql_command; -- Проверяем, что нашлось
    --EXEC sp_executesql @sql_command;  -- Раскомментировать для выполнения

    FETCH NEXT FROM col_cursor INTO @table_schema, @table_name, @column_name;
END

CLOSE col_cursor;
DEALLOCATE col_cursor;