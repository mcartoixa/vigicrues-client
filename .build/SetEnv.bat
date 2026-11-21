@ECHO OFF

:: Reset ERRORLEVEL
VERIFY OTHER 2>nul



:: -------------------------------------------------------------------
:: Set environment variables
:: -------------------------------------------------------------------
CALL :SetGitHomePathHelper > nul 2>&1
IF ERRORLEVEL 1 GOTO ERROR_GIT
ECHO SET GitHomePath=%GitHomePath%

uv --version 2>nul
IF ERRORLEVEL 1 GOTO ERROR_UV

ECHO.

CALL :SetLocalEnvHelper 2>nul

:: Git must be on the PATH for pygount (through GitPython)
SET "PATH=%GitHomePath%bin;%PATH%"
GOTO END



:SetLocalEnvHelper
IF EXIST .env (
    FOR /F "eol=# tokens=1* delims==" %%i IN (.env) DO (
        SET "%%i=%%j"
        ECHO SET %%i=%%j
    )
    ECHO.
)
EXIT /B 0



:SetGitHomePathHelper
SET GitHomePath=
FOR /F "tokens=1,2*" %%i IN ('REG QUERY HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Git_is1 /V InstallLocation') DO (
    IF "%%i"=="InstallLocation" (
        SET "GitHomePath=%%k"
    )
)
IF "%GitHomePath%"=="" (
    FOR /F "tokens=1,2*" %%i IN ('REG QUERY HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Git_is1 /V InstallLocation') DO (
        IF "%%i"=="InstallLocation" (
            SET "GitHomePath=%%k"
        )
    )
)
IF "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    IF "%GitHomePath%"=="" (
        FOR /F "tokens=1,2*" %%i IN ('REG QUERY HKEY_CURRENT_USER\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Git_is1 /V InstallLocation') DO (
            IF "%%i"=="InstallLocation" (
                SET "GitHomePath=%%k"
            )
        )
    )
    IF "%GitHomePath%"=="" (
        FOR /F "tokens=1,2*" %%i IN ('REG QUERY HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Git_is1 /V InstallLocation') DO (
            IF "%%i"=="InstallLocation" (
                SET "GitHomePath=%%k"
            )
        )
    )
)
IF "%GitHomePath%"=="" EXIT /B 1
EXIT /B 0



:: -------------------------------------------------------------------
:: Error messages
:: -------------------------------------------------------------------
:ERROR_GIT
ECHO [31mCould not find Git[0m
GOTO END_ERROR

:ERROR_UV
ECHO [31mCould not find uv[0m
GOTO END_ERROR



:: -------------------------------------------------------------------
:: End
:: -------------------------------------------------------------------
:END_ERROR
EXIT /B 1

:END
