@echo off
title Trinetra Frontend - SIH
cd /d "%~dp0"
echo =========================================================
echo       TRINETRA SIH FRONTEND (PORT 3000)
echo =========================================================
npx next dev --webpack
