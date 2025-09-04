
#============================================================================= #type: ignore  # noqa E501
# Copyright © 2025 NaturalPoint, Inc. All Rights Reserved.
#
# THIS SOFTWARE IS GOVERNED BY THE OPTITRACK PLUGINS EULA AVAILABLE AT https://www.optitrack.com/about/legal/eula.html #type: ignore  # noqa E501
# AND/OR FOR DOWNLOAD WITH THE APPLICABLE SOFTWARE FILE(S) (“PLUGINS EULA”). BY DOWNLOADING, INSTALLING, ACTIVATING #type: ignore  # noqa E501
# AND/OR OTHERWISE USING THE SOFTWARE, YOU ARE AGREEING THAT YOU HAVE READ, AND THAT YOU AGREE TO COMPLY WITH AND ARE #type: ignore  # noqa E501
# BOUND BY, THE PLUGINS EULA AND ALL APPLICABLE LAWS AND REGULATIONS. IF YOU DO NOT AGREE TO BE BOUND BY THE PLUGINS #type: ignore  # noqa E501
# EULA, THEN YOU MAY NOT DOWNLOAD, INSTALL, ACTIVATE OR OTHERWISE USE THE SOFTWARE AND YOU MUST PROMPTLY DELETE OR #type: ignore  # noqa E501
# RETURN IT. IF YOU ARE DOWNLOADING, INSTALLING, ACTIVATING AND/OR OTHERWISE USING THE SOFTWARE ON BEHALF OF AN ENTITY, #type: ignore  # noqa E501
# THEN BY DOING SO YOU REPRESENT AND WARRANT THAT YOU HAVE THE APPROPRIATE AUTHORITY TO ACCEPT THE PLUGINS EULA ON #type: ignore  # noqa E501
# BEHALF OF SUCH ENTITY. See license file in root directory for additional governing terms and information. #type: ignore  # noqa E501
#============================================================================= #type: ignore  # noqa E501


# OptiTrack NatNet direct depacketization sample for Python 3.x
#
# Uses the Python NatNetClient.py library to establish
# a connection and receive data via that NatNet connection
# to decode it using the NatNetClientLibrary.

import sys
import os
import time
import argparse
from scapy.all import Raw, PcapReader, socket
from NatNetClient import NatNetClient
import DataDescriptions
import MoCapData

# This is a callback function that gets connected to the NatNet client
# and called once per mocap frame.


def receive_new_frame_with_data(data_dict):
    order_list = ["frameNumber", "markerSetCount", "unlabeledMarkersCount", #type: ignore  # noqa F841
                  "rigidBodyCount", "skeletonCount", "labeledMarkerCount",
                  "timecode", "timecodeSub", "timestamp", "isRecording",
                  "trackedModelsChanged", "offset", "mocap_data"]
    dump_args = True
    if dump_args is True:
        out_string = "    "
        for key in data_dict:
            out_string += key + "= "
            if key in data_dict:
                out_string += str(data_dict[key]) + " "
            out_string += "/"
        print(out_string)

def receive_rigid_body_frame(new_id, position, rotation):
    pass

def add_lists(totals, totals_tmp):
    totals[0] += totals_tmp[0]
    totals[1] += totals_tmp[1]
    totals[2] += totals_tmp[2]
    return totals

def print_configuration(natnet_client):
    # NatNet Server Info
    application_name = natnet_client.get_application_name()
    nat_net_requested_version = natnet_client.get_nat_net_requested_version()
    nat_net_version_server = natnet_client.get_nat_net_version_server()
    server_version = natnet_client.get_server_version()
    print("  NatNet Server Info")
    print("    Application Name %s" % (application_name))
    print("    MotiveVersion  %d %d %d %d" % (server_version[0], server_version[1], server_version[2], server_version[3]))  #type: ignore  # noqa F501
    print("    NatNetVersion  %d %d %d %d" % (nat_net_version_server[0], nat_net_version_server[1], nat_net_version_server[2], nat_net_version_server[3])) #type: ignore  # noqa F501
    print("  NatNet Bitstream Requested")
    print("    NatNetVersion  %d %d %d %d" % (nat_net_requested_version[0], nat_net_requested_version[1], #type: ignore  # noqa F501
                                              nat_net_requested_version[2], nat_net_requested_version[3])) #type: ignore  # noqa F501

