import json
import boto3
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
    """Cost Report Lambda function
    """

    cost_report = get_cost_report()
    print(cost_report)
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world docker",
                "cost_report": cost_report,
            }
        ),
    }

def get_cost_report():
    """Cost Report Lambda function

    """
    client = boto3.client('ce')

    # current month
    end = datetime.now(timezone.utc).date()
    start = end.replace(day=1)

    # response = client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': start.strftime('%Y-%m-%d'),
    #         'End': end.strftime('%Y-%m-%d')
    #     },
    #     Granularity='MONTHLY',
    #     Metrics=['UnblendedCost']
    # )
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
    print(response)
    # {
    #     'GroupDefinitions': [
    #         {'Type': 'DIMENSION', 'Key': 'SERVICE'}
    #     ],
    #     'ResultsByTime': [
    #         {
    #             'TimePeriod': {'Start': '2025-01-01', 'End': '2025-01-24'},
    #             'Total': {},
    #             'Groups': [
    #                 {
    #                     'Keys': ['AWS CloudFormation'],
    #                     'Metrics': {'UnblendedCost': {'Amount': '0', 'Unit': 'USD'}}
    #                 },
    #                 {
    #                     'Keys': ['AWS CloudShell'],
    #                     'Metrics': {'UnblendedCost': {'Amount': '0.0000004268', 'Unit': 'USD'}}
    #                 },

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