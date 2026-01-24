# Scripts

### validate.sh

Use the aws-cli to validate cloudformation templates. Useful for identifying errors.

### validate_templates.py

Use the python cfn library to validate cloudformation templates. Necessaery to identify duplicate key errors which may
pass the aws cli check, but cause issues in ctl-api when the template is parsed.