def request_data_descriptions(s_client):
    s_client.send_request(s_client.command_socket, s_client.NAT_REQUEST_MODELDEF, "",  (s_client.server_ip_address, s_client.command_port)) #type: ignore  # noqa F501

def test_classes():
    totals = [0, 0, 0]
    print("Test Data Description Classes")
    totals_tmp = DataDescriptions.test_all()
    totals = add_lists(totals, totals_tmp)
    print("")
    print("Test MoCap Frame Classes")
    totals_tmp = MoCapData.test_all()
    totals = add_lists(totals, totals_tmp)
    print("")
    print("All Tests totals")
    print("--------------------")
    print("[PASS] Count = %3.1d" % totals[0])
    print("[FAIL] Count = %3.1d" % totals[1])
    print("[SKIP] Count = %3.1d" % totals[2])

def my_parse_args(arg_list, args_dict):
    arg_list_len = len(arg_list)
    if arg_list_len > 1:
        args_dict["serverAddress"] = arg_list[1]
        if arg_list_len > 2:
            args_dict["clientAddress"] = arg_list[2]
        if arg_list_len > 3:
            if len(arg_list[3]):
                args_dict["use_multicast"] = True
                if arg_list[3][0].upper() == "U":
                    args_dict["use_multicast"] = False
        if arg_list_len > 4:
            args_dict["stream_type"] = arg_list[4]
    return args_dict

def find_all_gt_caps(start_dir="."):
    file_list = []
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if file.endswith(".cap"):
                gtcap = os.path.join(root, file)
                file_list.append(gtcap)
    return file_list

def validate_file_path(file):
    """'Type' for argparse - checks that file exists."""
    if not os.path.exists(file):
        raise argparse.ArgumentTypeError("The path {0} does not"
                                         " exist.".format(file))
    return file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract GT OT from cap file.')
    parser.add_argument(
        '--outdir',
        dest='out_dir',
        type=validate_file_path,
        default="./Data",
        help="Save json to this directory.")
    parser.add_argument(
        '--capdir',
        dest='capdir',
        type=validate_file_path,
        default="./Data",
        help="GT ethernet recorded stream")
    args = parser.parse_args()
    optionsDict = {}
    optionsDict["clientAddress"] = "127.0.0.1"
    optionsDict["serverAddress"] = "127.0.0.1"
    optionsDict["use_multicast"] = None
    optionsDict["stream_type"] = None
    stream_type_arg = None
    streaming_client = NatNetClient()
    streaming_client.set_client_address(optionsDict["clientAddress"])
    streaming_client.set_server_address(optionsDict["serverAddress"])
    streaming_client.new_frame_with_data_listener = receive_new_frame_with_data  # type ignore # noqa E501
    streaming_client.rigid_body_listener = receive_rigid_body_frame
    is_running = streaming_client.run('d')
    if not is_running:
        print("ERROR: Could not start streaming client.")
        try:
            sys.exit(1)
        except SystemExit:
            print("...")
        finally:
            print("exiting")
    is_looping = True
    time.sleep(1)
    gtCapFiles = []
    if os.path.isdir(args.capdir):
        gtCapFiles = find_all_gt_caps(args.capdir)
    elif os.path.isfile(args.capdir):
        gtCapFiles = [args.capdir]
    else:
        print("CAP file neither dir nor file, exiting...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.connect((streaming_client.local_ip_address, streaming_client.data_port))
    for gtfile in gtCapFiles:
        filename, fileext = os.path.splitext(os.path.basename(gtfile))
        print("Start processing {}".format(filename))
        streaming_client.set_output_file(os.path.join(args.out_dir, filename + "_OptiTrack.json"))
        streaming_client.set_all_jsondata([])
        capreader = PcapReader(gtfile)
        for pkt in capreader:
            if 'UDP' in pkt and pkt['UDP'].dport in [streaming_client.data_port, streaming_client.data_port]:
                print(pkt.time)
                streaming_client.set_pkt_time(int(pkt.time * 1000000000))
                pkt['UDP'].dport = 1511
                #streaming_client.process_message(pkt[Raw].load)
                try:
                    streaming_client.process_message(pkt[Raw].load)
                except Exception as e:
                    print(f"[!] Błąd przy przetwarzaniu pakietu: {e}")
                    continue
                print("Packet processed: {:>20}".format(pkt.time), end='\r')
        streaming_client.write_to_file()
    s.send(b"Stop")
    streaming_client.shutdown()
    print("exiting")
