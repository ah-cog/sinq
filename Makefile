.PHONY: init up down logs status test ios android
init:
	git submodule update --init --recursive
up:
	docker compose up --build -d --wait
down:
	docker compose down
logs:
	docker compose logs -f
status:
	docker compose ps
test:
	docker compose exec server python manage.py test
	cd sinq-ios && npm ci && npx playwright install chromium && npm test
ios:
	python3 scripts/dev.py ios
android:
	python3 scripts/dev.py android
