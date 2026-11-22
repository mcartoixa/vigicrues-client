@ECHO OFF

:: Reset ERRORLEVEL
VERIFY OTHER 2>nul
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
IF ERRORLEVEL 1 GOTO ERROR_EXT

SET _EXIT_CODE=0
SET _NO_PAUSE=0
SET _TARGET=build
SET _VERBOSE=
PUSHD "%~dp0"
GOTO ARGS

:SHOW_USAGE
ECHO.
ECHO Usage: "build [analyze|build|clean|compile|package|rebuild|release|test|test-live] [/log] [/NoPause] [/?]"
ECHO.
ECHO.                /NoPause  - Does not pause after completion
ECHO.                /log      - Creates an extensive log file
ECHO.                /?        - Gets the usage for this script
IF "%_ERROR%"=="1" GOTO END_ERROR
GOTO END



:: -------------------------------------------------------------------
:: Builds the project
:: -------------------------------------------------------------------
:BUILD
uv sync --upgrade
IF ERRORLEVEL 1 GOTO END_ERROR
ECHO.
uv run --no-sync invoke %_VERBOSE% %_TARGET%
IF ERRORLEVEL 1 GOTO END_ERROR
GOTO END



:: -------------------------------------------------------------------
:: Parse command line argument values
:: Note: Currently, last one on the command line wins (ex: rebuild clean == clean)
:: -------------------------------------------------------------------
:ARGS
IF "%PROCESSOR_ARCHITECTURE%"=="x86" (
    "C:\Windows\Sysnative\cmd.exe" /C "%0 %*"

    IF ERRORLEVEL 1 EXIT /B 1
    EXIT /B 0
)

:ARGS_PARSE
IF /I "%~1"=="analyze"              SET _TARGET=analyze& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="build"                SET _TARGET=build& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="clean"                SET _TARGET=clean& RMDIR /S /Q .venv 2>nul& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="compile"              SET _TARGET=compile& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="package"              SET _TARGET=package& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="rebuild"              SET _TARGET=rebuild& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="release"              SET _TARGET=release& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="test"                 SET _TARGET=test& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="test-live"            SET _TARGET=test-live& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="/log"                 SET _VERBOSE=verbose& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="/NoPause"             SET _NO_PAUSE=1& SHIFT & GOTO ARGS_PARSE
IF /I "%~1"=="/?"   GOTO SHOW_USAGE
IF    "%~1" EQU ""  GOTO ARGS_DONE
ECHO [31mUnknown command-line switch[0m %~1
GOTO ERROR_USAGE

:ARGS_DONE



:: -------------------------------------------------------------------
:: Set environment variables
:: -------------------------------------------------------------------
:SETENV
CALL .build\SetEnv.bat
IF ERRORLEVEL 1 GOTO END_ERROR
ECHO.
GOTO BUILD



:: -------------------------------------------------------------------
:: Errors
:: -------------------------------------------------------------------
:ERROR_EXT
ECHO [31mCould not activate command extensions[0m
GOTO END_ERROR

:ERROR_USAGE
SET _ERROR=1
GOTO SHOW_USAGE



:: -------------------------------------------------------------------
:: End
:: -------------------------------------------------------------------
:END_ERROR
SET _EXIT_CODE=1
ECHO.
ECHO [41m                                                                                [0m
ECHO [41;1mThe build failed                                                                [0m
ECHO [41m                                                                                [0m

:END
POPD
@IF NOT "%_NO_PAUSE%"=="1" PAUSE
:: %_EXIT_CODE% is expanded before ENDLOCAL discards it
ENDLOCAL & EXIT /B %_EXIT_CODE%
