--Чистый gdg
-- Задания:
-- Требуется расшифровать поля code_usl, code_oper, code_oper2, dkk из справочника mdu (code_usl=code_usl/dkk/code_oper выводим name_usl)
--LEFT JOIN mdu mdu_usl
--    ON mdu_usl.code_usl = gdg.code_usl
--    AND mdu_usl.nsi_ot_per = gdg.nsi_ot_per
--LEFT JOIN mdu mdu_oper
--    ON mdu_oper.code_usl = gdg.code_oper
--    AND mdu_oper.nsi_ot_per = gdg.nsi_ot_per
--LEFT JOIN mdu mdu_oper2
--    ON mdu_oper2.code_usl = gdg.code_oper2
--    AND mdu_oper2.nsi_ot_per = gdg.nsi_ot_per
--LEFT JOIN mdu mdu_dkk
--    ON mdu_dkk.code_usl = gdg.dkk
--    AND mdu_dkk.nsi_ot_per = gdg.nsi_ot_per
-- А так же расшифровать vozg и duration из представленных справочников ниже:
-- CASE gdg.duration
-- WHEN 1 THEN 'до 3 дней включительно'
-- WHEN 2 THEN '4 - 10 дней включительно'
-- WHEN 3 THEN '11 - 20 дней включительно'
-- WHEN 4 THEN '21 - 30 дней включительно'
-- WHEN 5 THEN '30 дней'
-- ELSE ''
-- 
-- CASE gdg.vozg
-- WHEN 1 THEN 'до 28 дней включительно'
-- WHEN 2 THEN '29 - 90 дней включительно'
-- WHEN 3 THEN '91 день - 1 год'
-- WHEN 4 THEN '0 - 2 лет'
-- WHEN 5 THEN '0 - 18 лет'
-- WHEN 6 THEN '18+ лет'
-- WHEN 7 THEN '0 - 21 год'
-- ELSE ''

USE nsi;  -- переключение на вашу базу (если необходимо, иначе закомментируйте)

WITH gdg_filtered AS (
    SELECT
        code_usl,
        mkb,
        mkb2,
        mkb3,
        code_oper,
        code_oper2,
        dkk,
        vozg,
        sex,
        duration
    FROM gdg
    WHERE nsi_ot_per = '0126'
      AND frac IS NULL
      AND (dkk NOT LIKE 'sh%' OR dkk IS NULL)
      AND (dkk NOT LIKE '%ivf%' OR dkk IS NULL)
      AND (dkk NOT LIKE '%ifv%' OR dkk IS NULL)
      AND (code_oper NOT LIKE 'A07%' OR code_oper IS NULL)
      AND (code_oper NOT LIKE 'A06%' OR code_oper IS NULL)
      AND (code_usl NOT LIKE 'ds37%' OR code_usl IS NULL)
      AND (code_usl NOT LIKE 'st37%' OR code_usl IS NULL)
),
-- 1. Уникальные комбинации группирующих полей (все 9 характеристик)
distinct_groups AS (
    SELECT DISTINCT
        code_usl,
        mkb2,
        mkb3,
        code_oper,
        vozg,
        sex,
        duration,
        dkk,
        code_oper2
    FROM gdg_filtered
),
-- 2. Для каждой группы — уникальные не‑NULL значения mkb (подготовка к STRING_AGG)
unique_mkb_per_group AS (
    SELECT DISTINCT
        code_usl,
        mkb2,
        mkb3,
        code_oper,
        vozg,
        sex,
        duration,
        dkk,
        code_oper2,
        mkb
    FROM gdg_filtered
    WHERE mkb IS NOT NULL   -- берём только заполненные диагнозы
),
-- 3. Агрегация уникальных mkb в одну строку (сортировка внутри группы)
mkb_aggregated AS (
    SELECT
        code_usl,
        mkb2,
        mkb3,
        code_oper,
        vozg,
        sex,
        duration,
        dkk,
        code_oper2,
        STRING_AGG(CAST(mkb AS NVARCHAR(MAX)), ', ') WITHIN GROUP (ORDER BY mkb) AS mkb_list
    FROM unique_mkb_per_group
    GROUP BY
        code_usl,
        mkb2,
        mkb3,
        code_oper,
        vozg,
        sex,
        duration,
        dkk,
        code_oper2
)
-- 4. Финальный результат: все группы + подтянутый список mkb (или 'NULL')
SELECT
    dg.code_usl,
    dg.mkb2,
    dg.mkb3,
    dg.code_oper,
    dg.vozg,
    dg.sex,
    dg.duration,
    dg.dkk,
    dg.code_oper2,
    ISNULL(ma.mkb_list, 'NULL') AS mkb_list   -- 'NULL' для групп без кодов
FROM distinct_groups dg

LEFT JOIN mkb_aggregated ma
    ON  dg.code_usl = ma.code_usl
    AND (dg.mkb2 = ma.mkb2 OR (dg.mkb2 IS NULL AND ma.mkb2 IS NULL))
    AND (dg.mkb3 = ma.mkb3 OR (dg.mkb3 IS NULL AND ma.mkb3 IS NULL))
    AND (dg.code_oper = ma.code_oper OR (dg.code_oper IS NULL AND ma.code_oper IS NULL))
    AND (dg.vozg = ma.vozg OR (dg.vozg IS NULL AND ma.vozg IS NULL))
    AND (dg.sex = ma.sex OR (dg.sex IS NULL AND ma.sex IS NULL))
    AND (dg.duration = ma.duration OR (dg.duration IS NULL AND ma.duration IS NULL))
    AND (dg.dkk = ma.dkk OR (dg.dkk IS NULL AND ma.dkk IS NULL))
    AND (dg.code_oper2 = ma.code_oper2 OR (dg.code_oper2 IS NULL AND ma.code_oper2 IS NULL))

ORDER BY
    dg.code_usl,
    dg.code_oper;