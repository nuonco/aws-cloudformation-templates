# Runner ASG

Under no circumstances should this be used for anything other than debugging the runner VM.

## Parameters

| Name                | Description                                                                            |            Type             |                                       Default                                       | Allowed Values |
| ------------------- | -------------------------------------------------------------------------------------- | :-------------------------: | :---------------------------------------------------------------------------------: | :------------- |
| InstallId           | The install ID                                                                         |           String            |                                                                                     |                |
| InstanceType        | EC2 instance type for the runner                                                       |           String            |                                     t3a.medium                                      |                |
| KeyName             | SSH key pair for the runner instances                                                  | AWS::EC2::KeyPair::KeyName  |                                                                                     |                |
| RootVolumeSize      | Size of the root EBS volume in GB                                                      |           Number            |                                         30                                          |                |
| RunnerApiToken      | API token for the runner                                                               |           String            |                                                                                     |                |
| RunnerApiUrl        | API URL for the runner                                                                 |           String            |                               https://runner.nuon.co                                |                |
| RunnerEgressGroupId | The security group for the runner instance that allows outbound traffic.               | AWS::EC2::SecurityGroup::Id |                                                                                     |                |
| RunnerId            | The runner ID                                                                          |           String            |                                                                                     |                |
| RunnerInitScriptUrl | URL for the init script that is added to the use data for the Runner ASG VM instances. |           String            | https://raw.githubusercontent.com/nuonco/runner/refs/heads/main/scripts/aws/init.sh |                |
| SSHCidr             | CIDR range allowed to SSH into runner instances                                        |           String            |                                      0.0.0.0/0                                      |                |
| SubnetId            | The subnet on which the app will run within the selected VPC.                          |    AWS::EC2::Subnet::Id     |                                                                                     |                |
| VpcId               | The VPC in which to create the SSH security group                                      |      AWS::EC2::VPC::Id      |                                                                                     |                |

## Outputs

| Name                     | Description                                                     | Export |
| ------------------------ | --------------------------------------------------------------- | ------ |
| ASG                      | The runner ASG.                                                 |        |
| RunnerInstanceRole       | The role used by the instances managed by the Runner ASG        |        |
| RunnerInstanceRoleARN    | The ARN of role used by the instances managed by the Runner ASG |        |
| RunnerSSHSecurityGroupId | The ID of the SSH security group for runner instances           |        |
