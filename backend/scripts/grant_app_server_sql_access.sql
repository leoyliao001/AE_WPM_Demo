/*
    Grant the Apache/Django service on SCRBAEXDEFRM249 access to WPM.

    Run this script in SSMS connected to:
      Server:   SCRBAEXDEFRM259
      Login:    an account with ALTER ANY LOGIN / sysadmin permission

    The service runs as LocalSystem, so SQL Server sees this Windows account:
      CRB\SCRBAEXDEFRM249$
*/

USE [master];
GO

IF SUSER_ID(N'CRB\SCRBAEXDEFRM249$') IS NULL
BEGIN
    CREATE LOGIN [CRB\SCRBAEXDEFRM249$] FROM WINDOWS;
    PRINT 'Created server login CRB\SCRBAEXDEFRM249$.';
END
ELSE
BEGIN
    PRINT 'Server login CRB\SCRBAEXDEFRM249$ already exists.';
END;
GO

USE [WPM];
GO

IF USER_ID(N'CRB\SCRBAEXDEFRM249$') IS NULL
BEGIN
    CREATE USER [CRB\SCRBAEXDEFRM249$]
        FOR LOGIN [CRB\SCRBAEXDEFRM249$];
    PRINT 'Created WPM database user CRB\SCRBAEXDEFRM249$.';
END
ELSE
BEGIN
    PRINT 'WPM database user CRB\SCRBAEXDEFRM249$ already exists.';
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.database_role_members AS drm
    INNER JOIN sys.database_principals AS role_principal
        ON role_principal.principal_id = drm.role_principal_id
    INNER JOIN sys.database_principals AS member_principal
        ON member_principal.principal_id = drm.member_principal_id
    WHERE role_principal.name = N'db_datareader'
      AND member_principal.name = N'CRB\SCRBAEXDEFRM249$'
)
BEGIN
    ALTER ROLE [db_datareader] ADD MEMBER [CRB\SCRBAEXDEFRM249$];
    PRINT 'Added service account to db_datareader.';
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.database_role_members AS drm
    INNER JOIN sys.database_principals AS role_principal
        ON role_principal.principal_id = drm.role_principal_id
    INNER JOIN sys.database_principals AS member_principal
        ON member_principal.principal_id = drm.member_principal_id
    WHERE role_principal.name = N'db_datawriter'
      AND member_principal.name = N'CRB\SCRBAEXDEFRM249$'
)
BEGIN
    ALTER ROLE [db_datawriter] ADD MEMBER [CRB\SCRBAEXDEFRM249$];
    PRINT 'Added service account to db_datawriter.';
END;
GO

/* Verification: all three result sets should contain one row. */
USE [master];
GO

SELECT
    name,
    type_desc,
    is_disabled
FROM sys.server_principals
WHERE name = N'CRB\SCRBAEXDEFRM249$';
GO

USE [WPM];
GO

SELECT
    name,
    type_desc,
    authentication_type_desc
FROM sys.database_principals
WHERE name = N'CRB\SCRBAEXDEFRM249$';

SELECT
    role_principal.name AS database_role,
    member_principal.name AS member_name
FROM sys.database_role_members AS drm
INNER JOIN sys.database_principals AS role_principal
    ON role_principal.principal_id = drm.role_principal_id
INNER JOIN sys.database_principals AS member_principal
    ON member_principal.principal_id = drm.member_principal_id
WHERE member_principal.name = N'CRB\SCRBAEXDEFRM249$'
  AND role_principal.name IN (N'db_datareader', N'db_datawriter');
GO