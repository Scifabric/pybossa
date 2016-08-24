source ./venv/bin/activate
python app_context_rqworker.py scheduled_jobs super high medium low -s > /dev/null 2>&1 # dump all output (stdout and stderr) to /dev/null
