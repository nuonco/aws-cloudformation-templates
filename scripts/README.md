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
