test:
	python3 manage.py test shop booking --settings=glow_by_riri.settings_test

run:
	python3 manage.py runserver

migrate:
	python3 manage.py migrate

migrations:
	python3 manage.py makemigrations

shell:
	python3 manage.py shell
