import aws_cdk as cdk
from infra_stack import InfraStack

app = cdk.App()
InfraStack(app, "CSVInfraStack")
app.synth()
