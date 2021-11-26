from os.path import exists
from os import getcwd
from json import loads, dumps
from tabulate import tabulate
from subprocess import Popen, PIPE, call
from re import compile
from auth.helpers import _get_ldap_user

# aws errors
aws_err = {
    "ExpiredToken": "An error occurred (ExpiredToken) when calling the GetCallerIdentity operation: The security token included in the request is expired"
}

# netraz output types
netraz_output_types={
    "o":" output",
    "e":"  error",
    "h":"   help",
    "c":"aws-cli",
    "p":"   plan"
}

def construct_aws_cli_command(command, subcommand, params=[], values=[]):
    components = ["aws"]
    
    components.append(command)
    components.append(subcommand)

    for p, v in zip(params, values):
        components.append("--"+p)
        components.append(v)

    command = " ".join(components)

    return command

def check_auth():
    #netraz_output("o", "Verifying AWS CLI authenticaion")
    command = construct_aws_cli_command("sts", "get-caller-identity")
    stdout, stderr = execute_aws_cli(command)
    return stdout, stderr

def cli_is_not_authenticated():   
    # Check auth
    stdout, stderr = check_auth() 

    # Handle outcome
    if aws_err["ExpiredToken"] in stderr:
        # creds are expired

        # refresh creds
        # optional code in folder "auth"
        if exists("auth"):
            return check_private_auth()

        # No auth 
        netraz_output("e", "AWS CLI not authenticated")
        netraz_output("h", "Check your AWS CLI creds in ~/.aws/credentials")
        return True
    else:
        # creds are ok
        return False

def execute_aws_cli(command):
    # post what you're about to do 
    # netraz_output("c", command)

    command = [cmd.replace("&#;"," ") for cmd in command.split()]

    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    strout = stdout.decode("utf-8").replace('\n','')
    strerr = stderr.decode("utf-8").replace('\n','')

    return strout, strerr

def stdout_to_json(s):
    j = loads(s)
    return j

def print_netraz_table(info, headers):
    lineprint(["", tabulate(info, headers), "", "Rows: {}".format(len(info)), ""])
    return

def jsonprint(j):
    lineprint(["", dumps(j, indent=2, sort_keys=True), ""])
    return

def lineprint(lines):
    for line in lines:
        print(line)
    return

def netraz_output(type, output):
    output = ["netraz", netraz_output_types[type], str(output)]
    print(": ".join(output))

def check_private_auth():
    from auth.helpers import _setup_auth
    command, scriptname = _setup_auth()
    #netraz_output("o", "Running {3} in {0}/{1}/{2}".format(*[*command[1:], scriptname]))
    
    # execute script
    call(command)

    # check auth with aws get-caller-identity
    stdout, stderr = check_auth() 

    # not-in logic returns false if auth and true if not
    return aws_err["ExpiredToken"] in stderr

def check_file_support_dependencies(vars_name):

    # directory paths
    json = ".json"
    common_vars = "common" + json
    dp = [getcwd(), "/", "vars", "/"]
    cv = ''.join(dp)+common_vars
    sv = ''.join(dp)+vars_name+json
    vars = ''.join(dp[0:2])

    if not exists(vars):
        # check vars folder exists in cwd
        raise Exception("Vars folder not found")
    elif not exists(cv):
        # check common vars file exists in vars folder
        raise Exception("File: "+common_vars[:-5]+" not found")
    elif not exists(sv):
        # check specified vars file exists in vars folder
        raise Exception("File: "+vars_name+" not found")

    global sourcepath
    sourcepath = ''.join(dp[2:])+vars_name+json

    return sv, cv



