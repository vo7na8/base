USE [nsi];
SET NOCOUNT ON;

-- 1) Список реально существующих объектов (таблицы/представления) под нужные basename
IF OBJECT_ID('tempdb..#base') IS NOT NULL DROP TABLE #base;
CREATE TABLE #base (basename sysname PRIMARY KEY);

INSERT #base(basename)
SELECT DISTINCT r.basename
FROM [dbo].[nsi_reports] r
JOIN sys.objects o
  ON o.name = r.basename
 AND o.type IN ('U','V')               -- U=table, V=view
 AND o.schema_id = SCHEMA_ID('dbo');

-- 2) Сюда собираем посчитанные количества
IF OBJECT_ID('tempdb..#counts') IS NOT NULL DROP TABLE #counts;
CREATE TABLE #counts (
  basename   sysname NOT NULL,
  nsi_ot_per int     NOT NULL,
  nsi_number int     NOT NULL,
  cnt        bigint  NOT NULL,
  PRIMARY KEY (basename, nsi_ot_per, nsi_number)
);

DECLARE @tbl sysname;
DECLARE @sql nvarchar(max);

DECLARE cur CURSOR FAST_FORWARD FOR
  SELECT basename FROM #base;

OPEN cur;
FETCH NEXT FROM cur INTO @tbl;
WHILE @@FETCH_STATUS = 0
BEGIN
  SET @sql = N'
    INSERT INTO #counts (nsi_ot_per, nsi_number, basename, cnt)
    SELECT d.nsi_ot_per, d.nsi_number, @tbl AS basename, COUNT_BIG(*) AS cnt
    FROM [nsi].[dbo].' + QUOTENAME(@tbl) + N' AS d
    JOIN (
        SELECT DISTINCT nsi_ot_per, nsi_number
        FROM [nsi].[dbo].[nsi_reports]
        WHERE basename = @tbl
    ) r
      ON r.nsi_ot_per = d.nsi_ot_per
     AND r.nsi_number = d.nsi_number
    GROUP BY d.nsi_ot_per, d.nsi_number;
  ';

  BEGIN TRY
    EXEC sp_executesql @sql, N'@tbl sysname', @tbl=@tbl;
  END TRY
  BEGIN CATCH
    -- Пропускаем проблемный справочник, чтобы не падал весь процесс
    PRINT CONCAT('Skip ', @tbl, ': ', ERROR_MESSAGE());
  END CATCH;

  FETCH NEXT FROM cur INTO @tbl;
END
CLOSE cur;
DEALLOCATE cur;

-- 3) Обновляем сводную: пишем что посчиталось; где нет — ставим 0
UPDATE r
SET r.records_upload = ISNULL(c.cnt, 0)
FROM [nsi].[dbo].[nsi_reports] r
LEFT JOIN #counts c
  ON c.basename   = r.basename
 AND c.nsi_ot_per = r.nsi_ot_per
 AND c.nsi_number = r.nsi_number;

-- (по желанию) посмотреть, что посчиталось:
-- SELECT * FROM #counts ORDER BY basename, nsi_ot_per, nsi_number;
