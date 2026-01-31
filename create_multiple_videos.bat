@echo off
REM Batch script to create multiple rain sound videos for a YouTube channel
REM This creates a variety of rain videos with different intensities and durations

echo ===============================================
echo Rain Sound Video Batch Generator
echo ===============================================
echo.
echo This script will create multiple rain videos:
echo   - Light rain (8 hours)
echo   - Medium rain (10 hours)
echo   - Heavy rain (12 hours)
echo.
echo Total processing time: 3-6 hours
echo Total disk space needed: ~15-20 GB
echo.
pause

REM Create output directory
if not exist output_videos mkdir output_videos

echo.
echo ===============================================
echo Creating Test Video (1 minute)
echo ===============================================
python create_rain_video.py --test
move test_rain.mp4 output_videos\

echo.
echo ===============================================
echo Video 1/3: Light Rain (8 hours)
echo ===============================================
python create_rain_video.py --duration 8 --intensity light --output output_videos\light_rain_8hr.mp4

echo.
echo ===============================================
echo Video 2/3: Medium Rain (10 hours)
echo ===============================================
python create_rain_video.py --duration 10 --intensity medium --output output_videos\medium_rain_10hr.mp4

echo.
echo ===============================================
echo Video 3/3: Heavy Rain (12 hours)
echo ===============================================
python create_rain_video.py --duration 12 --intensity heavy --output output_videos\heavy_rain_12hr.mp4

echo.
echo ===============================================
echo COMPLETE!
echo ===============================================
echo.
echo Videos created in output_videos\ directory
dir output_videos\
echo.
echo Ready to upload to YouTube!
echo.
pause
