from json import load
from json.decoder import JSONDecodeError
from helpers import (
    cli_is_not_authenticated,
    construct_array_nia,
    construct_array_nip,
    construct_tag_string, 
    netraz_output, 
    construct_aws_cli_command, 
    execute_aws_cli, 
    stdout_to_json, 
    jsonprint, 
    print_netraz_table,
    check_file_support_dependencies,
    validate_and_process_vars
)
from netraz_cli import file_support_actions

def create_network_insights_path(args):
    if cli_is_not_authenticated():
        return
    elif (len(args) < 3 or len(args) > 5):
        netraz_output("e", "Unrecognised arguments")
        netraz_output("h", "netraz create-nip [src_id] [dst_id] [prot] ...")
    else:
        pre_params = [
            "source",       # source instance id
            "destination",  # destination id
            "protocol",         # internet protocol 
            "destination-port",      # destination port
            "tag-specifications"
        ]

        values =[]
        params =[]

        for idx, val in enumerate(args):
            if val != "":
                values.append(val)
                params.append(pre_params[idx])

        aws_cli_command = construct_aws_cli_command("ec2", "create-network-insights-path", params, values)
        stdout, stderr = execute_aws_cli(aws_cli_command)

        # known error catching
        if "invalid literal for int() with base 10: 'tcp" in stderr:
            netraz_output("e", "Check parameter order")
            raise Exception("Unexpected data type")

        # print what you have just done
        stdoutjson = stdout_to_json(stdout)["NetworkInsightsPath"]
        for k in ["DestinationPort", "NetworkInsightsPathArn", "Protocol", "Tags"]:
            try:
                del stdoutjson[k]
            except:
                # key doesn't exist anyway
                pass
        netraz_output("o", "Created NIP:")
        jsonprint(stdoutjson)

    return stdoutjson

def delete_network_insights_path(args, recursive=False):
    if cli_is_not_authenticated():
        return
    elif (len(args) < 1):
        netraz_output("h", "netraz delete-nip [path_id] [path_id] ...")
        raise Exception("No arguments prescribed")
    else:
        # if recursive = true then remove all the child analyses from the args list
        if recursive:
            # get all child nia's for each args(path_id)
            aws_cli_command = construct_aws_cli_command("ec2", "describe-network-insights-analyses")
            stdout, stderr = execute_aws_cli(aws_cli_command)
            all_nias_list = stdout_to_json(stdout)            

            # get list of nia's that are blocking the deleting of args paths
            ntd = [nia for nia in all_nias_list["NetworkInsightsAnalyses"] if nia["NetworkInsightsPathId"] in args]
            ntd_id = [nia["NetworkInsightsAnalysisId"] for nia in ntd]

            # then delete_network_insights_analysis(nias_to_dele)
            delete_network_insights_analysis(ntd_id)

        params, values = [], []

        for path_id in args:
            values.append(path_id)
            params.append("network-insights-path-id")
            aws_cli_command = construct_aws_cli_command("ec2", "delete-network-insights-path", params, values)
            stdout, stderr = execute_aws_cli(aws_cli_command)

            if "AnalysisExistsForNetworkInsightsPath" in stderr:
                raise Exception(stderr)
            else:
                # print what you have just done
                print(stdout)

    return

def delete_network_insights_analysis(args):
    if cli_is_not_authenticated():
        return
    elif (len(args) < 1):
        netraz_output("e", "No arguments prescribed")
        netraz_output("h", "netraz delete-nia [analysis_id] [analysis_id] ...")
    else:
        params, values = [], []

        for nia_id in args:
            values.append(nia_id)
            params.append("network-insights-analysis-id")
            aws_cli_command = construct_aws_cli_command("ec2", "delete-network-insights-analysis", params, values)
            stdout, stderr = execute_aws_cli(aws_cli_command)

            if "AnalysisExistsForNetworkInsightsPath" in stderr:
                netraz_output("e", stderr)
                raise Exception()
            else:
                # print what you have just done
                print(stdout)
    return 0

def start_network_insights_analysis(args):
    if cli_is_not_authenticated():
        return
    elif (len(args) != 1):
        netraz_output("e", "Only one argument allowed: nip-id")
        netraz_output("h", "netraz start-nia [path_id]")
    else:
        # one arg is network insights path id
        nip_id = args[0]
        
        params, values = [], []
        values.append(nip_id)
        params.append("network-insights-path-id")

        aws_cli_command = construct_aws_cli_command("ec2", "start-network-insights-analysis", params, values)
        stdout, stderr = execute_aws_cli(aws_cli_command)

        if "InvalidParameterValue" in stderr:
            netraz_output("e", stderr)
            raise Exception()
        else:
            # print what you have just done
            stdoutjson = stdout_to_json(stdout)["NetworkInsightsAnalysis"]
            for k in ["NetworkInsightsAnalysisArn", "Status"]:
                del stdoutjson[k]
            netraz_output("o", "Started NIA:")
            jsonprint(stdoutjson)

    return stdoutjson

