Development
-----------

If you want to setup a development environment, you are in need of `pipenv <https://docs.pipenv.org/>`__.

.. code:: shell

   git clone https://gitlab.com/coroner/cryptolyzer
   cd cryptolyzer
   pipenv install --dev
   pipenv run python setup.py develop
   pipenv shell
   cryptolyze -h


cryptolyze ssh2 ciphers 10.223.40.7
cryptolyze tls all 10.223.40.7


cryptolyze ssh2 ciphers 192.168.1.4
cryptolyze tls all 192.168.1.4