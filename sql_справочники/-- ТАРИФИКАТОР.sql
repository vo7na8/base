-- ТАРИФИКАТОР
-- Получение базовой стоимости случая для КСГ (cc)
DECLARE @nsi_per VARCHAR(10) = '0126';

SELECT
    drg.code_usl,
    drg.kz_value,
    drg.ku_value,
    drg.dz_value,
    bz_kdg.value AS bz_value,
    kd_kdg.value AS kd_value,
    ROUND((bz_kdg.value * kz_value * ((1 - dz_value) + dz_value * 1 * ku_value * kd_kdg.value)), 0) AS cc
FROM drg
-- присоединяем базовую ставку
LEFT JOIN kdg AS bz_kdg 
    ON bz_kdg.nsi_ot_per = drg.nsi_ot_per
    AND bz_kdg.code = '01'
    AND bz_kdg.usl_ok = CASE
    WHEN drg.code_usl LIKE 'st%' THEN 1
    WHEN drg.code_usl LIKE 'ds%' THEN 2
    END
-- присоединяем коэффициент дифференциации
LEFT JOIN kdg AS kd_kdg 
    ON kd_kdg.nsi_ot_per = drg.nsi_ot_per
    AND kd_kdg.code = '12'
    AND kd_kdg.usl_ok = CASE
    WHEN drg.code_usl LIKE 'st%' THEN 1
    WHEN drg.code_usl LIKE 'ds%' THEN 2
    END
WHERE drg.nsi_ot_per = @nsi_per


