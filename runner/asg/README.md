# Runner ASG

## Parameters

| Name                | Description                                                                            |            Type             |                                       Default                                       | Allowed Values |
| ------------------- | -------------------------------------------------------------------------------------- | :-------------------------: | :---------------------------------------------------------------------------------: | :------------- |
| InstallId           | The install ID                                                                         |           String            |                                                                                     |                |
| InstanceType        | EC2 instance type for the runner                                                       |           String            |                                     t3a.medium                                      |                |
| RootVolumeSize      | Size of the root EBS volume in GB                                                      |           Number            |                                         30                                          |                |
| RunnerApiUrl        | API URL for the runner                                                                 |           String            |                               https://runner.nuon.co                                |                |
| RunnerEgressGroupId | The security group for the runner instance that allows outbound traffic.               | AWS::EC2::SecurityGroup::Id |                                                                                     |                |
| RunnerId            | The runner ID                                                                          |           String            |                                                                                     |                |
| RunnerInitScriptUrl | URL for the init script that is added to the use data for the Runner ASG VM instances. |           String            | https://raw.githubusercontent.com/nuonco/runner/refs/heads/main/scripts/aws/init.sh |                |
| SubnetId            | The subnet on which the app will run within the selected VPC.                          |    AWS::EC2::Subnet::Id     |                                                                                     |                |

## Outputs

| Name                  | Description                                                     | Export |
| --------------------- | --------------------------------------------------------------- | ------ |
| ASG                   | The runner ASG.                                                 |        |
| RunnerInstanceRole    | The role used by the instances managed by the Runner ASG        |        |
| RunnerInstanceRoleARN | The ARN of role used by the instances managed by the Runner ASG |        |
