FROM postgres:latest

ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=secure-password
ENV POSTGRES_DATABASE=pandas-study-db

EXPOSE 5432

VOLUME ["/var/lib/postgresql/data"]