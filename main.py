from sys import argv
from netraz_cli import netraz_help, commands
from helpers import netraz_output
from netraz_commands import (
    create_network_insights_path,
    delete_network_insights_path,
    delete_network_insights_analysis,
    start_network_insights_analysis,
    get_network_insights_paths,
    get_network_insights_analyses,
    variable_file_support
)

if __name__ == "__main__":

    # empty args
    if len(argv)==1:
        # help
        netraz_help()
        exit()

    # command decomposition
    command, args = argv[1], argv[2:]

    if command in commands:
        try:
            if command == commands[0]:
                # help
                netraz_help()
            elif command == commands[1]:
                # create-nip
                netraz_output("o","Create network insights path")
                create_network_insights_path(args)
            elif command == commands[2]:
                # delete-nip
                netraz_output("o","Delete network insights path")
                delete_network_insights_path(args)
            elif command == commands[3]:
                # delete-nia
                netraz_output("o","Delete network insights analysis")
                delete_network_insights_analysis(args)
            elif command == commands[4]:
                # start-nia
                netraz_output("o","Start network insights analysis")
                start_network_insights_analysis(args)
            elif command == commands[5]:
                # get-nips
                netraz_output("o","Get network insights paths")
                get_network_insights_paths(args)
            elif command == commands[6]:
                # get-nias
                netraz_output("o", "Get network insights analyses")
                get_network_insights_analyses(args)
            elif command == commands[7]:
                # file_support
                netraz_output("o", "Variable file support")
                variable_file_support(args)
            
            # healthy finish
            netraz_output("o", "Completed")
        except Exception as e:
            netraz_output("o", "Aborted")
            netraz_output("e", e)
    else:
        netraz_output("e", "Unrecognised command: " + command)
        netraz_help()
