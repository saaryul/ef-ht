from aws_cdk import (
    core as cdk,
    aws_logs as logs,
    aws_sns as sns
)

class InfraStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create CloudWatch Log Group
        logs.LogGroup(self, "CSVAgentLogs", log_group_name="CSV_Agent_Logs")

        # Create SNS Topic for alerts
        sns_topic = sns.Topic(self, "CSVAgentAlerts", topic_name="CSV_Agent_Alerts")

        # Output SNS ARN
        cdk.CfnOutput(self, "SnsTopicArn", value=sns_topic.topic_arn)
