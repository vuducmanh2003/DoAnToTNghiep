#!/bin/bash
for i in {1..1000}; do
  curl -s -X POST http://127.0.0.1:5024/check_url \
       -H "Content-Type: application/json" \
       -d '{"url":"https://lmsattt.ptit.edu.vn/"}' \
       | jq '.inference_time' >> inference_time_log.txt
done
