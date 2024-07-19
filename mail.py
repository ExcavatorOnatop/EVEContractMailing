""" Send mails to the contract issuer when a courier contract is completed."""
import datetime
import time

import pytz
from esipy import EsiApp, EsiClient, EsiSecurity

def main():
    """ Run the main body of the mailer """
    app = EsiApp().get_latest_swagger

    # Time delay: tells the macro how much time in the past to look for contracts in minutes
    time_delay = 5

    # get your character ID from zkillboard.com, search for your name there and get a number
    # for example, for Cheradenine Zakalve: https://zkillboard.com/character/2112352919/
    # so number is 2112352919
    character_id = 2118653796

    # Name of your Bean Freight contract alt
    contract_alt_name = "XXXXXXXX"

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
    save_token = False
    access_token = ''
    refresh_token = ''
    lines = []
    try:
        with open(".token", "r", encoding="utf-8") as out:
            lines = out.readlines()
    except FileNotFoundError:
        pass
    if len(lines) == 0: # file does not exist
        save_token = True
    else:
        # Check the time
        current_time = time.time()
        access_token = lines[1][:-1]
        refresh_token = lines[2]

    if save_token:
        # this prints a URL where we can log in
        print(security.get_auth_uri(state='SomeRandomGeneratedState',
                                    scopes=[('esi-contracts.read_character_contracts.v1'
                                             '%20esi-mail.organize_mail.v1'
                                             '%20esi-ui.open_window.v1'
                                             '%20esi-universe.read_structures.v1')]))
        code = input('Enter the code from the browser: ')
        tokens = security.auth(str(code))
        print(tokens)
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']

        with open(".token", "w", encoding="utf-8") as file:
            file.write(str(time.time() + 1200) + '\n')
            file.write(access_token + '\n')
            file.write(refresh_token)
            file.close()
    else:
        print(refresh_token)
        security.update_token({
            'access_token': '',
            'expires_in': -1,
            'refresh_token': refresh_token
            })
        tokens = security.refresh()
        print(tokens)

    # Auth info
    security.verify()
    get_contracts = app.op['get_characters_character_id_contracts'](
        character_id = character_id,
        page = 1
        )
    contracts = client.request(get_contracts)
    data1 = contracts.data
    get_contracts = app.op['get_characters_character_id_contracts'](
        character_id = character_id,
        page = 2
        )
    contracts = client.request(get_contracts)
    data2 = contracts.data
    data = data1
    for elements in data2:
        data += [elements,]


    contracts_count = 0
    for item in data:
        #print("Test")
        #print(item)

        try:
            if item['type'] != "courier":
                continue
            if item['status'] != "finished":
                continue
            contracts_count +=1
        except Exception:
            print("Unspecified error to be debugged later")
            break

        date_completed = str(item['date_completed'])
        eve_zone = pytz.timezone('Iceland')

        contract_finish_time = datetime.datetime.strptime(date_completed[0:19], '%Y-%m-%dT%H:%M:%S')
        contract_finish_time = contract_finish_time.replace(tzinfo=eve_zone)
        current_time = datetime.datetime.now(eve_zone)

        if current_time > contract_finish_time + datetime.timedelta(minutes=time_delay):
            continue

        # For mail we need system's names
        # These are the ids of the station or a structure of the waypoints
        start_location_id = item['start_location_id']
        end_location_id = item['end_location_id']
        volume = item['volume']
        contract_id = item['contract_id']

        start_category = 'station'
        end_category   = 'station'
        # structure IDs are very large
        if start_location_id > 1000000000000:
            start_category = 'structure'
        if end_location_id   > 1000000000000:
            end_category = 'structure'

        #Get the system ID from the location of the station or a structure
        start_id = 0
        if start_category == 'station':
            get_names = app.op['get_universe_stations_station_id'](
                station_id = start_location_id
                )
            output = client.request(get_names)
            start_id = output.data['system_id']
        else:
            get_names = app.op['get_universe_structures_structure_id'](
                structure_id = start_location_id
            )
            output = client.request(get_names)
            start_id = output.data['solar_system_id']

        end_id = 0
        if end_category == 'station':
            get_names = app.op['get_universe_stations_station_id'](
                station_id = end_location_id
            )
            output = client.request(get_names)
            end_id = output.data['system_id']
        else:
            get_names = app.op['get_universe_structures_structure_id'](
                structure_id = end_location_id
            )
            output = client.request(get_names)
            end_id = output.data['solar_system_id']

        #Get names of start and end systems:
        get_names = app.op['get_universe_systems_system_id'](
            system_id = start_id
            )
        output = client.request(get_names)
        start_name = output.data['name']

        get_names = app.op['get_universe_systems_system_id'](
            system_id = end_id
            )
        output = client.request(get_names)
        end_name = output.data['name']

        #print("Courier " + start_name + " >> " + end_name)

        #Get the name of the person from issuer id
        get_names = app.op['post_universe_names'](
            ids = [item['issuer_id'],]
            )
        name_output = client.request(get_names)
        client_name = name_output.data[0]['name']
        #print(client_name)

        mail_body  = "Dear <a href=\"showinfo:1383//>" + client_name + "</a>!\n"
        mail_body += "\nJust to let you know that your contract:\n\n"
        mail_body += "<font size=\"14\" color=\"#bfffffff\"></font><font size=\"14\" color=\"#ffd98d00\">"
        mail_body += "<a href=\"contract:" + str(start_id) + "//" + str(contract_id) + "\">" + start_name + " &gt;&gt; "
        mail_body += end_name +" (" + str(volume) + " m3) "
        mail_body += "(Courier)</a></font><font size=\"14\" color=\"#bfffffff\"> </font>"
        mail_body += "\n\nhas been successfully delivered.\n\n"
        mail_body += "If everything was handled beyond expectations, please spare a minute to write a review in this"
        mail_body += "<font size=\"14\" color=\"#bfffffff\"> </font><font size=\"14\" color=\"#ffffe400\">"
        mail_body += "<a href=\"https://www.pandemic-horde.org/forum/index.php?threads/bean-freight-horde-courier-service.3507/\">link.</a></font>\n\n"
        mail_body += "\nThank you for choosing <font size=\"14\" color=\"#bfffffff\">"
        mail_body += "</font><font size=\"14\" color=\"#ffd98d00\"><a href=\"showinfo:2//98710371\">"
        mail_body += "Bean Freight</a></font><font size=\"14\" color=\"#bfffffff\"> </font>"
        mail_body += "In turn, 30% of the money generated is used to help support various PHIL operations.\n\n"
        mail_body += "With kindest regards,\n"
        mail_body += "<a href=\"showinfo:1383//" + str(item['acceptor_id']) + ">" + contract_alt_name + "</a>\n"
        mail_body += "<font size=\"14\" color=\"#bfffffff\"></font><font size=\"14\" color=\"#ffd98d00\">"
        mail_body += "<a href=\"showinfo:2//98710371\">Bean Freight</a></font><font size=\"14\" color=\"#bfffffff\"> </font>"
        print(mail_body)

        open_mail = app.op['post_ui_openwindow_newmail'](
            new_mail={"body": mail_body,
                    "recipients": [item['issuer_id'],],
                    "subject": "Bean Freight Contract: delivered!",
                    "to_corp_or_alliance_id": 0,
                    "to_mailing_list_id": 0},
        )
        client.request(open_mail)

    print(contracts_count, len(data))

if __name__ == "__main__":
    main()
