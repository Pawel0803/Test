# ---------------------------------------------
# NatNet Python Client 4.3 – wyjaśnienie linia po linii
# Każdą istotną linię opatrzyłem komentarzem po polsku.
# ---------------------------------------------

import sys                      # standardowy moduł Pythona: dostęp do argumentów, wyjścia itp.
import time                     # moduł do operacji czasowych (sleep, pomiar czasu)
from NatNetClient import NatNetClient  # import klasy klienta NatNet (API OptiTrack/Motive)
import DataDescriptions         # moduł pomocniczy do testów struktur opisów modeli
import MoCapData                # moduł pomocniczy do testów struktur danych ruchu (mocap)

# To jest funkcja zwrotna (callback), przypinana do klienta NatNet.
# Wywoływana raz na klatkę rejestrowaną przez system mocap.

def receive_new_frame(data_dict):
    order_list = [
        "frameNumber", "markerSetCount", "unlabeledMarkersCount",  # typy kluczy, w jakiej kolejności chcemy wypisywać
        "rigidBodyCount", "skeletonCount", "labeledMarkerCount",
        "timecode", "timecodeSub", "timestamp", "isRecording",
        "trackedModelsChanged"
    ]
    dump_args = False           # flaga: czy wypisywać całą zawartość data_dict
    if dump_args is True:      # jeśli True, to zbuduj string z parametrami i go wydrukuj
        out_string = "    "
        for key in data_dict:  # iteruj po wszystkich kluczach w słowniku z danymi ramki
            out_string += key + "= "
            if key in data_dict:
                out_string += data_dict[key] + " "   # UWAGA: wymagałoby str(), ale ten blok i tak domyślnie się nie wykona
            out_string += "/"
        print(out_string)      # wydrukuj zebrane informacje o ramce


def receive_new_frame_with_data(data_dict):
    # Druga wersja callbacku – uwzględnia dodatkowe pola „offset” i „mocap_data”
    order_list = [
        "frameNumber", "markerSetCount", "unlabeledMarkersCount",
        "rigidBodyCount", "skeletonCount", "labeledMarkerCount",
        "timecode", "timecodeSub", "timestamp", "isRecording",
        "trackedModelsChanged", "offset", "mocap_data"
    ]
    dump_args = True            # tutaj domyślnie wypisujemy zawartość, dla debugowania
    if dump_args is True:
        out_string = "    "
        for key in data_dict:
            out_string += key + "= "
            if key in data_dict:
                out_string += str(data_dict[key]) + " "  # str() – bezpieczne rzutowanie do tekstu
            out_string += "/"
        print(out_string)


# Callback wywoływany raz na każdy sztywny obiekt (Rigid Body) w danej klatce
# Zawiera jego id, pozycję i orientację.

def receive_rigid_body_frame(new_id, position, rotation):
    pass                        # aktualnie nic nie robi (placeholder)
    # przykładowe debug printy pozostawione w komentarzu:
    # print("Received frame for rigid body", new_id)
    # print("Received frame for rigid body", new_id, " ", position, " ", rotation)


# Prosta funkcja pomocnicza: dodaje elementy listy totals_tmp do totals (suma wyników testów)

def add_lists(totals, totals_tmp):
    totals[0] += totals_tmp[0]
    totals[1] += totals_tmp[1]
    totals[2] += totals_tmp[2]
    return totals


# Wypisanie aktualnej konfiguracji połączenia/serwera NatNet

def print_configuration(natnet_client):
    natnet_client.refresh_configuration()  # pobierz świeżą konfigurację z serwera
    print("Connection Configuration:")
    print("  Client:          %s" % natnet_client.local_ip_address)
    print("  Server:          %s" % natnet_client.server_ip_address)
    print("  Command Port:    %d" % natnet_client.command_port)
    print("  Data Port:       %d" % natnet_client.data_port)

    changeBitstreamString = "  Can Change Bitstream Version = "  # informacja pomocnicza
    if natnet_client.use_multicast:
        print("  Using Multicast")
        print("  Multicast Group: %s" % natnet_client.multicast_address)
        changeBitstreamString += "false"  # przy multicast nie można zmienić wersji bitstreamu
    else:
        print("  Using Unicast")
        changeBitstreamString += "true"   # przy unicast można

    # Informacje o serwerze NatNet / Motive
    application_name = natnet_client.get_application_name()
    nat_net_requested_version = natnet_client.get_nat_net_requested_version()
    nat_net_version_server = natnet_client.get_nat_net_version_server()
    server_version = natnet_client.get_server_version()

    print("  NatNet Server Info")
    print("    Application Name %s" % (application_name))
    print("    MotiveVersion  %d %d %d %d" % (server_version[0], server_version[1], server_version[2], server_version[3]))
    print("    NatNetVersion  %d %d %d %d" % (nat_net_version_server[0], nat_net_version_server[1], nat_net_version_server[2], nat_net_version_server[3]))
    print("  NatNet Bitstream Requested")
    print("    NatNetVersion  %d %d %d %d" % (
        nat_net_requested_version[0], nat_net_requested_version[1],
        nat_net_requested_version[2], nat_net_requested_version[3]
    ))

    print(changeBitstreamString)  # podsumowanie czy można zmieniać wersję strumienia
    # print("command_socket = %s" % (str(natnet_client.command_socket)))  # pomocnicze debugi
    # print("data_socket    = %s" % (str(natnet_client.data_socket)))
    print("  PythonVersion    %s" % (sys.version))


