#!/bin/bash

set -e
set -o pipefail
set -u

# Given an AWS profile and region as env vars, and a VPC ID as an arg,
# list the VPC, its public subnets, and its private subnets.
# For the private subnets, identify if they are able to route to 0.0.0.0/0
# via NAT Gateway or Internet Gateway and include that information as well.
#
# Environment variables:
#   AWS_PROFILE - AWS profile to use (optional)
#   AWS_REGION  - AWS region to use (required)
#
# Usage:
#   AWS_REGION=us-east-1 ./vpc-preflight.sh vpc-0123456789abcdef0

usage() {
    echo "Usage: AWS_REGION=<region> $0 <vpc-id>"
    echo ""
    echo "Environment variables:"
    echo "  AWS_PROFILE - AWS profile to use (optional)"
    echo "  AWS_REGION  - AWS region to use (required)"
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

VPC_ID="$1"

if [[ -z "${AWS_REGION:-}" ]]; then
    echo "Error: AWS_REGION environment variable is required"
    usage
fi

AWS_OPTS="--region ${AWS_REGION}"
if [[ -n "${AWS_PROFILE:-}" ]]; then
    AWS_OPTS="${AWS_OPTS} --profile ${AWS_PROFILE}"
fi

echo "=========================================="
echo "VPC Preflight Check"
echo "=========================================="
echo "VPC ID:  ${VPC_ID}"
echo "Region:  ${AWS_REGION}"
echo "Profile: ${AWS_PROFILE:-default}"
echo ""

# Verify VPC exists and get details
echo "Fetching VPC details..."
VPC_INFO=$(aws ec2 describe-vpcs ${AWS_OPTS} --vpc-ids "${VPC_ID}" --query 'Vpcs[0]' --output json 2>/dev/null) || {
    echo "Error: VPC ${VPC_ID} not found in region ${AWS_REGION}"
    exit 1
}

VPC_CIDR=$(echo "${VPC_INFO}" | jq -r '.CidrBlock')
VPC_NAME=$(echo "${VPC_INFO}" | jq -r '.Tags[]? | select(.Key=="Name") | .Value // "N/A"')
echo "VPC Name: ${VPC_NAME}"
echo "VPC CIDR: ${VPC_CIDR}"
echo ""

# Get all subnets in the VPC
echo "Fetching subnets..."
SUBNETS=$(aws ec2 describe-subnets ${AWS_OPTS} \
    --filters "Name=vpc-id,Values=${VPC_ID}" \
    --query 'Subnets[*]' \
    --output json)

SUBNET_COUNT=$(echo "${SUBNETS}" | jq 'length')
echo "Found ${SUBNET_COUNT} subnets"
echo ""

# Get all route tables in the VPC
ROUTE_TABLES=$(aws ec2 describe-route-tables ${AWS_OPTS} \
    --filters "Name=vpc-id,Values=${VPC_ID}" \
    --output json)

# Get the main route table for the VPC
MAIN_RT_ID=$(echo "${ROUTE_TABLES}" | jq -r '.RouteTables[] | select(.Associations[]?.Main == true) | .RouteTableId')

# Function to get route table for a subnet
get_route_table_for_subnet() {
    local subnet_id="$1"
    local rt_id

    # Check for explicit association
    rt_id=$(echo "${ROUTE_TABLES}" | jq -r --arg sid "${subnet_id}" \
        '.RouteTables[] | select(.Associations[]?.SubnetId == $sid) | .RouteTableId' | head -1)

    # Fall back to main route table if no explicit association
    if [[ -z "${rt_id}" ]]; then
        rt_id="${MAIN_RT_ID}"
    fi

    echo "${rt_id}"
}

# Function to check if route table has internet access and how
check_internet_access() {
    local rt_id="$1"
    local route_info

    route_info=$(echo "${ROUTE_TABLES}" | jq -r --arg rtid "${rt_id}" \
        '.RouteTables[] | select(.RouteTableId == $rtid) | .Routes[] | select(.DestinationCidrBlock == "0.0.0.0/0")')

    if [[ -z "${route_info}" ]]; then
        echo "none"
        return
    fi

    local gw_id=$(echo "${route_info}" | jq -r '.GatewayId // empty')
    local nat_id=$(echo "${route_info}" | jq -r '.NatGatewayId // empty')

    if [[ -n "${nat_id}" && "${nat_id}" != "null" ]]; then
        echo "nat:${nat_id}"
    elif [[ -n "${gw_id}" && "${gw_id}" == igw-* ]]; then
        echo "igw:${gw_id}"
    else
        echo "none"
    fi
}

# Classify subnets
PUBLIC_SUBNETS=()
PRIVATE_SUBNETS_WITH_NAT=()
PRIVATE_SUBNETS_NO_INTERNET=()

echo "Analyzing subnets..."
echo ""

for row in $(echo "${SUBNETS}" | jq -r '.[] | @base64'); do
    _jq() {
        echo "${row}" | base64 --decode | jq -r "${1}"
    }

    subnet_id=$(_jq '.SubnetId')
    subnet_cidr=$(_jq '.CidrBlock')
    subnet_az=$(_jq '.AvailabilityZone')
    subnet_name=$(_jq '.Tags[]? | select(.Key=="Name") | .Value // "N/A"')
    map_public_ip=$(_jq '.MapPublicIpOnLaunch')

    rt_id=$(get_route_table_for_subnet "${subnet_id}")
    internet_access=$(check_internet_access "${rt_id}")

    # Classify: public if has IGW route, private otherwise
    if [[ "${internet_access}" == igw:* ]]; then
        PUBLIC_SUBNETS+=("${subnet_id}")
        subnet_type="PUBLIC"
        internet_info="via ${internet_access#igw:}"
    elif [[ "${internet_access}" == nat:* ]]; then
        PRIVATE_SUBNETS_WITH_NAT+=("${subnet_id}")
        subnet_type="PRIVATE"
        internet_info="outbound via NAT ${internet_access#nat:}"
    else
        PRIVATE_SUBNETS_NO_INTERNET+=("${subnet_id}")
        subnet_type="PRIVATE"
        internet_info="NO INTERNET ACCESS"
    fi

    printf "  %-24s %-12s %-18s %s\n" "${subnet_id}" "${subnet_az}" "${subnet_type}" "${internet_info}"
    printf "    Name: %s\n" "${subnet_name}"
    printf "    CIDR: %s\n" "${subnet_cidr}"
done

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Public Subnets (${#PUBLIC_SUBNETS[@]}):"
if [[ ${#PUBLIC_SUBNETS[@]} -gt 0 ]]; then
    echo "  $(IFS=,; echo "${PUBLIC_SUBNETS[*]}")"
else
    echo "  (none)"
fi

echo ""
echo "Private Subnets with NAT (${#PRIVATE_SUBNETS_WITH_NAT[@]}):"
if [[ ${#PRIVATE_SUBNETS_WITH_NAT[@]} -gt 0 ]]; then
    echo "  $(IFS=,; echo "${PRIVATE_SUBNETS_WITH_NAT[*]}")"
else
    echo "  (none)"
fi

echo ""
echo "Private Subnets without Internet (${#PRIVATE_SUBNETS_NO_INTERNET[@]}):"
if [[ ${#PRIVATE_SUBNETS_NO_INTERNET[@]} -gt 0 ]]; then
    echo "  $(IFS=,; echo "${PRIVATE_SUBNETS_NO_INTERNET[*]}")"
else
    echo "  (none)"
fi

echo ""
echo "=========================================="
echo "Suggested CloudFormation Parameters"
echo "=========================================="
echo ""
echo "VpcID=${VPC_ID}"

if [[ ${#PUBLIC_SUBNETS[@]} -gt 0 ]]; then
    echo "PublicSubnetIDs=$(IFS=,; echo "${PUBLIC_SUBNETS[*]}")"
else
    echo "# WARNING: No public subnets found"
    echo "PublicSubnetIDs="
fi

if [[ ${#PRIVATE_SUBNETS_WITH_NAT[@]} -gt 0 ]]; then
    echo "PrivateSubnetIDs=$(IFS=,; echo "${PRIVATE_SUBNETS_WITH_NAT[*]}")"
else
    echo "# WARNING: No private subnets with NAT found"
    echo "PrivateSubnetIDs="
fi

echo ""
echo "# Runner subnet (pick one private subnet with NAT access):"
if [[ ${#PRIVATE_SUBNETS_WITH_NAT[@]} -gt 0 ]]; then
    echo "RunnerSubnetID=${PRIVATE_SUBNETS_WITH_NAT[0]}"
else
    echo "# WARNING: No suitable runner subnet found (needs NAT access)"
    echo "RunnerSubnetID="
fi
