"""
Cloud provider integration module for Proxmox NLI.
Handles integration with major cloud providers like AWS, Azure, and GCP.
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class CloudProvider(ABC):
    """Base class for cloud provider integrations"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize cloud provider with config"""
        self.config = config or {}
        self.provider_id = str(uuid.uuid4())
        self.connected = False
        self.last_error = None
    
    @abstractmethod
    def connect(self) -> Dict[str, Any]:
        """Connect to the cloud provider"""
        pass
    
    @abstractmethod
    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from the cloud provider"""
        pass
    
    @abstractmethod
    def get_resources(self, resource_type: str = None) -> Dict[str, Any]:
        """Get resources from the cloud provider"""
        pass
    
    @abstractmethod
    def provision_resource(self, resource_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision a new resource in the cloud"""
        pass
    
    @abstractmethod
    def deprovision_resource(self, resource_id: str) -> Dict[str, Any]:
        """Deprovision a resource in the cloud"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert provider to dictionary for serialization"""
        return {
            "id": self.provider_id,
            "type": self.__class__.__name__,
            "connected": self.connected,
            "last_error": self.last_error
        }

class AWSCloudProvider(CloudProvider):
    """AWS cloud provider integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize AWS cloud provider
        
        Config should contain:
        - access_key: AWS access key
        - secret_key: AWS secret key
        - region: AWS region
        """
        super().__init__(config)
        self.session = None
    
    def connect(self) -> Dict[str, Any]:
        """Connect to AWS"""
        try:
            # Check if boto3 is available
            try:
                import boto3
            except ImportError:
                return {
                    "success": False,
                    "message": "boto3 package is not installed. Install with: pip install boto3"
                }
            
            # Get credentials from config
            access_key = self.config.get('access_key')
            secret_key = self.config.get('secret_key')
            region = self.config.get('region', 'us-east-1')
            
            if not access_key or not secret_key:
                return {
                    "success": False,
                    "message": "AWS credentials not provided in config"
                }
            
            # Create session
            self.session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Test connection by listing S3 buckets
            s3 = self.session.client('s3')
            s3.list_buckets()
            
            self.connected = True
            return {
                "success": True,
                "message": f"Connected to AWS in region {region}"
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error connecting to AWS: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to AWS: {str(e)}"
            }
    
    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from AWS"""
        self.session = None
        self.connected = False
        return {
            "success": True,
            "message": "Disconnected from AWS"
        }
    
    def get_resources(self, resource_type: str = None) -> Dict[str, Any]:
        """
        Get AWS resources
        
        Args:
            resource_type: Type of resource (ec2, s3, rds, etc.)
            
        Returns:
            Dict with resource information
        """
        if not self.connected or not self.session:
            return {
                "success": False,
                "message": "Not connected to AWS"
            }
        
        try:
            resources = {}
            
            # Get EC2 instances
            if not resource_type or resource_type.lower() == 'ec2':
                ec2 = self.session.client('ec2')
                instances = ec2.describe_instances()
                resources['ec2'] = []
                
                for reservation in instances.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        resources['ec2'].append({
                            'id': instance.get('InstanceId'),
                            'type': instance.get('InstanceType'),
                            'state': instance.get('State', {}).get('Name'),
                            'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                            'public_ip': instance.get('PublicIpAddress'),
                            'private_ip': instance.get('PrivateIpAddress')
                        })
            
            # Get S3 buckets
            if not resource_type or resource_type.lower() == 's3':
                s3 = self.session.client('s3')
                buckets = s3.list_buckets()
                resources['s3'] = []
                
                for bucket in buckets.get('Buckets', []):
                    resources['s3'].append({
                        'name': bucket.get('Name'),
                        'creation_date': bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None
                    })
            
            # Get RDS instances
            if not resource_type or resource_type.lower() == 'rds':
                rds = self.session.client('rds')
                db_instances = rds.describe_db_instances()
                resources['rds'] = []
                
                for db in db_instances.get('DBInstances', []):
                    resources['rds'].append({
                        'id': db.get('DBInstanceIdentifier'),
                        'engine': db.get('Engine'),
                        'status': db.get('DBInstanceStatus'),
                        'endpoint': db.get('Endpoint', {}).get('Address') if db.get('Endpoint') else None
                    })
            
            return {
                "success": True,
                "resources": resources
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error getting AWS resources: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting AWS resources: {str(e)}"
            }
    
    def provision_resource(self, resource_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provision a new AWS resource
        
        Args:
            resource_type: Type of resource (ec2, s3, etc.)
            config: Resource configuration
            
        Returns:
            Dict with provisioned resource details
        """
        if not self.connected or not self.session:
            return {
                "success": False,
                "message": "Not connected to AWS"
            }
        
        try:
            # Handle EC2 instances
            if resource_type.lower() == 'ec2':
                ec2 = self.session.client('ec2')
                
                # Get parameters
                image_id = config.get('image_id')
                instance_type = config.get('instance_type', 't2.micro')
                key_name = config.get('key_name')
                security_group_ids = config.get('security_group_ids', [])
                subnet_id = config.get('subnet_id')
                
                response = ec2.run_instances(
                    ImageId=image_id,
                    InstanceType=instance_type,
                    KeyName=key_name if key_name else None,
                    MaxCount=1,
                    MinCount=1,
                    SecurityGroupIds=security_group_ids if security_group_ids else None,
                    SubnetId=subnet_id if subnet_id else None
                )
                
                instance = response['Instances'][0]
                instance_id = instance['InstanceId']
                
                return {
                    "success": True,
                    "message": f"EC2 instance {instance_id} is being provisioned",
                    "resource": {
                        "type": "ec2",
                        "id": instance_id,
                        "details": instance
                    }
                }
            
            # Handle S3 buckets
            elif resource_type.lower() == 's3':
                s3 = self.session.client('s3')
                
                # Get parameters
                bucket_name = config.get('bucket_name')
                
                if not bucket_name:
                    return {
                        "success": False,
                        "message": "Bucket name not provided"
                    }
                
                s3.create_bucket(Bucket=bucket_name)
                
                return {
                    "success": True,
                    "message": f"S3 bucket {bucket_name} created",
                    "resource": {
                        "type": "s3",
                        "id": bucket_name
                    }
                }
            
            # Unsupported resource type
            else:
                return {
                    "success": False,
                    "message": f"Unsupported resource type: {resource_type}"
                }
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error provisioning AWS resource: {str(e)}")
            return {
                "success": False,
                "message": f"Error provisioning AWS resource: {str(e)}"
            }
    
    def deprovision_resource(self, resource_id: str) -> Dict[str, Any]:
        """
        Deprovision an AWS resource
        
        Args:
            resource_id: Resource ID (e.g., i-12345 for EC2)
            
        Returns:
            Dict with operation result
        """
        if not self.connected or not self.session:
            return {
                "success": False,
                "message": "Not connected to AWS"
            }
        
        try:
            # Try to determine resource type from ID
            if resource_id.startswith('i-'):
                # EC2 instance
                ec2 = self.session.client('ec2')
                ec2.terminate_instances(InstanceIds=[resource_id])
                
                return {
                    "success": True,
                    "message": f"EC2 instance {resource_id} is being terminated"
                }
            else:
                # Might be an S3 bucket
                try:
                    s3 = self.session.client('s3')
                    
                    # First delete all objects
                    bucket = self.session.resource('s3').Bucket(resource_id)
                    bucket.objects.all().delete()
                    
                    # Then delete the bucket
                    s3.delete_bucket(Bucket=resource_id)
                    
                    return {
                        "success": True,
                        "message": f"S3 bucket {resource_id} deleted"
                    }
                except Exception:
                    return {
                        "success": False,
                        "message": f"Could not determine resource type for ID: {resource_id}"
                    }
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error deprovisioning AWS resource: {str(e)}")
            return {
                "success": False,
                "message": f"Error deprovisioning AWS resource: {str(e)}"
            }

