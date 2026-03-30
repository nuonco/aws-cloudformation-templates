## CIDR Allocation

Our VPC stacks are configured with sane defaults but are fully override-able.

### Default Configuration

The VPC uses `10.128.0.0/16` (65,536 IPs total). Subnets are allocated as follows:

| Subnet           | CIDR            | Total IPs | Usable IPs | Purpose                |
| ---------------- | --------------- | --------: | ---------: | ---------------------- |
| Public Subnet 1  | 10.128.0.0/26   |        64 |         59 | ALB / ingress (AZ1)    |
| Public Subnet 2  | 10.128.0.64/26  |        64 |         59 | ALB / ingress (AZ2)    |
| Public Subnet 3  | 10.128.0.128/26 |        64 |         59 | ALB / ingress (AZ3)    |
| Runner Subnet    | 10.128.128.0/24 |       256 |        251 | Dedicated runner (AZ1) |
| Private Subnet 1 | 10.128.130.0/24 |       256 |        251 | EKS workloads (AZ1)    |
| Private Subnet 2 | 10.128.132.0/24 |       256 |        251 | EKS workloads (AZ2)    |
| Private Subnet 3 | 10.128.134.0/24 |       256 |        251 | EKS workloads (AZ3)    |

<!-- prettier-ignore-start -->
> [NOTE!]
> AWS reserves 5 IPs per subnet (first 4 + last), so usable = total - 5.
<!-- prettier-ignore-end -->

**Default total usable IPs: 1,181** (177 public + 1,004 private/runner).

### Larger Private Subnets

If you need more IPs for EKS workloads (e.g. high pod density or many nodes), increase the private subnets from `/24`
(251 usable) to `/20` (4,091 usable each):

| Parameter          | Default         | Larger Value    | Usable IPs |
| ------------------ | --------------- | --------------- | ---------: |
| PrivateSubnet1CIDR | 10.128.130.0/24 | 10.128.16.0/20  |      4,091 |
| PrivateSubnet2CIDR | 10.128.132.0/24 | 10.128.32.0/20  |      4,091 |
| PrivateSubnet3CIDR | 10.128.134.0/24 | 10.128.48.0/20  |      4,091 |
| RunnerSubnetCIDR   | 10.128.128.0/24 | 10.128.128.0/24 |        251 |

This brings private/runner usable IPs to **12,524** while staying within the `/16` VPC range. Public subnets can remain
at `/26` since they only host load balancers.

## Outputs

| Name           | Description                                  | Export |
| -------------- | -------------------------------------------- | ------ |
| VPC            | The VPC.                                     |        |
| PublicSubnets  | A list of the public subnets.                |        |
| PrivateSubnets | A list of the private subnets.               |        |
| RunnerSubnet   | The dedicated private subnet for the runner. |        |
