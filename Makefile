.PHONY: data baseline train evaluate app web desktop desktop-exe test
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
desktop:
	python -m src.desktop
desktop-exe:
	python -m src.desktop.build
test:
	python -m pytest -q
