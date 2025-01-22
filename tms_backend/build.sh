set -o errecit

pip install -r requirements.txt

python manage.py collectstatic
python manage.oy migrate

if [[$CREATE_SUPERUSER]];
then 
    python manage.py createsuperuser --no-input --email "$DJANGO_SUPERUSER_EMAIL"
fi