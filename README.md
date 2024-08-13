# vector


This is a repository for the vector project. The vector project is a web application that allows users to search for CVEs and view information about them.

Currently, the CVE Vector data is stored in postgresDB with the PGVector plugin enabled

## Setup

### Install dependencies

```
pip install -r requirements.txt
```

### Setup The Postgres Database
```
version: '3.8'

services:
  psql:
    image: pgvector/pgvector:0.7.4-pg14
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - 5432:5432

volumes:
  psql_volume:
```

### Run the DB Migrations using flyway
```
flyway migrate
```

The migrations are located in the `migrations` directory inside the following repo: 
https://github.com/csye7125-su24-team7/webapp-cve-consumer


Create a .env file in the root of the project and add the following:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cve
DB_USER=username
DB_PASSWORD=password
```