# netraz

Welcome to netraz, a cli tool for instantiating aws NETwork Reachability AnalyZer services!
Commands include: help, create-nip
usage: `netraz <command> [parameters]`

## Bash Alias
    netraz(){
            python3 /<srcpath>/netraz/main.py $@
    }

## Commands
### netraz help
`netraz help`
### netraz create-nip
`netraz create-nip [source id] [target id] [protocol] [dst port]`

`netraz create-nip i-1234abcd i-5678efgh TCP 443`
### netraz delete-nip
`netraz delete-nip [path_id] [path_id] ...`

`netraz delete-nip nip-1234abcd`
### netraz delete-nia
`netraz delete-nia [path_id] [path_id] ...`

`netraz delete-nia nia-1234abcd`
### netraz -f
`netraz -f [filename] [plan/apply]`

`netraz -f sample apply`

## PyTests
Install: `pip install pytest`

Run: `pytest tests/`