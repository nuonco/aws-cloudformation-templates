# VPC stack templates for EKS

These VPC CF Stacks have a parameter `ClusterName`. Typically, a vendor defines an input `cluster_name` which is then
passed to the stack automatically by the nuon control plane. This way, the VPC is pre-tagged for use by the cluster.

This is maintained for historical purposes. At the time of writing, the tagging is managed by the eks sandbox terraform
meaning we no longer have an explicit need for the automated tagging that takes place here.

Tagging in the terraform is preferable and sometimes required as is in the case when the eks sandboxes are deployed to
an existing vpc.

The EKS VPC templates also support the optional Route 53 DNS firewall used by the non-EKS VPC stacks. Set
`EnableFirewall=true` and provide `EgressAllowedDomains` to allowlist outbound DNS when needed.
