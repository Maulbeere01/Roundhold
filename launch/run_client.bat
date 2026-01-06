@echo off
if "%TD_SERVER_ADDR%"=="" set TD_SERVER_ADDR=localhost:42069
python -m client.src.td_client.main
