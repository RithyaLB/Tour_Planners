@echo off
cd /d "D:\SEM-9\SOA Lab\Tour_Packages"
call Environment\Scripts\activate.bat
cd /d "D:\SEM-9\SOA Lab\Tour_Packages\Tour_Planners\tour_package"
python waitress_server.py
pause