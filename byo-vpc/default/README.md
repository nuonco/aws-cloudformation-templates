# BYO-VPC

Generic BYO-VPC Stack. This is a "pass-through" CloudFormation template useful for deploying infrastructure into an
existing VPC. Accepts existing VPC and subnet IDs, validates that the subnets belong to the specified VPC, and makes
them available them in the format expected by Nuon via the PhoneHome props.

- Does not create any VPC or subnet resources
- Validates that all provided subnets belong to the specified VPC using a Lambda-backed Custom Resource for validation

### Notes

The Lambda-backed custom resource performs the following validations:

1. **Subnet ownership**: Verifies all provided subnets (public, private, and runner) belong to the specified VPC
2. **Runner internet access**: Confirms the runner subnet has a route to `0.0.0.0/0` via a NAT Gateway or Internet
   Gateway

If validation fails, the stack creation will fail with a descriptive error message indicating which subnets are invalid
or missing internet access.

### Utils

There is a script that can be used to gather the necessary information about a VPC for use in the template.

```bash
./scripts/vpc-preflight.sh
```

### TODO

- [ ] add support for creating a fresh subnet for the runner w/ a nat gateway.

## Description

<!-- cf-doc md stack.yaml -->

Deploys a VPC w/ 1 to 3 public subnets (one per az), 1 to 3 private subnets (one per az), a Nat gateway, and an internet
gateway. The subnets are tagged for use by EKS (alb ingress controller). To control the number of public or private
subnets, remove the subnets (starting with 3 then 2). Will create at least one subnet.

## Parameters

| Name               | Description                                                                                      |  Type  |     Default     | Allowed Values |
| ------------------ | ------------------------------------------------------------------------------------------------ | :----: | :-------------: | :------------- |
| ClusterName        | The name for the EKS Cluster that will be deployed on this VPC.                                  | String |                 |                |
| NuonAppID          | The Nuon Install ID. Used in tags.                                                               | String |                 |                |
| NuonInstallID      | The Nuon Install ID; prefixed to resource names.                                                 | String |                 |                |
| NuonOrgID          | The Nuon Org ID. Used in tags.                                                                   | String |                 |                |
| PrivateSubnet1CIDR | Please enter the IP range (CIDR notation) for the private subnet in the first Availability Zone  | String | 10.128.130.0/24 |                |
| PrivateSubnet2CIDR | Please enter the IP range (CIDR notation) for the private subnet in the second Availability Zone | String | 10.128.132.0/24 |                |
| PrivateSubnet3CIDR | Please enter the IP range (CIDR notation) for the private subnet in the third Availability Zone  | String | 10.128.134.0/24 |                |
| PublicSubnet1CIDR  | Please enter the IP range (CIDR notation) for the public subnet in the first Availability Zone   | String |  10.128.0.0/26  |                |
| PublicSubnet2CIDR  | Please enter the IP range (CIDR notation) for the public subnet in the second Availability Zone  | String | 10.128.0.64/26  |                |
| PublicSubnet3CIDR  | Please enter the IP range (CIDR notation) for the public subnet in the third Availability Zone   | String | 10.128.0.128/26 |                |
| RunnerSubnetCIDR   | Please enter the IP range (CIDR notation) for the dedicated private subnet for the runner.       | String | 10.128.128.0/24 |                |
| VpcCIDR            | Please enter the IP range (CIDR notation) for this VPC.                                          | String |  10.128.0.0/16  |                |

## Outputs

| Name           | Description                                  | Export |
| -------------- | -------------------------------------------- | ------ |
| PrivateSubnets | A list of the private subnets.               |        |
| PublicSubnets  | A list of the public subnets.                |        |
| RunnerSubnet   | The dedicated private subnet for the runner. |        |
| VPC            | The VPC.                                     |        |
