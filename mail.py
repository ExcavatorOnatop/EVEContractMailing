import os, time, datetime, pytz
from esipy import EsiApp
from esipy import EsiClient
from esipy import EsiSecurity

app = EsiApp().get_latest_swagger

# Time delay: tells the macro how much time in the past to look for contracts in minutes
timeDelay = 5

# get your character ID from zkillboard.com, search for your name there and get a number
# for example, for Cheradenine Zakalve: https://zkillboard.com/character/2112352919/
# so number is 2112352919
characterID = 2118653796

# Name of your Bean Freight contract alt
contractAltName = "XXXXXXXX"

# replace the redirect_uri, client_id and secret_key values
# with the values you get from the STEP 1 !
security = EsiSecurity(
    redirect_uri='http://localhost:8000/sso/callback',
    client_id='XXXXXXXXXXXXX',
    secret_key='XXXXXXXXXXXXXX',
    headers={'User-Agent': 'Bean Freight Mail App'},
)

# and the client object, replace the header user agent value with something reliable !
client = EsiClient(
    retry_requests=True,
    headers={'User-Agent': 'Bean Freight Mail App'},
    security=security
)

# Check if token is saved
saveToken = False
accessToken = ''
refreshToken = ''
out = os.popen("cat .token")
lines = out.readlines()
if len(lines) == 0: # file does not exist
    saveToken = True
else:
    # Check the time
    currentTime = time.time()
    tokenTime = float(lines[0][:-1])
    accessToken = lines[1][:-1]
    refreshToken = lines[2]
    
    #if tokenTime + 1200 < currentTime:
    #    saveToken = True

if saveToken:
    # this print a URL where we can log in
    print(security.get_auth_uri(state='SomeRandomGeneratedState',
                                scopes=['esi-contracts.read_character_contracts.v1%20esi-mail.organize_mail.v1%20esi-ui.open_window.v1%20esi-universe.read_structures.v1']))
    code = input('Enter the code from the browser: ')
    tokens = security.auth(str(code))
    print(tokens)
    accessToken = tokens['access_token']
    refreshToken = tokens['refresh_token']

    file = open(".token", "w")
    file.write(str(time.time() + 1200) + '\n')
    file.write(accessToken + '\n')
    file.write(refreshToken)
    file.close()
else:
    print(refreshToken)
    security.update_token({
        'access_token': '',
        'expires_in': -1,
        'refresh_token': refreshToken
        })
    tokens = security.refresh()
    print(tokens)

# Auth info
api_info = security.verify()
getContracts = app.op['get_characters_character_id_contracts'](
    character_id = characterID,
    page = 1
    )
contracts = client.request(getContracts)
data1 = contracts.data
getContracts = app.op['get_characters_character_id_contracts'](
    character_id = characterID,
    page = 2
    )
contracts = client.request(getContracts)
data2 = contracts.data
data = data1
for elements in data2:
    data += [elements,]


