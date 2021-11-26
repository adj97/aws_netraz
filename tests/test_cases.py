from helpers import construct_aws_cli_command

def test_construct_aws_cli_command():
    expected_output = [
        "aws ec2 create-network-insights-path --source i-qwertyuiop --destination i-qwertyuiop --destination-port 443 --protocol TCP",
        "aws ec2 start-network-insights-analysis --network-insights-path-id nip-qwertyuiop",
        "aws ec2 delete-network-insights-analysis --network-insights-analysis-id nia-qwertyuiop",
        "aws ec2 delete-network-insights-path --network-insights-path-id nip-qwertyuiop"
    ]
    input = [
        ["ec2", "create-network-insights-path", ["source", "destination", "destination-port", "protocol"], ["i-qwertyuiop", "i-qwertyuiop", "443", "TCP"]],
        ["ec2", "start-network-insights-analysis", ["network-insights-path-id"], ["nip-qwertyuiop"]],
        ["ec2", "delete-network-insights-analysis", ["network-insights-analysis-id"], ["nia-qwertyuiop"]],
        ["ec2", "delete-network-insights-path", ["network-insights-path-id"], ["nip-qwertyuiop"]],
    ]

    for i,e in zip(input, expected_output):
        output = construct_aws_cli_command(i[0], i[1], params=i[2], values=i[3])
        assert output == e