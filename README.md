**Automatizacion de exportacion de imagenes de Google Earth Engine.**

Script que genera SCI y CCI de la última imágen disponible en el catálogo de GEE.

SCI: Snow Cover Index
CCI: Cloud Cover Index


To automate you need to sign-in using a service account
1. Create or Select a Google Cloud Project
2. Enable the project for 'Earth Engine API'
3. Create a service Account
    3.1 Grant role: Earth Engine Resource Writer (Avoiding Manage role to limit risk)
4. Create keys for service account (json file). Store this file securely
5. Activate the service account for GEE here (https://signup.earthengine.google.com/#!/service_accounts)
6. test sign in from python.