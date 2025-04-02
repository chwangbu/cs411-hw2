#!/bin/bash

echo "Starting smoketest"

BASE_URL="http://localhost:5001/api"

echo "clearing boxers"
curl -s -X POST ${BASE_URL}/clear-boxers
echo "boxers cleaered"

echo "adding boxer A"
curl -s -X POST ${BASE_URL}/add-boxer -H "Content-Type: application/json" -d '{"name": "A", "weight": 150, "height": 74, "reach": 74.0, "age": 31}'
echo "added boxer A"

echo "trial boxer duplicate"
curl -s -o /dev/null -w "%{http_code}\n" -X POST ${BASE_URL}/add-boxer -H "Content-Type: application/json" -d '{"name": "A", "weight": 150, "height": 74, "reach": 74.0, "age": 31}'

echo "smoketest complete"
