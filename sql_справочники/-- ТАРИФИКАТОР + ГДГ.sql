-- ТАРИФИКАТОР + ГДГ
USE nsi;

WITH 
-- 1. Тарификатор: вычисляем cc для каждого code_usl периода 0126
tariff_cte AS (
    SELECT
        drg.code_usl,
        drg.kz_value,
        drg.ku_value,
        drg.dz_value,
        bz_kdg.value AS bz_value,
        kd_kdg.value AS kd_value,
        ROUND((bz_kdg.value * kz_value * ((1 - dz_value) + dz_value * 1 * ku_value * kd_kdg.value)), 0) AS cc
    FROM drg
    LEFT JOIN kdg AS bz_kdg 
        ON bz_kdg.nsi_ot_per = drg.nsi_ot_per
        AND bz_kdg.code = '01'
        AND bz_kdg.usl_ok = CASE
            WHEN drg.code_usl LIKE 'st%' THEN 1
            WHEN drg.code_usl LIKE 'ds%' THEN 2
        END
    LEFT JOIN kdg AS kd_kdg 
        ON kd_kdg.nsi_ot_per = drg.nsi_ot_per
        AND kd_kdg.code = '12'
        AND kd_kdg.usl_ok = CASE
            WHEN drg.code_usl LIKE 'st%' THEN 1
            WHEN drg.code_usl LIKE 'ds%' THEN 2
        END
    WHERE drg.nsi_ot_per = '0126'
),

-- 2. Фильтрация справочника gdg
gdg_filtered AS (
    SELECT
        code_usl,
        code_oper,
        code_oper2,
        dkk,
        vozg,
        sex,
        duration,
        mkb,
        mkb2,
        mkb3,
        nsi_ot_per
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
      AND (code_usl NOT LIKE 'ds19.079' OR code_usl IS NULL)
      and code_oper = 'A22.12.003.001'
),

-- 3. Обогащаем данными из mdu и тарификатора
gdg_enriched AS (
    SELECT
        gdg.code_usl,
        mdu_usl.name_usl,
        gdg.code_oper,
        mdu_oper.name_usl AS oper_name,
        gdg.vozg,
        gdg.sex,
        gdg.duration,
        gdg.dkk,
        mdu_dkk.name_usl AS dkk_name,
        gdg.code_oper2,
        mdu_oper2.name_usl AS oper2_name,
        tariff.cc AS tariff_cc,
        gdg.mkb,
        gdg.mkb2,
        gdg.mkb3
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
    LEFT JOIN tariff_cte tariff
        ON tariff.code_usl = gdg.code_usl
),

-- 4. Создаем ключ группы для всех полей, кроме mkb*
group_keys AS (
    SELECT *,
        -- Уникальный идентификатор группы (все поля, кроме mkb*)
        CONCAT_WS('|',
            ISNULL(code_usl, ''), 
            ISNULL(name_usl, ''),
            ISNULL(code_oper, ''), 
            ISNULL(oper_name, ''),
            ISNULL(CAST(vozg AS VARCHAR), ''),
            ISNULL(sex, ''),
            ISNULL(CAST(duration AS VARCHAR), ''),
            ISNULL(dkk, ''),
            ISNULL(dkk_name, ''),
            ISNULL(code_oper2, ''),
            ISNULL(oper2_name, ''),
            ISNULL(CAST(tariff_cc AS VARCHAR), '')
        ) AS group_key
    FROM gdg_enriched
    WHERE mkb IS NOT NULL OR mkb2 IS NOT NULL OR mkb3 IS NOT NULL
),

-- 5. Нумеруем строки внутри каждой группы
numbered AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY group_key
            ORDER BY mkb, mkb2, mkb3
        ) AS rn
    FROM group_keys
),

-- 6. Группируем с разбиением на блоки по 50
grouped AS (
    SELECT
        code_usl,
        name_usl,
        code_oper,
        oper_name,
        vozg,
        sex,
        duration,
        dkk,
        dkk_name,
        code_oper2,
        oper2_name,
        tariff_cc,
        (rn - 1) / 50 AS block_num,
        -- Собираем mkb-коды только в пределах блока
        STRING_AGG(CASE WHEN mkb IS NOT NULL THEN mkb END, ', ') 
            WITHIN GROUP (ORDER BY mkb, mkb2, mkb3) AS mkb_concat,
        STRING_AGG(CASE WHEN mkb2 IS NOT NULL THEN mkb2 END, ', ') 
            WITHIN GROUP (ORDER BY mkb, mkb2, mkb3) AS mkb2_concat,
        STRING_AGG(CASE WHEN mkb3 IS NOT NULL THEN mkb3 END, ', ') 
            WITHIN GROUP (ORDER BY mkb, mkb2, mkb3) AS mkb3_concat
    FROM numbered
    GROUP BY
        code_usl,
        name_usl,
        code_oper,
        oper_name,
        vozg,
        sex,
        duration,
        dkk,
        dkk_name,
        code_oper2,
        oper2_name,
        tariff_cc,
        (rn - 1) / 50  -- группировка по номеру блока
)

-- 7. Финальный вывод
SELECT
    code_usl,
    name_usl,
    mkb_concat AS mkb,
    mkb2_concat AS mkb2,
    mkb3_concat AS mkb3,
    code_oper,
    oper_name,
    CONCAT(
        ISNULL(CAST(vozg AS NVARCHAR(10)), ''),
        '. ',
        CASE vozg
            WHEN 1 THEN 'до 28 дней включительно'
            WHEN 2 THEN '29 - 90 дней включительно'
            WHEN 3 THEN '91 день - 1 год'
            WHEN 4 THEN '0 - 2 лет'
            WHEN 5 THEN '0 - 18 лет'
            WHEN 6 THEN '18+ лет'
            WHEN 7 THEN '0 - 21 год'
            ELSE ''
        END
    ) AS vozg_display,
    sex,
    CONCAT(
        ISNULL(CAST(duration AS NVARCHAR(10)), ''),
        '. ',
        CASE duration
            WHEN 1 THEN 'до 3 дней включительно'
            WHEN 2 THEN '4 - 10 дней включительно'
            WHEN 3 THEN '11 - 20 дней включительно'
            WHEN 4 THEN '21 - 30 дней включительно'
            WHEN 5 THEN '30 дней'
            ELSE ''
        END
    ) AS duration_display,
    dkk,
    dkk_name,
    code_oper2,
    oper2_name,
    tariff_cc
FROM grouped
ORDER BY 
    code_usl,
    code_oper,
    block_num;