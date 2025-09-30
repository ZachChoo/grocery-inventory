@echo off
echo Cleaning up test database...
docker-compose run --rm k6-cleanup

echo Restarting test API to recreate tables...
docker-compose restart test_api

echo Waiting for test API to be ready...
timeout /t 3 /nobreak > nul

echo Running k6 load tests...
docker-compose run --rm k6

echo Done!