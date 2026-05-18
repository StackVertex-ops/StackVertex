"""Customer Metrics Service - Kosten & Metriken für Customer Deployments.

Zeigt Kunden ihre Infrastructure Kosten und Performance Metriken.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import boto3


class CustomerMetricsService:
    """Service für Customer Deployment Metriken & Kosten."""

    def __init__(self):
        self.ce_client = boto3.client('ce')  # Cost Explorer
        self.cloudwatch = boto3.client('cloudwatch')

    async def get_deployment_costs(
        self,
        deployment_id: str,
        customer_id: str,
        period_days: int = 30
    ) -> dict:
        """
        Holt Kosten für ein Customer Deployment.

        Nutzt AWS Cost Explorer API mit Resource Tags.
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=period_days)

        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.isoformat(),
                    'End': end_date.isoformat()
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Tags': {
                        'Key': 'DeploymentId',
                        'Values': [deployment_id]
                    }
                }
            )

            # Parse Results
            daily_costs = []
            total_cost = Decimal('0')

            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                amount = Decimal(result['Total']['UnblendedCost']['Amount'])
                daily_costs.append({
                    'date': date,
                    'cost': float(amount)
                })
                total_cost += amount

            # Forecast nächster Monat
            forecast = await self._forecast_costs(deployment_id)

            return {
                'deployment_id': deployment_id,
                'period_days': period_days,
                'total_cost': float(total_cost),
                'currency': 'USD',
                'daily_costs': daily_costs,
                'forecast_next_month': forecast,
                'cost_breakdown': await self._get_cost_breakdown(deployment_id)
            }

        except Exception:
            # Fallback: Schätze Kosten basierend auf Resources
            return await self._estimate_costs(deployment_id)

    async def _get_cost_breakdown(self, deployment_id: str) -> dict:
        """Kosten-Breakdown nach Service."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)

        response = self.ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.isoformat(),
                'End': end_date.isoformat()
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            Filter={
                'Tags': {
                    'Key': 'DeploymentId',
                    'Values': [deployment_id]
                }
            },
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )

        breakdown = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                breakdown[service] = cost

        return breakdown

    async def _forecast_costs(self, deployment_id: str) -> float:
        """Forecast für nächsten Monat."""
        try:
            end_date = (datetime.utcnow() + timedelta(days=30)).date()
            start_date = datetime.utcnow().date()

            response = self.ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.isoformat(),
                    'End': end_date.isoformat()
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY',
                Filter={
                    'Tags': {
                        'Key': 'DeploymentId',
                        'Values': [deployment_id]
                    }
                }
            )

            forecast = float(response['Total']['Amount'])
            return round(forecast, 2)

        except Exception:
            # Kein Forecast verfügbar - nutze aktuellen Trend
            return 0.0

    async def _estimate_costs(self, deployment_id: str) -> dict:
        """
        Schätze Kosten wenn Cost Explorer nicht verfügbar.

        Basiert auf deployed Resources und Pricing.
        """
        # TODO: Implementiere Resource-based Cost Estimation
        # - EC2: instance_type → hourly rate × hours
        # - RDS: instance_class → hourly rate × hours
        # - S3: storage GB × $0.023
        # etc.

        return {
            'deployment_id': deployment_id,
            'estimated': True,
            'total_cost': 0.0,
            'message': 'Cost tracking not yet available for new deployments'
        }

    async def get_deployment_metrics(
        self,
        deployment_id: str,
        metric_period_hours: int = 24
    ) -> dict:
        """
        Holt Performance Metriken für Customer Deployment.

        Zeigt:
        - EC2 CPU/Memory
        - RDS Connections/CPU
        - ALB Requests
        - S3 Storage
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=metric_period_hours)

        metrics = {}

        # EC2 Metrics
        ec2_metrics = await self._get_ec2_metrics(
            deployment_id, start_time, end_time
        )
        if ec2_metrics:
            metrics['ec2'] = ec2_metrics

        # RDS Metrics
        rds_metrics = await self._get_rds_metrics(
            deployment_id, start_time, end_time
        )
        if rds_metrics:
            metrics['rds'] = rds_metrics

        # ALB Metrics
        alb_metrics = await self._get_alb_metrics(
            deployment_id, start_time, end_time
        )
        if alb_metrics:
            metrics['alb'] = alb_metrics

        # S3 Storage
        s3_metrics = await self._get_s3_metrics(deployment_id)
        if s3_metrics:
            metrics['s3'] = s3_metrics

        return {
            'deployment_id': deployment_id,
            'period_hours': metric_period_hours,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics
        }

    async def _get_ec2_metrics(
        self,
        deployment_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> dict | None:
        """EC2 CPU & Network Metrics."""
        try:
            # Get EC2 Instance IDs for this deployment
            ec2 = boto3.client('ec2')
            instances = ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:DeploymentId', 'Values': [deployment_id]},
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )

            if not instances['Reservations']:
                return None

            instance_id = instances['Reservations'][0]['Instances'][0]['InstanceId']

            # Get CloudWatch Metrics
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average', 'Maximum']
            )

            datapoints = sorted(cpu_response['Datapoints'], key=lambda x: x['Timestamp'])

            if not datapoints:
                return {'cpu_percent': 0, 'status': 'no_data'}

            latest = datapoints[-1]

            return {
                'instance_id': instance_id,
                'cpu_percent': round(latest['Average'], 2),
                'cpu_max': round(latest['Maximum'], 2),
                'datapoints': [
                    {
                        'timestamp': dp['Timestamp'].isoformat(),
                        'cpu': round(dp['Average'], 2)
                    }
                    for dp in datapoints
                ]
            }

        except Exception as e:
            return {'error': str(e)}

    async def _get_rds_metrics(
        self,
        deployment_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> dict | None:
        """RDS CPU, Connections, Storage Metrics."""
        try:
            # Get RDS Instance for deployment
            rds = boto3.client('rds')
            instances = rds.describe_db_instances()

            db_instance = None
            for instance in instances['DBInstances']:
                tags = rds.list_tags_for_resource(
                    ResourceName=instance['DBInstanceArn']
                )['TagList']

                for tag in tags:
                    if tag['Key'] == 'DeploymentId' and tag['Value'] == deployment_id:
                        db_instance = instance
                        break

            if not db_instance:
                return None

            db_id = db_instance['DBInstanceIdentifier']

            # CPU
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )

            # Connections
            conn_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='DatabaseConnections',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )

            cpu_data = sorted(cpu_response['Datapoints'], key=lambda x: x['Timestamp'])
            conn_data = sorted(conn_response['Datapoints'], key=lambda x: x['Timestamp'])

            return {
                'db_instance_id': db_id,
                'cpu_percent': round(cpu_data[-1]['Average'], 2) if cpu_data else 0,
                'connections_current': int(conn_data[-1]['Average']) if conn_data else 0,
                'connections_max': int(conn_data[-1]['Maximum']) if conn_data else 0,
                'storage_gb': round(db_instance['AllocatedStorage'], 2)
            }

        except Exception as e:
            return {'error': str(e)}

    async def _get_alb_metrics(
        self,
        deployment_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> dict | None:
        """Application Load Balancer Metrics."""
        try:
            # Get ALB for deployment
            elb = boto3.client('elbv2')
            load_balancers = elb.describe_load_balancers()

            alb_arn = None
            for lb in load_balancers['LoadBalancers']:
                tags = elb.describe_tags(ResourceArns=[lb['LoadBalancerArn']])['TagDescriptions'][0]['Tags']

                for tag in tags:
                    if tag['Key'] == 'DeploymentId' and tag['Value'] == deployment_id:
                        alb_arn = lb['LoadBalancerArn']
                        break

            if not alb_arn:
                return None

            # Request Count
            requests = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='RequestCount',
                Dimensions=[{'Name': 'LoadBalancer', 'Value': alb_arn.split('/')[-1]}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )

            total_requests = sum(dp['Sum'] for dp in requests['Datapoints'])

            return {
                'alb_arn': alb_arn,
                'total_requests': int(total_requests),
                'requests_per_hour': int(total_requests / 24) if total_requests else 0
            }

        except Exception:
            return None

    async def _get_s3_metrics(self, deployment_id: str) -> dict | None:
        """S3 Storage Metrics."""
        try:
            s3 = boto3.client('s3')
            cloudwatch = boto3.client('cloudwatch')

            # Get S3 Buckets for deployment
            buckets = s3.list_buckets()['Buckets']

            deployment_buckets = []
            for bucket in buckets:
                try:
                    tags = s3.get_bucket_tagging(Bucket=bucket['Name'])['TagSet']
                    for tag in tags:
                        if tag['Key'] == 'DeploymentId' and tag['Value'] == deployment_id:
                            deployment_buckets.append(bucket['Name'])
                except:
                    continue

            if not deployment_buckets:
                return None

            total_size = 0
            for bucket_name in deployment_buckets:
                # Get latest storage metrics
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/S3',
                    MetricName='BucketSizeBytes',
                    Dimensions=[
                        {'Name': 'BucketName', 'Value': bucket_name},
                        {'Name': 'StorageType', 'Value': 'StandardStorage'}
                    ],
                    StartTime=datetime.utcnow() - timedelta(days=2),
                    EndTime=datetime.utcnow(),
                    Period=86400,  # Daily
                    Statistics=['Average']
                )

                if response['Datapoints']:
                    latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                    total_size += latest['Average']

            return {
                'buckets': deployment_buckets,
                'total_size_bytes': int(total_size),
                'total_size_gb': round(total_size / (1024**3), 2)
            }

        except Exception:
            return None

    async def get_deployment_uptime(self, deployment_id: str) -> dict:
        """Calculate deployment uptime percentage."""
        # Check CloudWatch Alarms für dieses Deployment
        cloudwatch = boto3.client('cloudwatch')

        alarms = cloudwatch.describe_alarms(
            AlarmNamePrefix=f'deployment-{deployment_id}'
        )

        total_alarms = len(alarms['MetricAlarms'])
        alarm_count = sum(
            1 for alarm in alarms['MetricAlarms']
            if alarm['StateValue'] == 'ALARM'
        )

        ok_count = sum(
            1 for alarm in alarms['MetricAlarms']
            if alarm['StateValue'] == 'OK'
        )

        uptime_percent = (ok_count / total_alarms * 100) if total_alarms > 0 else 100.0

        return {
            'deployment_id': deployment_id,
            'uptime_percent': round(uptime_percent, 2),
            'total_alarms': total_alarms,
            'alarms_active': alarm_count,
            'status': 'healthy' if uptime_percent >= 99.0 else 'degraded'
        }
