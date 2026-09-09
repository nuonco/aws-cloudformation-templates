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
| EnableTelemetryIngress | Create the private runner OTLP HTTP endpoint.                                       |           String            |                                        false                                        | true, false    |
| VpcId               | VPC containing the runner and endpoint; required when telemetry ingress is enabled.    |           String            |                                                                                     |                |
| TelemetrySourcePrefixListId | IPv4 prefix list allowed to send telemetry; required when telemetry ingress is enabled. | String | | |

`EnableTelemetryIngress` controls creation of the private, plaintext OTLP endpoint on TCP port 4318. It is separate from the runner collector's runtime enablement toggle, so both must be enabled for ingestion to succeed.

## Outputs

| Name                  | Description                                                     | Export |
| --------------------- | --------------------------------------------------------------- | ------ |
| ASG                   | The runner ASG.                                                 |        |
| RunnerInstanceRole    | The role used by the instances managed by the Runner ASG        |        |
| RunnerInstanceRoleARN | The ARN of role used by the instances managed by the Runner ASG |        |
| TelemetryEndpoint     | Private OTLP HTTP URL, or an empty string when disabled.         |        |

With a compatible Nuon control plane and a VPC template exposing `VpcIpv4PrefixListId`, the parent install stack exposes
`EnableTelemetryIngress` under Runner Configuration and supplies the VPC ID and prefix list automatically. This works
with both managed and BYO VPC templates; no telemetry-specific network input is needed. The endpoint is
also available to component configuration as `{{ .nuon.install_stack.outputs.telemetry_endpoint }}`. For example:

```toml
[env_vars]
OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
OTEL_EXPORTER_OTLP_ENDPOINT = "{{ .nuon.install_stack.outputs.telemetry_endpoint }}"
```

The internal NLB uses the runner's private subnet and accepts port 4318 from the VPC IPv4 prefix list. Its DNS name remains stable
when the ASG replaces the runner. An empty output means no endpoint is provisioned; only configure producers when an
endpoint is present. Both the runner and VPC templates must be upgraded to versions containing telemetry ingress support.
