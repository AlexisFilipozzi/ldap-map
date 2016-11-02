LDAP-map
========

Installation
------------

```
apt-get install python3-pip
apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev
apt-get install libyaml-dev
```

On utilise Python3.

On peut également avoir besoin de l'utilitaire mail en CLI, on installe donc :
```
apt-get install mailutils
```

On installe les dépendances Python :
```
pip3 install -r requirements.txt
```

Utilisation de virtualenv
-------------------------
```
virtualenv -p python3 env
source env/bin/activate
```

Test
----
On peut vérifier les types statiques avec :
```
mypy Classes generate_map.py
```