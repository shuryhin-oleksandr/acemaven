# Acemaven project.

#Run postgres with postgis extension and preset credentials:    
    sudo docker run --name=acemaven -d -e POSTGRES_USER=postgres -e POSTGRES_PASS=TesTpassword -e POSTGRES_DBNAME=acemaven -p 5434:5432 kartoza/postgis
    sudo apt install gdal-bin libgdal-dev python3-gdal binutils libproj-dev
#Run redis:
    sudo docker run --name my-redis-container -p 6379:6379 -d redis