import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

from cfnlint.decode import decode


class VpcDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.template, errors = decode(str(Path(__file__).with_name("stack.yaml")))
        self.assertEqual(errors, [])
        self.ec2 = Mock()
        boto3 = ModuleType("boto3")
        boto3.client = Mock(return_value=self.ec2)
        self.response = ModuleType("cfnresponse")
        self.response.SUCCESS = "SUCCESS"
        self.response.FAILED = "FAILED"
        self.response.send = Mock()
        namespace = {}
        code = self.template["Resources"]["SubnetValidatorFunction"]["Properties"]["Code"]["ZipFile"]
        with patch.dict(sys.modules, boto3=boto3, cfnresponse=self.response):
            exec(compile(code, "index.py", "exec"), namespace)
        self.handler = namespace["handler"]
        self.event = {
            "RequestType": "Create",
            "ResourceProperties": {
                "VpcId": "vpc-example",
                "PublicSubnets": "subnet-public",
                "PrivateSubnets": "subnet-private",
                "RunnerSubnet": "subnet-runner",
            },
        }
        self.ec2.describe_vpcs.return_value = {
            "Vpcs": [{"CidrBlockAssociationSet": [
                {"CidrBlock": "10.11.0.0/24", "CidrBlockState": {"State": "associated"}},
                {"CidrBlock": "10.1.10.0/24", "CidrBlockState": {"State": "associated"}},
                {"CidrBlock": "192.168.0.0/16", "CidrBlockState": {"State": "disassociating"}},
                {"CidrBlock": "172.16.0.0/16", "CidrBlockState": {"State": "failed"}},
            ]}],
        }
        self.ec2.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-runner", "VpcId": "vpc-example"}],
        }
        self.ec2.describe_route_tables.return_value = {
            "RouteTables": [{"Routes": [{"DestinationCidrBlock": "0.0.0.0/0", "NatGatewayId": "nat-example"}]}],
        }

    def test_create_and_update_discover_all_associated_ipv4_cidrs(self):
        for request_type in ("Create", "Update"):
            with self.subTest(request_type=request_type):
                self.event["RequestType"] = request_type
                self.handler(self.event, None)
                self.ec2.describe_vpcs.assert_called_with(VpcIds=["vpc-example"])
                self.response.send.assert_called_with(self.event, None, "SUCCESS", {
                    "ValidatedPublicSubnets": "subnet-public",
                    "ValidatedPrivateSubnets": "subnet-private",
                    "ValidatedRunnerSubnet": "subnet-runner",
                    "VpcId": "vpc-example",
                    "VpcCidrEntries": [{"Cidr": "10.1.10.0/24"}, {"Cidr": "10.11.0.0/24"}],
                })

    def test_discovery_error_fails_validation(self):
        self.ec2.describe_vpcs.side_effect = RuntimeError("describe denied")
        self.handler(self.event, None)
        self.response.send.assert_called_once_with(self.event, None, "FAILED", {}, reason="describe denied")

    def test_subnet_validation_is_preserved(self):
        self.ec2.describe_subnets.return_value["Subnets"][0]["VpcId"] = "vpc-other"
        self.handler(self.event, None)
        self.assertEqual(self.response.send.call_args.args[2], "FAILED")
        self.assertIn("do not belong to VPC", self.response.send.call_args.kwargs["reason"])

    def test_delete_does_not_query_the_vpc(self):
        self.event["RequestType"] = "Delete"
        self.handler(self.event, None)
        self.ec2.describe_vpcs.assert_not_called()
        self.response.send.assert_called_once_with(self.event, None, "SUCCESS", {})

    def test_prefix_list_uses_discovery_and_updates_existing_stacks(self):
        resources = self.template["Resources"]
        self.assertEqual(resources["SubnetValidation"]["Properties"]["SchemaVersion"], "2")
        prefix_list = resources["VpcIpv4PrefixList"]["Properties"]
        self.assertEqual(prefix_list["Entries"], {"Fn::GetAtt": ["SubnetValidation", "VpcCidrEntries"]})
        self.assertEqual(prefix_list["MaxEntries"], 50)
        self.assertEqual(prefix_list["AddressFamily"], "IPv4")
        self.assertEqual(self.template["Outputs"]["VpcIpv4PrefixListId"]["Value"], {"Ref": "VpcIpv4PrefixList"})
        actions = resources["SubnetValidatorRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][0]["Action"]
        self.assertIn("ec2:DescribeVpcs", actions)


if __name__ == "__main__":
    unittest.main()
