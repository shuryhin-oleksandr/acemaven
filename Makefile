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


.PHONY: wsgi
wsgi:
	gunicorn --config='gunicorn_wsgi.conf.py' config.wsgi:application


.PHONY: asgi
asgi:
	gunicorn --config='gunicorn_asgi.conf.py' config.asgi:application


.PHONY: venv
venv:
	source venv/bin/activate


.PHONY: celery
celery:
	celery  -A config worker --loglevel=info


.PHONY: celery_beat
celery_beat:
	celery  -A config beat -l INFO


