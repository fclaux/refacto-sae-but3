FROM php:8.1-apache

RUN docker-php-ext-install pdo pdo_mysql mysqli
RUN a2enmod rewrite

RUN sed -i 's/80/8080/g' /etc/apache2/sites-available/000-default.conf /etc/apache2/ports.conf

COPY --chown=www-data:www-data . /var/www/html/

WORKDIR /var/www/html

USER www-data

EXPOSE 8080