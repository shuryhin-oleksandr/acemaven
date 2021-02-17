# Acemaven project.

# Python 
    version 3.8

# Run postgres with postgis extension and preset credentials:    
    sudo docker run --name=acemaven -d -e POSTGRES_USER=[user] -e POSTGRES_PASS=[password] -e POSTGRES_DBNAME=acemaven -p 5434:5432 kartoza/postgis
    sudo apt install gdal-bin libgdal-dev python3-gdal binutils libproj-dev
# Run redis:
    sudo docker run --name my-redis-container -p 6379:6379 -d redis
    
# Run celery:
    celery  -A config worker --loglevel=info
    celery  -A config beat -l INFO

# Apply fixtures:
    python manage.py loaddata fixtures/*.json
    
# System platform settings:
    Choose country and make it main for platform. Choose main and addtitional currencies. Add exchange rates. 
    Config the client platform and general settings.
    Config air and sea tracking api details.
    