# VPC for BYO-EKS

Pass-through CloudFormation stack for Bring-Your-Own EKS scenarios. Accepts existing VPC and subnet IDs, validates that
the subnets belong to the specified VPC, and outputs them in the format expected by Nuon.

- Does not create any VPC or subnet resources
- Validates that all provided subnets belong to the specified VPC
- Uses a Lambda-backed Custom Resource for validation

## Parameters

| Name             | Description                                                                    |            Type            | Default | Required |
| ---------------- | ------------------------------------------------------------------------------ | :------------------------: | :-----: | :------: |
| ClusterName      | The name or ARN of the existing EKS Cluster.                                   |           String           |         |   Yes    |
| VpcID            | The ID of the existing VPC (e.g., vpc-xxxxxxxxx).                              |     AWS::EC2::VPC::Id      |         |   Yes    |
| PublicSubnetIDs  | Comma-separated list of existing public subnet IDs                             | List<AWS::EC2::Subnet::Id> |         |   Yes    |
| PrivateSubnetIDs | Comma-separated list of existing private subnet IDs                            | List<AWS::EC2::Subnet::Id> |         |   Yes    |
| RunnerSubnetID   | Subnet for the Nuon runner. Must have outbound internet access (e.g., via NAT) |     AWS::EC2::Subnet::Id   |         |   Yes    |
| NuonInstallID    | The Nuon Install ID; prefixed to resource names.                               |           String           |         |   Yes    |
| NuonOrgID        | The Nuon Org ID. Used in tags.                                                 |           String           |         |   Yes    |
| NuonAppID        | The Nuon App ID. Used in tags.                                                 |           String           |         |   Yes    |

## Outputs

| Name           | Description                        |
| -------------- | ---------------------------------- |
| VPC            | The VPC ID.                        |
| PublicSubnets  | Comma-separated public subnet IDs  |
| PrivateSubnets | Comma-separated private subnet IDs |
| RunnerSubnet   | The subnet ID for the Nuon runner  |
| ClusterName    | The EKS cluster name/ARN.          |

## Resources Created

This stack creates minimal resources for validation purposes:

- **SubnetValidatorRole**: IAM role for the Lambda function with `ec2:DescribeSubnets`, `ec2:DescribeRouteTables`, and `ec2:DescribeNatGateways` permissions
- **SubnetValidatorFunction**: Lambda function that validates subnets belong to the VPC and that the runner subnet has outbound internet access
- **SubnetValidation**: Custom resource that invokes the validator

## Usage

```bash
aws cloudformation create-stack \
  --stack-name my-byo-eks-vpc \
  --template-body file://stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=ClusterName,ParameterValue=my-eks-cluster \
    ParameterKey=VpcID,ParameterValue=vpc-0123456789abcdef0 \
    ParameterKey=PublicSubnetIDs,ParameterValue="subnet-pub1,subnet-pub2,subnet-pub3" \
    ParameterKey=PrivateSubnetIDs,ParameterValue="subnet-priv1,subnet-priv2,subnet-priv3" \
    ParameterKey=RunnerSubnetID,ParameterValue=subnet-runner \
    ParameterKey=NuonInstallID,ParameterValue=install-123 \
    ParameterKey=NuonOrgID,ParameterValue=org-456 \
    ParameterKey=NuonAppID,ParameterValue=app-789
```

## TODO

- [ ] Consider adding EKS cluster validation
