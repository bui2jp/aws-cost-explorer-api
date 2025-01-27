import json
import boto3
import os
from botocore.exceptions import ClientError
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
    """Cost Report Lambda function
    """

    cost_report, total_cost = get_cost_report()
    print(cost_report)
    print(total_cost)
    # {"message": "cost_report", "cost_report": [[{"service": "Amazon Kinesis", "amount": 2.7, "unit": "USD"}, {"service": "Amazon Virtual Private Cloud", "amount": 2.09, "unit": "USD"}, {"service": "AWS Identity and Access Management Access Analyzer", "amount": 1.0, "unit": "USD"}, {"service": "Amazon Route 53", "amount": 0.5, "unit": "USD"}, {"service": "Tax", "amount": 0.66, "unit": "USD"}], 6.95]}

    message_body = "今月のAWSの利用料金: " + str(total_cost) + " USD"
    # SNSに通知
    notify_sns(message_body)
    return {
        "statusCode": 200,
        "body": message_body,
        # "body": json.dumps(
        #     {
        #         "message": "今月のAWSの利用料金",
        #         "total_cost (USD)": total_cost,
        #         "cost_report (USD)": cost_report,
        #     }
        # ),
    }

def get_cost_report():
    """Cost Report Lambda function

    """
    client = boto3.client('ce')

    # current month
    end = datetime.now(timezone.utc).date()
    start = end.replace(day=1)

    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        # print(response)
    except Exception as e:
        print('client.get_cost_and_usage exception' + str(e))
        return []

    # Amountが0.1以上のモノだけを抽出
    cost_data = []
    for group in response['ResultsByTime'][0]['Groups']:
        service = group['Keys'][0]
        amount_usd = float(group['Metrics']['UnblendedCost']['Amount'])
        if amount_usd >= 0.1:
            cost_data.append({
                'service': service,
                'amount': round(amount_usd, 2),  # 少数代２位まで
                'unit': group['Metrics']['UnblendedCost']['Unit']
            })
    # 降順にsort by Amount Taxは一番最後に表示
    # cost_data.sort(key=lambda x: x['amount'], reverse=True)
    cost_data.sort(key=lambda x: (x['service'] == 'Tax', -x['amount']))

    # print(cost_data)
    # [
    #     {'service': 'Amazon Kinesis', 'amount': 1.7763626168, 'unit': 'USD'},
    #     {'service': 'Amazon Virtual Private Cloud', 'amount': 1.743233335, 'unit': 'USD'},
    #     {'service': 'AWS Identity and Access Management Access Analyzer', 'amount': 1.002, 'unit': 'USD'},
    #     {'service': 'Tax', 'amount': 0.51, 'unit': 'USD'},
    #     {'service': 'Amazon Route 53', 'amount': 0.50076, 'unit': 'USD'}
    # ]    
    total_amount = sum([data['amount'] for data in cost_data])
    
    return cost_data, total_amount


def notify_sns(message):
    """SNSに通知
    """
    try:
        sns = boto3.client('sns')
        # sns_topic_arn = os.environ['SNS_TOPIC_ARN']
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN', 'Please set SNS_TOPIC_ARN') #arn:aws:sns:ap-northeast-1:049777008631:aws-cost-report-CostReportSNSTopic-xxxxxx

        print('sns_topic_arn: ' + sns_topic_arn)
        response = sns.publish(
            TopicArn=sns_topic_arn,
            # Message=json.dumps(message),
            Message=message,
            Subject='Daily Cost Report',
        )
        print(response)
    except ClientError as e:
        print('sns.publish ClientError' + str(e))
        return
    except Exception as e:
        print('sns.publish exception' + str(e))
        return
    