# VPC for EKS

Deploys a VPC w/ 1 to 3 public subnets (one per az), 1 to 3 private subnets (one
per az), a Nat gateway, and an internet gateway. The subnets are tagged for use
by EKS (alb ingress controller). To control the number of public or private
subnets, remove the subnets (starting with 3 then 2). Will create at least one
subnet.

## Parameters

| Name               | Description                                                                                      |  Type  |     Default     | Allowed Values |
| ------------------ | ------------------------------------------------------------------------------------------------ | :----: | :-------------: | :------------- |
| ClusterName        | The name for the EKS Cluster that will be deployed on this VPC.                                  | String |                 |                |
| NuonInstallID      | The Nuon Install ID; prefixed to resource names.                                                 | String |                 |                |
| NuonOrgID          | The Nuon Org ID. Used in tags.                                                                   | String |                 |                |
| NuonAppID          | The Nuon Install ID. Used in tags.                                                               | String |                 |                |
| VpcCIDR            | Please enter the IP range (CIDR notation) for this VPC.                                          | String |  10.128.0.0/16  |                |
| PublicSubnet1CIDR  | Please enter the IP range (CIDR notation) for the public subnet in the first Availability Zone   | String |  10.128.0.0/26  |                |
| PublicSubnet2CIDR  | Please enter the IP range (CIDR notation) for the public subnet in the second Availability Zone  | String | 10.128.0.64/26  |                |
| PublicSubnet3CIDR  | Please enter the IP range (CIDR notation) for the public subnet in the third Availability Zone   | String | 10.128.0.128/26 |                |
| RunnerSubnetCIDR   | Please enter the IP range (CIDR notation) for the dedicated private subnet for the runner.       | String | 10.128.128.0/24 |                |
| PrivateSubnet1CIDR | Please enter the IP range (CIDR notation) for the private subnet in the first Availability Zone  | String | 10.128.130.0/24 |                |
| PrivateSubnet2CIDR | Please enter the IP range (CIDR notation) for the private subnet in the second Availability Zone | String | 10.128.132.0/24 |                |
| PrivateSubnet3CIDR | Please enter the IP range (CIDR notation) for the private subnet in the third Availability Zone  | String | 10.128.134.0/24 |                |

## Outputs

| Name           | Description                                  | Export |
| -------------- | -------------------------------------------- | ------ |
| VPC            | The VPC.                                     |        |
| PublicSubnets  | A list of the public subnets.                |        |
| PrivateSubnets | A list of the private subnets.               |        |
| RunnerSubnet   | The dedicated private subnet for the runner. |        |
