curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What do you know about Supplier: Alpha Suppliers Inc. and ABC Stationery Supplies; what they supplies?"}'

curl -X POST localhost:11434/api/generate -d '{"model": "gemma3:4b", "prompt": "Why is the sky blue tell me in 2 sentence?", "stream": false }'