class AzureCloudProvider(CloudProvider):
    """Azure cloud provider integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Azure cloud provider
        
        Config should contain:
        - client_id: Azure client ID
        - client_secret: Azure client secret
        - tenant_id: Azure tenant ID
        - subscription_id: Azure subscription ID
        """
        super().__init__(config)
        self.client = None
    
    def connect(self) -> Dict[str, Any]:
        """Connect to Azure"""
        try:
            # Check if azure packages are available
            try:
                from azure.identity import ClientSecretCredential
                from azure.mgmt.resource import ResourceManagementClient
            except ImportError:
                return {
                    "success": False,
                    "message": "Azure SDK not installed. Install with: pip install azure-identity azure-mgmt-resource"
                }
            
            # Get credentials from config
            client_id = self.config.get('client_id')
            client_secret = self.config.get('client_secret')
            tenant_id = self.config.get('tenant_id')
            subscription_id = self.config.get('subscription_id')
            
            if not all([client_id, client_secret, tenant_id, subscription_id]):
                return {
                    "success": False,
                    "message": "Azure credentials not provided in config"
                }
            
            # Create credential
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Create resource client
            self.client = ResourceManagementClient(credential, subscription_id)
            
            # Test connection
            self.client.resource_groups.list()
            
            self.connected = True
            return {
                "success": True,
                "message": "Connected to Azure"
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error connecting to Azure: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Azure: {str(e)}"
            }
    
    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from Azure"""
        self.client = None
        self.connected = False
        return {
            "success": True,
            "message": "Disconnected from Azure"
        }
    
    def get_resources(self, resource_type: str = None) -> Dict[str, Any]:
        """Get resources from Azure"""
        if not self.connected or not self.client:
            return {
                "success": False,
                "message": "Not connected to Azure"
            }
        
        try:
            resources = {}
            
            # Get resource groups
            if not resource_type or resource_type.lower() == 'resource_group':
                resources['resource_groups'] = []
                for group in self.client.resource_groups.list():
                    resources['resource_groups'].append({
                        'id': group.id,
                        'name': group.name,
                        'location': group.location,
                        'properties': group.properties.__dict__ if group.properties else {}
                    })
            
            # Other resource types can be added here
            
            return {
                "success": True,
                "resources": resources
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error getting Azure resources: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Azure resources: {str(e)}"
            }
    
    def provision_resource(self, resource_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision a resource in Azure"""
        if not self.connected or not self.client:
            return {
                "success": False,
                "message": "Not connected to Azure"
            }
        
        try:
            # Handle resource groups
            if resource_type.lower() == 'resource_group':
                name = config.get('name')
                location = config.get('location', 'eastus')
                
                if not name:
                    return {
                        "success": False,
                        "message": "Resource group name not provided"
                    }
                
                resource_group = self.client.resource_groups.create_or_update(
                    name,
                    {"location": location}
                )
                
                return {
                    "success": True,
                    "message": f"Resource group {name} created",
                    "resource": {
                        "type": "resource_group",
                        "id": resource_group.id,
                        "name": resource_group.name
                    }
                }
            
            # Unsupported resource type
            else:
                return {
                    "success": False,
                    "message": f"Unsupported resource type: {resource_type}"
                }
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error provisioning Azure resource: {str(e)}")
            return {
                "success": False,
                "message": f"Error provisioning Azure resource: {str(e)}"
            }
    
    def deprovision_resource(self, resource_id: str) -> Dict[str, Any]:
        """Deprovision a resource in Azure"""
        if not self.connected or not self.client:
            return {
                "success": False,
                "message": "Not connected to Azure"
            }
        
        try:
            # Extract resource group name from ID
            if '/resourceGroups/' in resource_id:
                parts = resource_id.split('/resourceGroups/')
                if len(parts) > 1:
                    group_name = parts[1].split('/')[0]
                    
                    self.client.resource_groups.begin_delete(group_name)
                    
                    return {
                        "success": True,
                        "message": f"Resource group {group_name} is being deleted"
                    }
            
            return {
                "success": False,
                "message": f"Could not parse resource ID: {resource_id}"
            }
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error deprovisioning Azure resource: {str(e)}")
            return {
                "success": False,
                "message": f"Error deprovisioning Azure resource: {str(e)}"
            }

