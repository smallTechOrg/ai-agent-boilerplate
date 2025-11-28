# mock curls to test with
curl -X 'POST' \
  'http://127.0.0.1:5000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
   -H 'Origin: https://example.com' \
  -d '{
  "input": "Go back to russian please",
  "session_id": "0b3cf7e1-5b30-46df-b018-85ca4dbd4391",
  "request_type": "sales"
}'