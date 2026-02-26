-- ЧЕЛОВЕКОЧИТАЕМЫЙ GDG

USE nsi;

WITH gdg_filtered AS (
    SELECT
        code_usl,
        code_oper,
        code_oper2,
        dkk,
        vozg,
        sex,
        duration,
        mkb,
        nsi_ot_per
    FROM gdg
    WHERE nsi_ot_per = '0126'
      AND frac IS NULL -- без лучевой терапии
      AND (dkk NOT LIKE 'sh%' OR dkk IS NULL) -- без онкологии
      AND (dkk NOT LIKE '%ivf%' OR dkk IS NULL) -- без ЭКО
      AND (dkk NOT LIKE '%ifv%' OR dkk IS NULL) -- без ЭКО
      AND (code_oper NOT LIKE 'A07%' OR code_oper IS NULL) -- без лучевой терапии
      AND (code_oper NOT LIKE 'A06%' OR code_oper IS NULL) -- без лучевой терапии
      AND (code_usl NOT LIKE 'ds37%' OR code_usl IS NULL) -- без реабилитации ДС
      AND (code_usl NOT LIKE 'st37%' OR code_usl IS NULL) -- без реабилитации КС
)
SELECT
    gdg.code_usl,
    mdu_usl.name_usl,
    STRING_AGG(CAST(gdg.mkb AS NVARCHAR(MAX)), ', ') WITHIN GROUP (ORDER BY gdg.mkb) AS mkb_concat,
    gdg.code_oper,
    mdu_oper.name_usl AS oper_name,
    CONCAT(
        ISNULL(CAST(gdg.vozg AS NVARCHAR(10)), ''),
        ' - ',
        CASE gdg.vozg
            WHEN 1 THEN 'до 28 дней включительно'
            WHEN 2 THEN '29 - 90 дней включительно'
            WHEN 3 THEN '91 день - 1 год'
            WHEN 4 THEN '0 - 2 лет'
            WHEN 5 THEN '0 - 18 лет'
            WHEN 6 THEN '18+ лет'
            WHEN 7 THEN '0 - 21 год'
            ELSE 'не определено'
        END
    ) AS vozg_display,
    gdg.sex,
    CONCAT(
        ISNULL(CAST(gdg.duration AS NVARCHAR(10)), ''),
        ' - ',
        CASE gdg.duration
            WHEN 1 THEN 'до 3 дней включительно'
            WHEN 2 THEN '4 - 10 дней включительно'
            WHEN 3 THEN '11 - 20 дней включительно'
            WHEN 4 THEN '21 - 30 дней включительно'
            WHEN 5 THEN '30 дней'
            ELSE 'не определено'
        END
    ) AS duration_display,
    gdg.dkk,
    mdu_dkk.name_usl AS dkk_name,
    gdg.code_oper2,
    mdu_oper2.name_usl AS oper2_name
FROM gdg_filtered gdg
LEFT JOIN mdu mdu_usl
    ON mdu_usl.code_usl = gdg.code_usl
    AND mdu_usl.nsi_ot_per = gdg.nsi_ot_per
LEFT JOIN mdu mdu_oper
    ON mdu_oper.code_usl = gdg.code_oper
    AND mdu_oper.nsi_ot_per = gdg.nsi_ot_per
LEFT JOIN mdu mdu_oper2
    ON mdu_oper2.code_usl = gdg.code_oper2
    AND mdu_oper2.nsi_ot_per = gdg.nsi_ot_per
LEFT JOIN mdu mdu_dkk
    ON mdu_dkk.code_usl = gdg.dkk
    AND mdu_dkk.nsi_ot_per = gdg.nsi_ot_per
GROUP BY
    gdg.code_usl,
    mdu_usl.name_usl,
    gdg.code_oper,
    mdu_oper.name_usl,
    gdg.vozg,
    gdg.sex,
    gdg.duration,
    gdg.dkk,
    mdu_dkk.name_usl,
    gdg.code_oper2,
    mdu_oper2.name_usl
ORDER BY
    gdg.code_usl,
    gdg.code_oper;