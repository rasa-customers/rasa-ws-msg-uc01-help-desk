# Workshop Use Case 01 - IT Help Desk

```diff
@@ Cheatsheet @@

+ Train
rasa train
rasa train -c config.yml -d domain

+ Inspect
rasa inspect --debug
rasa inspect --debug --log-file logs.txt

+ Run
rasa run
rasa run actions --debug --auto-reload
rasa run --debug --log-file logs.txt --enable-api --cors "*"
rasa run --debug --log-file $(LOG_DIR)/logs_$(shell date +%Y%m%d%H%M%S).out --enable-api --cors "*"

+ Shell
rasa shell --debug

+ E2e
rasa test e2e tests/
```