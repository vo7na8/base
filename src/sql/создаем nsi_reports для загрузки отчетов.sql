CREATE TABLE nsi_reports (
    id INT IDENTITY(1,1) PRIMARY KEY,
    package_name NVARCHAR(255) NOT NULL,
    nsi_ot_per NVARCHAR(10) NOT NULL,
    nsi_number NVARCHAR(10) NOT NULL,
    filename NVARCHAR(255) NOT NULL,
    basename NVARCHAR(255) NOT NULL,
    ext NVARCHAR(10) NOT NULL,
    sha256 CHAR(64) NOT NULL,
    modified DATETIME2 NOT NULL,
    records_read INT NOT NULL,
    records_upload INT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME()
);