def get_network_insights_paths(args):
    if cli_is_not_authenticated():
        return
    elif (len(args) >= 0):
        params, values = [], []

        if (len(args) == 0):
            output_message = "Getting all NIPs"
            print_title = "All available"
        elif (len(args) > 0):
            output_message = "Getting specific NIPs"
            print_title = "Requested"
            params.append("network-insights-path-ids")
            values.append(' '.join(args))

        netraz_output("o", output_message)
        aws_cli_command = construct_aws_cli_command("ec2", "describe-network-insights-paths", params, values)
        stdout, stderr = execute_aws_cli(aws_cli_command)
            
        # Convert output to json
        nips_list = stdout_to_json(stdout)

        # Construct info array
        info, headers = construct_array_nip(nips_list)

        if (len(args) == 1):
            # print single json
            jsonprint(nips_list["NetworkInsightsPaths"][0])
        else:
            # print info
            netraz_output("o", print_title + " network insights paths:")
            print_netraz_table(info, headers)

    return

def get_network_insights_analyses(args):
    if cli_is_not_authenticated():
        return
    elif (len(args) >= 0):

        if (len(args) == 0):
            output_message = "Getting all NIAs"
            print_title = "All available"
        elif (len(args) > 0):
            output_message = "Getting specific NIAs"
            print_title = "Requested"

        netraz_output("o", output_message)
        aws_cli_command = construct_aws_cli_command("ec2", "describe-network-insights-analyses")
        stdout, stderr = execute_aws_cli(aws_cli_command)
            
        # Convert output to json
        nias_list = stdout_to_json(stdout)

        # Construct info array
        info, headers = construct_array_nia(nias_list)

        if (len(args) == 1):
            # print json and explanations
            if args[0][0:5] != "nia-0":
                netraz_output("e", "Single argument get-nias is only permitted to be an nia_id")
                raise Exception("Parameter Error")
            else:
                explanations = nias_list["NetworkInsightsAnalyses"][0]["Explanations"]
                nias_list["NetworkInsightsAnalyses"][0].pop("Explanations",None)

                netraz_output("o", print_title + " network insights analysis:")
                jsonprint(nias_list["NetworkInsightsAnalyses"][0])

                # Construct info array
                headers = ['ExplanationCode', 'Direction', 'Subnet_Id', 'Vpc_Id', 'Acl_Id', 'NetworkInterface_Id', 'SecurityGroups_Ids']
                info = []
                for exp in explanations:
                    row = []
                    for column in headers:
                        try:
                            if "_" in column:
                                key, subkey = column.split("_")
                                if key == "SecurityGroups":
                                    subkey = subkey[:-1]
                                    sgids = []
                                    for sg in exp[key]:
                                        sgids.append(sg[subkey])
                                    row.append('\n'.join(sgids))
                                else:
                                    row.append(exp[key][subkey])
                            else:
                                row.append(exp[column])
                        except:
                            row.append("-")
                    info.append(row)

                netraz_output("o", print_title + " network insights analysis explanations:")
                print_netraz_table(info, headers)
        else:
            for idx, nia_row in enumerate(info):
                # if no match then delete from info
                non_empty_args = args != []
                row_nip_not_in_args = nia_row[0] not in args
                row_nia_not_in_args = nia_row[1] not in args
                if (non_empty_args and row_nip_not_in_args and row_nia_not_in_args):
                    # this entry is not interesting
                    info.pop(idx)

            # print info as table (no explanations)
            netraz_output("o", print_title + " network insights analyses:")
            print_netraz_table(info, headers)

    return
    
