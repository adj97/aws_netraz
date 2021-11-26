from helpers import lineprint

def netraz_help():
    print_message = [
        "Welcome to netraz, a cli tool for instantiating aws NETwork Reachability AnalyZer services!",
        "Commands include: " + ", ".join(commands),
        "usage: netraz <command> [parameters]"
    ]
    lineprint(print_message)

commands = [
    "help",
    "create-nip",
    "delete-nip",
    "delete-nia",
    "start-nia",
    "get-nips",
    "get-nias",
    "-f"
]

file_support_actions = [
    "plan",
    "apply"
]
