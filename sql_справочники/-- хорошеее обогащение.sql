-- хорошеее обогащение
USE nsi;  -- при необходимости

WITH gdg_filtered AS (
    SELECT
        usl_ok,
        code_usl,
        mkb,
        mkb2,
        mkb3,
        code_oper,
        code_oper2,
        dkk,
        vozg,
        sex,
        duration,
        nsi_ot_per
    FROM gdg
    WHERE nsi_ot_per = '0126'
      AND frac IS NULL
      AND (dkk LIKE 'sh%') --OR dkk IS NULL)
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
        usl_ok,
        code_usl,
        mkb2,
        mkb3,
        code_oper,
        vozg,
        sex,
        duration,
        dkk,
        code_oper2,
        nsi_ot_per
    FROM gdg_filtered
),
-- 2. Для каждой группы — уникальные не‑NULL значения mkb
unique_mkb_per_group AS (
    SELECT DISTINCT
        usl_ok,
        code_usl,
        mkb2,
        mkb3,
        code_oper,
        vozg,
        sex,
        duration,
        dkk,
        code_oper2,
        nsi_ot_per,
        mkb
    FROM gdg_filtered
    WHERE mkb IS NOT NULL
),
-- 3. Агрегация уникальных mkb в одну строку
mkb_aggregated AS (
    SELECT
        usl_ok,
        code_usl,
        mkb2,
        mkb3,
        code_oper,
        vozg,
        sex,
        duration,
        dkk,
        code_oper2,
        nsi_ot_per,
        STRING_AGG(CAST(mkb AS NVARCHAR(MAX)), ', ')
            WITHIN GROUP (ORDER BY mkb) AS mkb_list
    FROM unique_mkb_per_group
    GROUP BY
        usl_ok,
        code_usl,
        mkb2,
        mkb3,
        code_oper,
        vozg,
        sex,
        duration,
        dkk,
        code_oper2,
        nsi_ot_per
)
-- 4. Финальный результат
SELECT
    dg.code_usl,
    mdu_usl.name_usl      AS name_usl,
    dg.mkb2,
    dg.mkb3,
    dg.code_oper,
    mdu_oper.name_usl     AS name_oper,
    dg.code_oper2,
    mdu_oper2.name_usl    AS name_oper2,
    dg.dkk,
    mdu_dkk.name_usl      AS name_dkk,
    dg.vozg,
    CASE dg.vozg
        WHEN 1 THEN N'до 28 дней включительно'
        WHEN 2 THEN N'29 - 90 дней включительно'
        WHEN 3 THEN N'91 день - 1 год'
        WHEN 4 THEN N'0 - 2 лет'
        WHEN 5 THEN N'0 - 18 лет'
        WHEN 6 THEN N'18+ лет'
        WHEN 7 THEN N'0 - 21 год'
        ELSE N''
    END                 AS vozg_desc,
    dg.sex,
    dg.duration,
    CASE dg.duration
        WHEN 1 THEN N'до 3 дней включительно'
        WHEN 2 THEN N'4 - 10 дней включительно'
        WHEN 3 THEN N'11 - 20 дней включительно'
        WHEN 4 THEN N'21 - 30 дней включительно'
        WHEN 5 THEN N'30 дней'
        ELSE N''
    END                 AS duration_desc,
    ISNULL(ma.mkb_list, 'NULL') AS mkb_list
FROM distinct_groups dg
LEFT JOIN mkb_aggregated ma
       ON  dg.code_usl   = ma.code_usl
      AND (dg.mkb2       = ma.mkb2       OR (dg.mkb2       IS NULL AND ma.mkb2       IS NULL))
      AND (dg.mkb3       = ma.mkb3       OR (dg.mkb3       IS NULL AND ma.mkb3       IS NULL))
      AND (dg.code_oper  = ma.code_oper  OR (dg.code_oper  IS NULL AND ma.code_oper  IS NULL))
      AND (dg.vozg       = ma.vozg       OR (dg.vozg       IS NULL AND ma.vozg       IS NULL))
      AND (dg.sex        = ma.sex        OR (dg.sex        IS NULL AND ma.sex        IS NULL))
      AND (dg.duration   = ma.duration   OR (dg.duration   IS NULL AND ma.duration   IS NULL))
      AND (dg.dkk        = ma.dkk        OR (dg.dkk        IS NULL AND ma.dkk        IS NULL))
      AND (dg.code_oper2 = ma.code_oper2 OR (dg.code_oper2 IS NULL AND ma.code_oper2 IS NULL))
      AND (dg.nsi_ot_per = ma.nsi_ot_per OR (dg.nsi_ot_per IS NULL AND ma.nsi_ot_per IS NULL))

-- Расшифровка code_usl / code_oper / code_oper2 / dkk
LEFT JOIN mdu mdu_usl
       ON mdu_usl.code_usl   = dg.code_usl
      AND mdu_usl.nsi_ot_per = dg.nsi_ot_per
LEFT JOIN mdu mdu_oper
       ON mdu_oper.code_usl   = dg.code_oper
      AND mdu_oper.nsi_ot_per = dg.nsi_ot_per
LEFT JOIN mdu mdu_oper2
       ON mdu_oper2.code_usl   = dg.code_oper2
      AND mdu_oper2.nsi_ot_per = dg.nsi_ot_per
LEFT JOIN mdu mdu_dkk
       ON mdu_dkk.code_usl   = dg.dkk
      AND mdu_dkk.nsi_ot_per = dg.nsi_ot_per

ORDER BY
    dg.code_usl,
    dg.code_oper;
