# Scripts

### validate.sh

Use the aws-cli to validate cloudformation templates. Useful for identifying errors.

### validate_templates.py

Use the python cfn library to validate cloudformation templates. Necessaery to identify duplicate key errors which may
pass the aws cli check, but cause issues in ctl-api when the template is parsed.

### inspect_egress_domains.py

Inspect a domain or URL and print the `EgressAllowedDomains` values that should be added for the firewall-enabled VPC
stacks in this repository.

Examples:

```bash
uv run scripts/inspect_egress_domains.py aws.github.io
uv run scripts/inspect_egress_domains.py https://aws.github.io/eks-charts/index.yaml
```

### publish.sh

Upload `*/stack.yaml` files to the `nuon-artifacts` bucket under
`aws-cloudformation-templates/<subpath>/<stack>/stack.yaml`. Called by the `release` and `preview` workflows.

Publishes every stack by default (releases). Pass stack directories as trailing arguments
(e.g. `runner/asg vpc/eks/default`) to publish only those. The `preview` workflow uses
`dorny/paths-filter` to pass only stacks whose `stack.yaml` changed in the PR.
