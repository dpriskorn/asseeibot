# Usage: chmod +x this script and run like this "./create_kubernettes_article_job_and_watch_the_log.sh 1"
# Increment the job number yourself each time
toolforge-jobs run job$1 --image tf-python39 --command "pip install -r ~/asseeibot/requirements.txt && python3 ~/asseeibot/asseeibot/main.py"
watch tail ~/job$1*