def validate_s_vars(var):
    # required: dest(str) or destIp(str:IP), protocol(tcp/udp), source(str) or sourceIp(str:IP)
    # optional: destPort(int), Tags(list)
    # priority: if a sourceIp or destIp are declared, then override the dest/source accordingly

    constraints = {
        "Destination": {"Name": "Destination", "Type": str},
        "DestinationIp": {"Name": "DestinationIp", "Type": str},
        "Source": {"Name": "Source", "Type": str},
        "SourceIp": {"Name": "SourceIp", "Type": str},
        "Protocol": {"Name": "Protocol", "Type": str, "Enum": ["tcp", "udp"]},
        "DestinationPort": {"Name": "DestinationPort", "Type": int},
        "Tags": {"Name": "Tags:Name", "Type": str}
    }
    ip_regex = compile(r"""^([0-9]{1,3}[.]){3}[0-9]{1,3}$""")

    for nip in var["nips"]:
        for con_k, con_v in constraints.items():
            try:
                attribute = nip[con_v["Name"]] # will throw exception
                attribute + "string" # will throw exception

                # check types
                if con_v["Name"] == "Protocol":
                    con_v["Enum"].index(attribute) # will throw exeption
                if con_v["Name"] == "DestinationPort" and attribute != "":
                    int(attribute)

                if con_v["Name"][-2:]=="Ip":
                    if attribute == "":
                        # double check the corresponding required attribute
                        if nip[con_k[:-2]] == "":
                            raise Exception("You must specify a source/destination id if not an IP")
                        # then ignore
                        pass
                    elif not ip_regex.match(attribute):
                        raise Exception("\"" + attribute + "\" is not a suitable IP address")
                    else:
                        # this is a suitable IP and should replace the source/destination
                        pass

            except TypeError:
                raise Exception("Attributes must be declared as strings")
            except ValueError:
                if con_v["Name"] == "Protocol":
                    raise Exception("Protocol must be tcp or udp")
                if con_v["Name"] == "DestinationPort":
                    raise Exception("Destination port string must only contain an integer: \"" + str(attribute) + "\"")
            except KeyError:
                if (con_v["Name"] in ["DestinationIp", "DestinationPort", "SourceIp"]):
                    pass
                else:
                    raise Exception("Required attribute \"" + con_v["Name"] + "\" not found")
            except Exception as e:
                print(e)

    return var

def validate_and_process_c_vars(c_var):
    try:
        c_var["Tags"]
    except Exception as e:
        print(type(e))

    # append ldap user
    user = _get_ldap_user()
    c_var["Tags"]["CreatedBy"] = user

    # append sourcepath
    c_var["Tags"]["SourcePath"] = sourcepath
        
    return c_var

def validate_and_process_vars(var, c_var):
    var = validate_s_vars(var)
    c_var = validate_and_process_c_vars(c_var)
    return var, c_var

def construct_array_nip(nips_list):
    # Construct info array
    headers = ['Name', 'NetworkInsightsPathId', 'Source', 'Destination', 'DestinationPort', 'Protocol']
    info = []
    for nips in nips_list["NetworkInsightsPaths"]:
        row = []
        for column in headers:
            try:
                row.append(nips[column])
            except:
                try:
                    if column == "Name":
                        row.append([t["Value"] for t in nips["Tags"] if t["Key"]=="Name"][0])
                    else:
                        row.append("-")
                except:
                    row.append("-")
                    
        info.append(row)

    return info, headers

def construct_array_nia(nias_list):
    # Construct info array
    headers = ['NetworkInsightsPathId', 'NetworkInsightsAnalysisId', 'NetworkPathFound', 'StartDate', 'Status']
    info = []
    for nias in nias_list["NetworkInsightsAnalyses"]:
        row = []
        for column in headers:
            try:
                row.append(nias[column])
            except:
                row.append("-")
        info.append(row)

    return info, headers

def construct_tag_string(nip, c_var):
    #tags = "ResourceType=network-insights-path,
    #        Tags=[
    #           {Key=string,Value=string},
    #           {Key=string,Value=string},
    #           ...
    #        ]"

    tag_string = "ResourceType=network-insights-path"
    tag_string += ",Tags=["
    key_value = "{{Key=\"{}\",Value=\"{}\"}}"
    
    # Name
    tag_string += key_value.format("Name", nip["Tags:Name"].replace(" ","&#;"))

    # Common Tags
    for k,v in c_var["Tags"].items():
        tag_string += "," + key_value.format(k,v.replace(" ","&#;"))
    
    # end
    tag_string += "]"

    return tag_string
