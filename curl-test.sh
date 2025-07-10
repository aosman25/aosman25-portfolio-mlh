#!/usr/bin/env bash

BASE_URL=http://127.0.0.1:5000
RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
RESET="\e[0m"

get_length() {
	curl -s "$BASE_URL/api/timeline_post"  | jq '.["timeline_posts"] | length'
}

get_post_id() {
	curl -s "$BASE_URL/api/timeline_post" | jq '.["timeline_posts"][0]["id"]'
}

OLD_LENGTH=$(get_length)

# POST Test Request
curl -H "Content-type: multipart/form-data" -F name=TEST -F email=TEST@TEST.COM -F content=TEST -X POST -s "$BASE_URL/api/timeline_post" > /dev/null

POST_LENGTH=$(get_length)

if [ $POST_LENGTH -eq $(($OLD_LENGTH + 1))  ]; then
	echo -e "${GREEN}Successfully Posted Test Request${RESET}"
else 
	echo -e "${RED}Failed to Post Test Request${RESET}"
	echo -e "${YELLOW}Expected length: $(($OLD_LENGTH + 1)), got: $POST_LENGTH${RESET}"
	exit 1
fi

POST_ID=$(get_post_id)

# Clean Up Database
curl -X DELETE -s "$BASE_URL/api/timeline_post/$POST_ID" > /dev/null

DELETE_LENGTH=$(get_length)
if [ $OLD_LENGTH -eq $DELETE_LENGTH  ]; then
	echo -e "${GREEN}Successfully Cleaned Up Database${RESET}"
	exit 0
else 
	echo -e "${RED}Failed to Clean Up Database${RESET}"
	echo -e "${YELLOW}Expected length: $OLD_LENGTH, got: $DELETE_LENGTH${RESET}"
	exit 1
fi
