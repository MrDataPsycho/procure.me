.PHONY: be_serve ui_serve embed_openai embed_ollama silver_to_gold silver_to_gold_test

be_serve:
	uvicorn src.services.contract_app:app --reload

ui_serve:
	streamlit run src/ui/chat_app.py

silver_to_gold_test:
	python src/etl/metadata_extraction_gold.py -s data/silver/contracts -d data/gold/metadata --limit 1

silver_to_gold_test:
	python src/etl/metadata_extraction_gold.py -s data/silver/contracts -d data/gold/metadata