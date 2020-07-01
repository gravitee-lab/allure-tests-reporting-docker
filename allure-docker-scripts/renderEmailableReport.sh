#!/bin/bash
PROJECT_ID=$1

ENDPOINT="http://localhost:$PORT/allure-docker-service/emailable-report/render?project_id=$PROJECT_ID"
RETRY=7
DELAY=2
ENABLE_SECURITY_LOGIN=0

if [ -n "$SECURITY_USER" ] && [ -n "$SECURITY_PASS" ]; then
    BODY=$(curl -sb -X POST http://localhost:$PORT/login -H 'Content-Type: application/json' -d '{ "username": "'$SECURITY_USER'", "password": "'$SECURITY_PASS'"}')
    ACCESS_TOKEN=$(grep -o '"access_token":"[^"]*' <<< "$BODY" | grep -o '[^"]*$')
    ENABLE_SECURITY_LOGIN=1
fi

RETRY_COUNTER=1
while :
	do
        if [ "$ENABLE_SECURITY_LOGIN" == "1" ] ; then
            STATUS="$(curl -LI $ENDPOINT -H "Authorization: Bearer $ACCESS_TOKEN" -o /dev/null -w '%{http_code}\n' -s)"
        else
			STATUS="$(curl -LI $ENDPOINT -o /dev/null -w '%{http_code}\n' -s)"
        fi

		if [ "$STATUS" == "200" ]; then
			echo "Status: $STATUS"
			break;
		fi

		echo "Retrying call $ENDPOINT in $DELAY seconds"
		sleep $DELAY
		RETRY_COUNTER=$[$RETRY_COUNTER +1]
		if [ "$RETRY_COUNTER" == "$RETRY" ]; then
			echo "Timeout requesting $API_CALL after $RETRY attempts"
			break;
		fi
done