def variable_file_support(args):
    if cli_is_not_authenticated():
        return
    else:
        # unpack
        vars_name = args[0]
        try:
            action = args[1] # may throw index error
            action = file_support_actions.index(args[1]) # may throw value error
            action = file_support_actions[action] # success
        except ValueError:
            raise Exception("Parameter error: unknown action \"" + action + "\"")
        except IndexError:
            raise Exception("Parameter error: no action given")
        

        sv, cv = check_file_support_dependencies(vars_name)

        # All good to go ahead with the file
        netraz_output("o", "Processing file: "+vars_name)

        # load json files
        try:
            # vars file
            with open(sv) as f:
                var = load(f)
            # common file
            with open(cv) as f:
                c_var = load(f)
        except JSONDecodeError:
            raise Exception("Vars specification file syntax error")
        except Exception as e:
            print(type(e))

        # validate vars file
        var, c_var = validate_and_process_vars(var, c_var)
        
        # 1 check if the nips exist already
        # get all nips
        aws_cli_command = construct_aws_cli_command("ec2", "describe-network-insights-paths")
        stdout, stderr = execute_aws_cli(aws_cli_command)

        # Convert output to json
        all_nips_list = stdout_to_json(stdout)
        info, headers = construct_array_nip(all_nips_list)
        #print_netraz_table(info, headers)

        # get existing nip names
        existing_nip_names = [[t["Value"] for t in nip_json["Tags"] if t["Key"]=="Name"][0] for nip_json in all_nips_list["NetworkInsightsPaths"]]
        existing_nips = [nip for nip in all_nips_list["NetworkInsightsPaths"]]

        # ntc name declared here as some nips will be delete/create to change properties
        ntc_name = []

        # nip's to delete
        # nip's should be deleted if they (exist and are tagged with the current file path) and:
        #  - are not listed (by name) in the current vars file
        #  - are listed by name and any properties have changed (delete & re-create)
        ntd_name = []
        for nip in existing_nips:
            # ignore if not tagged with current file path
            twcfp = [t["Value"] for t in nip["Tags"] if t["Key"]=="SourcePath"][0][5:-5] == vars_name        
            if not twcfp: continue

            # delete if name not listed in current vars file
            nlicvf = [t["Value"] for t in nip["Tags"] if t["Key"]=="Name"][0] in [n["Tags:Name"] for n in var["nips"]]
            if not nlicvf: 
                ntd_name.append([t["Value"] for t in nip["Tags"] if t["Key"]=="Name"][0])
                continue

            # delete if any properties have changed
            # match by name
            ename = [t["Value"] for t in nip["Tags"] if t["Key"]=="Name"][0]
            v = [n for n in var["nips"] if n["Tags:Name"]==ename][0]
            phc = []
            phc.append(nip["Destination"] != v["Destination"])
            phc.append("DestinationPort" in nip and str(nip["DestinationPort"]) != str(v["DestinationPort"]))
            phc.append(nip["Protocol"] != v["Protocol"])
            phc.append(nip["Source"] != v["Source"])
            nip_cb = [t["Value"] for t in nip["Tags"] if t["Key"]=="CreatedBy"][0]
            v_cb = c_var["Tags"]["CreatedBy"]
            phc.append(nip_cb != v_cb)

            if any(phc):
                ntd_name.append([t["Value"] for t in nip["Tags"] if t["Key"]=="Name"][0])
                ntc_name.append([t["Value"] for t in nip["Tags"] if t["Key"]=="Name"][0])
                continue

            # else don't delete

        # nip's to create
        # nip's should be created if they either:
        #  - don't exist at all
        #  - do exist but(and) are tagged with a different vars file path
        for nip in var["nips"]:
            # if nip does not exist (by name)
            ndne = nip["Tags:Name"] not in existing_nip_names

            # if not tagged with current file path
            # SOMETHING IS WRONG WITH THIS LINE
            
            current_var_filepath_tag = ""
            try:
                current_var_filepath_tag = [[t["Value"] for t in n["Tags"] if t["Key"]=="SourcePath"] for n in existing_nips if [t["Value"] for t in n["Tags"] if t["Key"]=="Name"][0] == nip["Tags:Name"]][0][0][5:-5]
                ntwcfp = current_var_filepath_tag != vars_name
            except:
                ntwcfp = False

            if ndne:  
                # create if not exist
                ntc_name.append(nip["Tags:Name"])
            elif ntwcfp:
                # does exist but not current file path tag
                ntc_name.append(nip["Tags:Name"])
            else:
                continue

        # print
        if len(ntc_name)==0 and len(ntd_name)==0:
            # no ntc either
            netraz_output("o","No changes. AWS reachability for " + vars_name + " appears up-to-date.")
            return
        else:
            if len(ntd_name)!=0:
                # some ntd
                netraz_output("p","NIPs to delete: " + ', '.join(ntd_name))
            if len(ntc_name)!=0:
                # no ntd but some ntc
                netraz_output("p","NIPs to create: " + ', '.join(ntc_name))

        # get ntc's from var (declaration file)
        ntc = [nip for nip in var["nips"] if nip["Tags:Name"] in ntc_name]

        # get ntd's from existing_nips where the name is in ntd_name
        ntd = [n for n in existing_nips if [t["Value"] for t in n["Tags"] if t["Key"]=="Name"][0] in ntd_name]

        #plan does nothing
        if action!=file_support_actions[0]:
            # apply
            netraz_output("o", "Do you want to perform these actions? Only \"yes\" will be accepted to approve.")
            apply_confirmation = input("  Enter a value: ")
            if apply_confirmation != "yes":
                raise Exception("User aborted")
            else:
                # delete all ntd's and all of each ones associated nia's
                if (len(ntd) > 0):
                    ntd_ids = [n["NetworkInsightsPathId"] for n in ntd]
                    delete_network_insights_path(ntd_ids, recursive=True)

                # create non-existing
                for nip in ntc:
                    # setup create nip
                    args = []
                    args.append(nip["Source"])
                    args.append(nip["Destination"])
                    args.append(nip["Protocol"])
                    args.append(nip["DestinationPort"])
                    args.append(construct_tag_string(nip, c_var))
                    nip_id = create_network_insights_path(args)["NetworkInsightsPathId"]
                    nia_id = start_network_insights_analysis([nip_id])
        
    return