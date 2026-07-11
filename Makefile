.PHONY: qa smoke

qa:
	python -m compileall -q src tests
	python -m unittest discover -s tests -v

smoke:
	PYTHONPATH=src python -m zdc_hybrid.smoke
