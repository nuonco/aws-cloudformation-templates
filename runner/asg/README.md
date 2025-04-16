# Runner ASG

## Parameters

| Name                | Description                                                              |            Type             |        Default         | Allowed Values |
| ------------------- | ------------------------------------------------------------------------ | :-------------------------: | :--------------------: | :------------- |
| RunnerApiUrl        | API URL for the runner                                                   |           String            | https://runner.nuon.co |                |
| InstanceType        | EC2 instance type for the runner                                         |           String            |       t3a.medium       |                |
| SubnetId            | The subnet on which the app will run within the selected VPC.            |    AWS::EC2::Subnet::Id     |                        |                |
| RunnerEgressGroupId | The security group for the runner instance that allows outbound traffic. | AWS::EC2::SecurityGroup::Id |                        |                |
| RunnerId            | The runner ID                                                            |           String            |                        |                |
| RunnerApiToken      | API token for the runner                                                 |           String            |                        |                |

## Outputs

| Name | Description     | Export |
| ---- | --------------- | ------ |
| ASG  | The runner ASG. |        |