# Wypis listy poleceń obsługiwanych przez pętlę wejścia w main()

def print_commands(can_change_bitstream):
    outstring = "Commands:\n"
    outstring += "Return Data from Motive\n"
    outstring += "  s  send data descriptions\n"  # poproś o opisy modeli (rigid bodies, markery, itp.)
    outstring += "  r  resume/start frame playback\n"  # wystartuj odtwarzanie klatek (timeline)
    outstring += "  p  pause frame playback\n"      # pauza timeline
    outstring += "     pause may require several seconds\n"
    outstring += "     depending on the frame data size\n"
    outstring += "Change Working Range\n"
    outstring += "  o  reset Working Range to: start/current/end frame 0/0/end of take\n"
    outstring += "  w  set Working Range to: start/current/end frame 1/100/1500\n"
    outstring += "Return Data Display Modes\n"
    outstring += "  j  print_level = 0 supress data description and mocap frame data\n"
    outstring += "  k  print_level = 1 show data description and mocap frame data\n"
    outstring += "  l  print_level = 20 show data description and every 20th mocap frame data\n"
    outstring += "Change NatNet data stream version (Unicast only)\n"
    outstring += "  3  Request NatNet 3.1 data stream (Unicast only)\n"
    outstring += "  4  Request NatNet 4.1 data stream (Unicast only)\n"  # uwaga: faktycznie poniżej ustawiane jest 4.2
    outstring += "General\n"
    outstring += "  t  data structures self test (no motive/server interaction)\n"
    outstring += "  c  print configuration\n"
    outstring += "  h  print commands\n"
    outstring += "  q  quit\n\n"
    outstring += "NOTE: Motive frame playback will respond differently in\n"
    outstring += "       Endpoint, Loop, and Bounce playback modes.\n\n"
    outstring += "EXAMPLE: PacketClient [serverIP [ clientIP [ Multicast/Unicast]]]\n"
    outstring += "         PacketClient \"192.168.10.14\" \"192.168.10.14\" Multicast\n"
    outstring += "         PacketClient \"127.0.0.1\" \"127.0.0.1\" u\n\n"
    print(outstring)             # ostateczny wydruk menu poleceń


# Wysyła żądanie opisów modeli (model definitions) do serwera NatNet

def request_data_descriptions(s_client):
    s_client.send_request(              # używa gniazda komend klienta
        s_client.command_socket,
        s_client.NAT_REQUEST_MODELDEF,  # kod żądania: „podaj opisy modeli”
        "",
        (s_client.server_ip_address, s_client.command_port)  # adres serwera komend
    )


# Uruchamia testy klas pomocniczych i podsumowuje wyniki

def test_classes():
    totals = [0, 0, 0]                 # [PASS, FAIL, SKIP]
    print("Test Data Description Classes")
    totals_tmp = DataDescriptions.test_all()  # uruchom testy opisów modeli
    totals = add_lists(totals, totals_tmp)
    print("")
    print("Test MoCap Frame Classes")
    totals_tmp = MoCapData.test_all()  # uruchom testy struktur danych klatek
    totals = add_lists(totals, totals_tmp)
    print("")
    print("All Tests totals")
    print("--------------------")
    print("[PASS] Count = %3.1d" % totals[0])
    print("[FAIL] Count = %3.1d" % totals[1])
    print("[SKIP] Count = %3.1d" % totals[2])


# Prosty parser argumentów wiersza poleceń: ustawia adresy i tryby

