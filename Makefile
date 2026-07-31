install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run:
	streamlit run streamlit_app.py

api:
	uvicorn backend.main:app --reload

test:
	pytest -q

migrate:
	alembic upgrade head

docker:
	docker compose up --build
