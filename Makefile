.PHONY: data baseline train evaluate app web test
data:
	python -m src.data.download
	python -m src.data.clean
baseline:
	python -m src.data.baseline
train:
	python -m src.models.train
evaluate:
	python -m src.models.evaluate
app:
	streamlit run src/app/app.py
web:
	python -m src.app.server
test:
	python -m pytest -q
