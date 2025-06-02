python -m venv venv

#Windows
venv/Scripts/activate

#Linux
venv/bin/activate

pip install -r requirements.txt

*Abra o seu docker desktop*

Rode no terminal:
docker-compose up

Abra um outro terminal e rode o arquivo zodbController.py pra fazer CRUD no Zodb 
ou postgresController pra fazer no postgres.