class GCPCloudProvider(CloudProvider):
    """Google Cloud Platform provider integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize GCP cloud provider
        
        Config should contain:
        - project_id: GCP project ID
        - credentials_file: Path to service account JSON file
        """
        super().__init__(config)
    
    def connect(self) -> Dict[str, Any]:
        """Connect to GCP"""
        try:
            # Check if google-cloud packages are available
            try:
                from google.cloud import storage
                from google.oauth2 import service_account
            except ImportError:
                return {
                    "success": False,
                    "message": "Google Cloud SDK not installed. Install with: pip install google-cloud-storage"
                }
            
            # Get credentials from config
            project_id = self.config.get('project_id')
            credentials_file = self.config.get('credentials_file')
            
            if not project_id:
                return {
                    "success": False,
                    "message": "GCP project ID not provided in config"
                }
            
            if not credentials_file or not os.path.isfile(credentials_file):
                return {
                    "success": False,
                    "message": f"GCP credentials file not found: {credentials_file}"
                }
            
            # Load credentials
            self.credentials = service_account.Credentials.from_service_account_file(credentials_file)
            self.project_id = project_id
            
            # Test connection with storage client
            storage_client = storage.Client(project=project_id, credentials=self.credentials)
            storage_client.list_buckets()
            
            self.connected = True
            return {
                "success": True,
                "message": f"Connected to GCP project {project_id}"
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error connecting to GCP: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to GCP: {str(e)}"
            }
    
    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from GCP"""
        self.credentials = None
        self.connected = False
        return {
            "success": True,
            "message": "Disconnected from GCP"
        }
    
    def get_resources(self, resource_type: str = None) -> Dict[str, Any]:
        """Get resources from GCP"""
        if not self.connected:
            return {
                "success": False,
                "message": "Not connected to GCP"
            }
        
        try:
            from google.cloud import storage
            
            resources = {}
            
            # Get storage buckets
            if not resource_type or resource_type.lower() == 'bucket':
                storage_client = storage.Client(project=self.project_id, credentials=self.credentials)
                buckets = storage_client.list_buckets()
                
                resources['buckets'] = []
                for bucket in buckets:
                    resources['buckets'].append({
                        'name': bucket.name,
                        'location': bucket.location,
                        'created': bucket.time_created.isoformat() if bucket.time_created else None
                    })
            
            # Other resource types would go here
            
            return {
                "success": True,
                "resources": resources
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error getting GCP resources: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting GCP resources: {str(e)}"
            }
    
    def provision_resource(self, resource_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision a resource in GCP"""
        if not self.connected:
            return {
                "success": False,
                "message": "Not connected to GCP"
            }
        
        try:
            from google.cloud import storage
            
            # Handle storage buckets
            if resource_type.lower() == 'bucket':
                bucket_name = config.get('name')
                location = config.get('location', 'us-central1')
                
                if not bucket_name:
                    return {
                        "success": False,
                        "message": "Bucket name not provided"
                    }
                
                storage_client = storage.Client(project=self.project_id, credentials=self.credentials)
                bucket = storage_client.create_bucket(bucket_name, location=location)
                
                return {
                    "success": True,
                    "message": f"GCP bucket {bucket_name} created",
                    "resource": {
                        "type": "bucket",
                        "name": bucket.name,
                        "location": bucket.location
                    }
                }
            
            # Unsupported resource type
            else:
                return {
                    "success": False,
                    "message": f"Unsupported resource type: {resource_type}"
                }
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error provisioning GCP resource: {str(e)}")
            return {
                "success": False,
                "message": f"Error provisioning GCP resource: {str(e)}"
            }
    
    def deprovision_resource(self, resource_id: str) -> Dict[str, Any]:
        """Deprovision a resource in GCP"""
        if not self.connected:
            return {
                "success": False,
                "message": "Not connected to GCP"
            }
        
        try:
            from google.cloud import storage
            
            # Handle storage buckets
            storage_client = storage.Client(project=self.project_id, credentials=self.credentials)
            
            try:
                bucket = storage_client.get_bucket(resource_id)
                bucket.delete(force=True)
                
                return {
                    "success": True,
                    "message": f"GCP bucket {resource_id} deleted"
                }
            except Exception:
                return {
                    "success": False,
                    "message": f"Resource not found or not a bucket: {resource_id}"
                }
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error deprovisioning GCP resource: {str(e)}")
            return {
                "success": False,
                "message": f"Error deprovisioning GCP resource: {str(e)}"
            }

def get_cloud_provider(provider_type: str, config: Dict[str, Any] = None) -> CloudProvider:
    """
    Factory function to get cloud provider instance
    
    Args:
        provider_type: Type of provider (aws, azure, gcp)
        config: Provider configuration
        
    Returns:
        CloudProvider instance
    """
    provider_type = provider_type.lower()
    
    if provider_type == 'aws':
        return AWSCloudProvider(config)
    elif provider_type == 'azure':
        return AzureCloudProvider(config)
    elif provider_type == 'gcp':
        return GCPCloudProvider(config)
    else:
        raise ValueError(f"Unsupported cloud provider: {provider_type}")