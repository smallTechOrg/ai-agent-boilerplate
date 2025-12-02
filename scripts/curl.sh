# mock curls to test with
# chat - no message
curl -X 'POST' \
  'http://127.0.0.1:5000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
   -H 'Origin: https://example.com' \
  -d '{
  "input": "",
  "session_id": "0b3cf7e1-5b30-46df-b018-85ca4dbd4391",
  "request_type": "sales"
}'

# happy case scenario
curl -X 'POST' \
  'http://127.0.0.1:5000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
   -H 'Origin: https://example.com' \
  -d '{
  "input": "how are you",
  "session_id": "0b3cf7e1-5b30-46df-b018-85ca4dbd4391",
  "request_type": "sales"
}'

# internal server error / incorrect request tpe
curl -w "HTTP Code: %{http_code}\n" -X 'POST' \
  'http://127.0.0.1:5000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
   -H 'Origin: https://example.com' \
  -d '{
  "input": "how are you",
  "session_id": "0b3cf7e1-5b30-46df-b018-85ca4dbd4391",
  "request_type": "salesx"
}'


# incorrect address
curl -X 'POST' \
  'http://127.0.0.1:5000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
   -H 'Origin: https://examplex.com' \
  -d '{
  "input": "how are you",
  "session_id": "0b3cf7e1-5b30-46df-b018-85ca4dbd4391",
  "request_type": "sales"
}'

# history
curl -X 'GET' \
  'http://127.0.0.1:5000/history?session_id=4a4cf7e1-5b30-46df-b018-85ca4dbd4591' \
  -H 'accept: application/json' \
  -H 'Origin: https://example.com'

  curl -X 'GET' \
  'http://127.0.0.1:5000/history?session_id=4a4cf7e1-5b30-46df-b018-85ca4dbd459' \
  -H 'accept: application/json' \
  -H 'Origin: https://example.com'




  # chat info
  curl -X 'GET' \
  'http://127.0.0.1:5000/chat-info' \
  -H 'accept: application/json'


  curl -X 'PATCH' \
  'http://127.0.0.1:5000/chat-info' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "session_id": "0b3cf7e1-5b30-46df-b018-85ca4dbd4391",
  "status": "CLOSED"
}'



# happy chat info pathc

curl -X 'PATCH' \
  'http://127.0.0.1:5000/chat-info' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "session_id": "0b3cf7e1-5b30-46df-b018-85ca4dbd4391",
  "status": "CLOSED",
  "remarks": "no",
  "is_active": true
}'



curl -X 'PATCH' \
  'http://127.0.0.1:5000/chat-info' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "session_id": "0b3cf7e1-5b30-46df-b018-85ca4dbd4391",
  "status": "CLOSED",
  "remarks": "no",
  "is_active": "asda"
}'