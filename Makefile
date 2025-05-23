.PHONY: be_serve ui_serve

be_serve:
	uvicorn src.services.contract_app:app --reload

ui_serve:
	streamlit run src/ui/chat_app.py