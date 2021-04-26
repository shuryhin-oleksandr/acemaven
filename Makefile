.PHONY: migrate
migrate:
	python manage.py migrate


.PHONY: migrations
migrations:
	python manage.py makemigrations


.PHONY: static
static:
	python manage.py collectstatic --noinput


.PHONY: translations
translations:
	python manage.py makemessages -l 'es'
	python manage.py makemessages -l 'pt'


.PHONY: translate
translate:
	python manage.py compilemessages


.PHONY: run
run:
	python manage.py runserver


.PHONY: superuser
superuser:
	python manage.py createsuperuser
