# external imports
from subprocess import PIPE, Popen

base_auth = "/auth/"
execute = "."

# chmod +x scriptname.sh
scripts = [
    "refresh_auth.sh",
    "get_user.sh"
]

def _setup_auth():
    # empty cmd
    command = []

    # local script path
    script_path = ''.join([execute, base_auth, scripts[0]])
    command.append(script_path)
    
    command.append("args") # script args

    return command, "getCredentialsScript.sh"

def _get_user():
    # empty cmd
    command = []

    # local script path
    script_path = ''.join([execute, base_auth, scripts[1]])
    command.append(script_path)

    # execute
    p = Popen(command, stdout=PIPE)
    output, err = p.communicate()    

    return output.decode("utf-8").replace('\n','')