def my_parse_args(arg_list, args_dict):
    # ustaw wartości bazowe w args_dict już podane z zewnątrz
    arg_list_len = len(arg_list)
    if arg_list_len > 1:
        args_dict["serverAddress"] = arg_list[1]  # 1-szy argument: IP serwera
        if arg_list_len > 2:
            args_dict["clientAddress"] = arg_list[2]  # 2-gi argument: IP klienta (lokalnego interfejsu)
        if arg_list_len > 3:
            if len(arg_list[3]):         # 3-ci argument decyduje o multicast/unicast
                args_dict["use_multicast"] = True
                if arg_list[3][0].upper() == "U":  # jeśli zaczyna się od 'U' -> Unicast
                    args_dict["use_multicast"] = False
        if arg_list_len > 4:
            args_dict["stream_type"] = arg_list[4]  # 4-ty argument: typ strumienia ('d' lub 'c')
    return args_dict


# Główny blok wykonywany przy uruchomieniu pliku jako skrypt

if __name__ == "__main__":

    optionsDict = {}
    optionsDict["clientAddress"] = "127.0.0.1"  # domyślne IP klienta
    optionsDict["serverAddress"] = "127.0.0.1"  # domyślne IP serwera
    optionsDict["use_multicast"] = None         # tryb transmisji nieustawiony (zapytamy użytkownika)
    optionsDict["stream_type"] = None           # typ strumienia (data/command) nieustawiony (zapytamy)
    stream_type_arg = None                       # niewykorzystywana zmienna (pozostałość)

    # Tworzymy klienta NatNet i wczytujemy opcjonalne argumenty z linii poleceń
    optionsDict = my_parse_args(sys.argv, optionsDict)
    streaming_client = NatNetClient()            # instancja klienta NatNet
    streaming_client.set_client_address(optionsDict["clientAddress"])  # ustaw IP klienta
    streaming_client.set_server_address(optionsDict["serverAddress"])  # ustaw IP serwera

    # Konfiguracja callbacków odbierających dane
    streaming_client.new_frame_listener = receive_new_frame           # wywołuj dla każdej klatki
    # streaming_client.new_frame_with_data_listener = receive_new_frame_with_data  # alternatywny callback (zakomentowany)
    streaming_client.rigid_body_listener = receive_rigid_body_frame   # wywołuj dla każdego Rigid Body

    # Drukujemy nagłówek programu
    print("NatNet Python Client 4.3\n")

    # Pytamy użytkownika o tryb transmisji: multicast (0) czy unicast (1)
    cast_choice = input("Select 0 for multicast and 1 for unicast: ")
    cast_choice = int(cast_choice)
    while cast_choice != 0 and cast_choice != 1:  # dopóki nie poda 0 lub 1, pytaj dalej
        cast_choice = input("Invalid option. Select 0 for multicast or 1 for unicast: ")
        cast_choice = int(cast_choice)
    # ustaw tryb w opcjach i w kliencie
    if cast_choice == 0:
        optionsDict["use_multicast"] = True
    else:
        optionsDict["use_multicast"] = False
    streaming_client.set_use_multicast(optionsDict["use_multicast"])  # przekaż do klienta

    # Pozwalaj użytkownikowi nadpisać lokalny adres IP (enter = zachowaj domyślny)
    client_addr_choice = input("Client Address (127.0.0.1): ")
    if client_addr_choice != "":
        streaming_client.set_client_address(client_addr_choice)

    # Pozwalaj nadpisać adres IP serwera
    server_addr_choice = input("Server Address (127.0.0.1): ")
    if server_addr_choice != "":
        streaming_client.set_server_address(server_addr_choice)

    # Pytanie o typ strumienia: dane (d) czy komendy (c)
    stream_choice = None
    while stream_choice != 'd' and stream_choice != 'c':
        stream_choice = input("Select d for datastream and c for command stream: ")
    optionsDict["stream_type"] = stream_choice

    # Start klienta (oddzielny wątek), zwróci True jeśli się udało
    is_running = streaming_client.run(optionsDict["stream_type"])
    if not is_running:
        print("ERROR: Could not start streaming client.")
        try:
            sys.exit(1)          # wyjdź z kodem 1
        except SystemExit:
            print("...")        # przechwycony wyjątek wyjścia – dopisz wielokropek
        finally:
            print("exiting")    # komunikat końcowy

    is_looping = True            # flaga pętli komend użytkownika
    time.sleep(1)                # daj chwilę na ustanowienie połączenia
    if streaming_client.connected() is False:  # sprawdź czy połączony z Motive
        print("ERROR: Could not connect properly.  Check that Motive streaming is on.")
        try:
            sys.exit(2)          # wyjdź z kodem 2
        except SystemExit:
            print("...")
        finally:
            print("exiting")

    print_configuration(streaming_client)  # pokaż konfigurację połączenia
    print("\n")
    print_commands(streaming_client.can_change_bitstream_version())  # pokaż menu (zależne od trybu)

    # Główna pętla obsługi poleceń od użytkownika
    while is_looping:
        inchars = input("Enter command or ('h' for list of commands)\n")  # pobierz polecenie
        if len(inchars) > 0:
            c1 = inchars[0].lower()  # bierz pierwszy znak i zamień na małą literę
            if c1 == 'h':
                print_commands(streaming_client.can_change_bitstream_version())  # wydrukuj help
            elif c1 == 'c':
                print_configuration(streaming_client)  # pokaż konfigurację
            elif c1 == 's':
                request_data_descriptions(streaming_client)  # zażądaj opisów modeli
                time.sleep(1)                               # krótka pauza
            elif (c1 == '3') or (c1 == '4'):
                # próba przełączenia wersji strumienia NatNet (tylko Unicast)
                if streaming_client.can_change_bitstream_version():
                    tmp_major = 4
                    tmp_minor = 2
                    if (c1 == '3'):
                        tmp_major = 3
                        tmp_minor = 1
                    return_code = streaming_client.set_nat_net_version(tmp_major, tmp_minor)
                    time.sleep(1)
                    if return_code == -1:
                        print("Could not change bitstream version to %d.%d" % (tmp_major, tmp_minor))
                    else:
                        print("Bitstream version at %d.%d" % (tmp_major, tmp_minor))
                else:
                    print("Can only change bitstream in Unicast Mode")

            elif c1 == 'p':
                sz_command = "TimelineStop"                     # zatrzymaj oś czasu w Motive
                return_code = streaming_client.send_command(sz_command)
                time.sleep(1)
                print("Command: %s - return_code: %d" % (sz_command, return_code))
            elif c1 == 'r':
                sz_command = "TimelinePlay"                     # uruchom odtwarzanie osi czasu
                return_code = streaming_client.send_command(sz_command)
                print("Command: %s - return_code: %d" % (sz_command, return_code))
            elif c1 == 'o':
                # Zestaw komend ustawiających zakres pracy (Working Range) na 0/0/koniec
                tmpCommands = [
                    "TimelinePlay",
                    "TimelineStop",
                    "SetPlaybackStartFrame,0",
                    "SetPlaybackStopFrame,1000000",
                    "SetPlaybackLooping,0",
                    "SetPlaybackCurrentFrame,0",
                    "TimelineStop"
                ]
                for sz_command in tmpCommands:
                    return_code = streaming_client.send_command(sz_command)
                    print("Command: %s - return_code: %d" % (sz_command, return_code))
                time.sleep(1)
            elif c1 == 'w':
                # Zestaw komend ustawiających zakres pracy na 1/100/1500
                tmp_commands = [
                    "TimelinePlay",
                    "TimelineStop",
                    "SetPlaybackStartFrame,1",
                    "SetPlaybackStopFrame,1500",
                    "SetPlaybackLooping,0",
                    "SetPlaybackCurrentFrame,100",
                    "TimelineStop"
                ]
                for sz_command in tmp_commands:
                    return_code = streaming_client.send_command(sz_command)
                    print("Command: %s - return_code: %d" % (sz_command, return_code))
                time.sleep(1)
            elif c1 == 't':
                test_classes()  # uruchom testy struktur

            elif c1 == 'j':
                streaming_client.set_print_level(0)  # 0 = tylko numery klatek, bez danych/opisów
                print("Showing only received frame numbers and supressing data descriptions")
            elif c1 == 'k':
                streaming_client.set_print_level(1)  # 1 = pokazuj każdą klatkę + opisy
                print("Showing every received frame")

            elif c1 == 'l':
                print_level = streaming_client.set_print_level(20)  # co 20-tą klatkę
                print_level_mod = print_level % 100
                if (print_level == 0):
                    print("Showing only received frame numbers and supressing data descriptions")
                elif (print_level == 1):
                    print("Showing every frame")
                elif (print_level_mod == 1):
                    print("Showing every %dst frame" % print_level)
                elif (print_level_mod == 2):
                    print("Showing every %dnd frame" % print_level)
                elif (print_level == 3):
                    print("Showing every %drd frame" % print_level)
                else:
                    print("Showing every %dth frame" % print_level)

            elif c1 == 'q':
                is_looping = False           # zakończ pętlę
                streaming_client.shutdown()  # zamknij połączenie/gniazda
                break                        # wyjdź z pętli while
            else:
                print("Error: Command %s not recognized" % c1)  # nieznane polecenie
            print("Ready...\n")          # prompt gotowości po obsłudze komendy
    print("exiting")                      # końcowy wydruk po wyjściu z pętli