counterContracts = 0
for item in data:
    #print("Test")
    #print(item)

    try:
        if item['type'] != "courier":
            continue
        if item['status'] != "finished":
            continue
        counterContracts +=1
    except:
        print("Unspecified error to be debugged later")
        break
        
    dateCompleted = str(item['date_completed'])
    eveZone = pytz.timezone('Iceland')
    
    contractFinishTime = datetime.datetime.strptime(dateCompleted[0:19], '%Y-%m-%dT%H:%M:%S')
    contractFinishTime = contractFinishTime.replace(tzinfo=eveZone)
    currentTime = datetime.datetime.now(eveZone)
    #print('\n\n',dateCompleted,'\t',contractFinishTime)

    if currentTime > contractFinishTime + datetime.timedelta(minutes=timeDelay):
        #print("Contract not considered", contractFinishTime, currentTime)
        continue
    #print("Found new contract", contractFinishTime, currentTime)


    
    #print("\n\nNew contract completed")
    #print(item)
    
    # For mail we need system's names
    # These are the ids of the station or a structure of the waypoints
    startLocationID = item['start_location_id']
    endLocationID = item['end_location_id']
    volume = item['volume']
    contractId = item['contract_id']
    
    startCategory = 'station'
    endCategory   = 'station'
    # structure IDs are very large
    if startLocationID > 1000000000000:
        startCategory = 'structure'
    if endLocationID   > 1000000000000:
        endCategory = 'structure'

    #print(startCategory + " >> " + endCategory)
    
    #Get the system ID from the location of the station or a structure
    startId = 0
    if startCategory == 'station':
        getNames = app.op['get_universe_stations_station_id'](
            station_id = startLocationID
            )
        output = client.request(getNames)
        startId = output.data['system_id']
    else:
        getNames = app.op['get_universe_structures_structure_id'](
            structure_id = startLocationID
        )
        output = client.request(getNames)
        startId = output.data['solar_system_id']

    endId = 0
    if endCategory == 'station':
        getNames = app.op['get_universe_stations_station_id'](
            station_id = endLocationID
        )
        output = client.request(getNames)
        endId = output.data['system_id']
    else:
        getNames = app.op['get_universe_structures_structure_id'](
            structure_id = endLocationID
        )
        output = client.request(getNames)
        endId = output.data['solar_system_id']

    #Get names of start and end systems:
    getNames = app.op['get_universe_systems_system_id'](
        system_id = startId
        )
    output = client.request(getNames)
    startName = output.data['name']

    getNames = app.op['get_universe_systems_system_id'](
        system_id = endId
        )
    output = client.request(getNames)
    endName = output.data['name']

    #print("Courier " + startName + " >> " + endName)
    
    #Get the name of the person from issuer id
    getNames = app.op['post_universe_names'](
        ids = [item['issuer_id'],]
        )
    nameOutput = client.request(getNames)
    clientName = nameOutput.data[0]['name']
    #print(clientName)

    bodyOfTheMail  = "Dear <a href=\"showinfo:1383//>" + clientName + "</a>!\n"
    bodyOfTheMail += "\nJust to let you know that your contract:\n\n"
    bodyOfTheMail += "<font size=\"14\" color=\"#bfffffff\"></font><font size=\"14\" color=\"#ffd98d00\">"
    bodyOfTheMail += "<a href=\"contract:" + str(startId) + "//" + str(contractId) + "\">" + startName + " &gt;&gt; "
    bodyOfTheMail += endName +" (" + str(volume) + " m3) "
    bodyOfTheMail += "(Courier)</a></font><font size=\"14\" color=\"#bfffffff\"> </font>"
    bodyOfTheMail += "\n\nhas been successfully delivered.\n\n"
    bodyOfTheMail += "If everything was handled beyond expectations, please spare a minute to write a review in this"
    bodyOfTheMail += "<font size=\"14\" color=\"#bfffffff\"> </font><font size=\"14\" color=\"#ffffe400\">"
    bodyOfTheMail += "<a href=\"https://www.pandemic-horde.org/forum/index.php?threads/bean-freight-horde-courier-service.3507/\">link.</a></font>\n\n"
    bodyOfTheMail += "\nThank you for choosing <font size=\"14\" color=\"#bfffffff\">"
    bodyOfTheMail += "</font><font size=\"14\" color=\"#ffd98d00\"><a href=\"showinfo:2//98710371\">"
    bodyOfTheMail += "Bean Freight</a></font><font size=\"14\" color=\"#bfffffff\"> </font>"
    bodyOfTheMail += "In turn, 30% of the money generated is used to help support various PHIL operations.\n\n"
    bodyOfTheMail += "With kindest regards,\n"
    bodyOfTheMail += "<a href=\showinfo:1383//" + str(item['acceptor_id']) + ">" + contractAltName + "</a>\n"
    bodyOfTheMail += "<font size=\"14\" color=\"#bfffffff\"></font><font size=\"14\" color=\"#ffd98d00\">"
    bodyOfTheMail += "<a href=\"showinfo:2//98710371\">Bean Freight</a></font><font size=\"14\" color=\"#bfffffff\"> </font>"
    print(bodyOfTheMail)

    openMail = app.op['post_ui_openwindow_newmail'](
        new_mail={"body": bodyOfTheMail,
                  "recipients": [item['issuer_id'],],
                  "subject": "Bean Freight Contract: delivered!",
                  "to_corp_or_alliance_id": 0,
                  "to_mailing_list_id": 0},
    )
    client.request(openMail)
    
print(counterContracts, len(data))    
