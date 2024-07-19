# EVEContractMailing
A simple macro to create mails to customers after fulfilling the courier contract. Works with python3.9, for some reason EsiPy package did not work with the recent python.

## Instructions:

Download the code
```
git clone https://github.com/Kyria/flask-esipy-example.git
git clone https://github.com/ExcavatorOnatop/EVEContractMailing.git
```

Open mail.py with your favorite editor and replace XXXs with your information:
- characterID can be found by searching for your Bean Freight Alt in zkillboard. For example, a search for Cheradenine Zakalve results in a URL https://zkillboard.com/character/2112352919/, so the characterID for Cheradenine Zakalve is 2112352919
- contractAltName is the in-game name of your Bean Freight contract Alt

Register your code with EVE Online

Go to https://developers.eveonline.com/ and create a new application giving it the following scopes:
- esi-contracts.read_character_contracts.v1
- esi-mail.organize_mail.v1
- esi-ui.open_window.v1
- esi-universe.read_structures.v1

Copy and paste the application's client_id and secret_key in mail.py macro (lines 22 and 23)

## First execution
When you run the macro for the first time the code will create a token with the authorization information. First it will provide you with the URL link:
```
https://login.eveonline.com/v2/oauth/authorize?response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fsso%2Fcallback&client_id=XXXXXXXXXXXXX&scope=esi-contracts.read_character_contracts.v1%20esi-mail.organize_mail.v1%20esi-ui.open_window.v1%20esi-universe.read_structures.v1&state=SomeRandomGeneratedState
```
(XXXXs will be replaced with the client_id that you modified in the mail.py code). Enter the URL string in the browser of your choice and log into the Bean Freight contract alt. Once this is done, the URL in the browser will look like this:
```
http://localhost:8000/sso/callback?code=XXXXXXXX&state=SomeRandomGeneratedState
```
where XXXX will be the code provided to you by EVE Online, copy the code only and enter it at prompt. Once this is done your token (in .token file) will be created and you no longer need to authorize the macro to open mails on the client.

# Notes
- The macro does not keep track which mails are created. The information from all the successfully completed courier contracts within the specified timeframe (controlled by timeDelay variable in mail.py) will be used.
- Please check the mail before sending it, to make sure all is correct.
- You cannot send more than 5 mails per minute, unfortunately




