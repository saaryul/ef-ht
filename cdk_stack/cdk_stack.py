from aws_cdk import (
    Stack,
    aws_logs as logs,
    aws_sns as sns,
    CfnOutput 
)
from constructs import Construct

class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create CloudWatch Log Group
        logs.LogGroup(self, "CSVAgentLogs", log_group_name="CSV_Agent_Logs")

        # Create SNS Topic for alerts
        sns_topic = sns.Topic(self, "CSVAgentAlerts", topic_name="CSV_Agent_Alerts")

        # Output SNS ARN
        CfnOutput(self, "SnsTopicArn", value=sns_topic.topic_arn) 
