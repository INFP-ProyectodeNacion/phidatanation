from typing import Optional, Any, Dict, List, Literal, Union

from phidata.infra.aws.api_client import AwsApiClient
from phidata.infra.aws.resource.base import AwsResource
from phidata.infra.aws.resource.ecs.cluster import EcsCluster
from phidata.infra.aws.resource.ecs.task_definition import EcsTaskDefinition
from phidata.utils.cli_console import print_info, print_error
from phidata.utils.log import logger


class EcsService(AwsResource):
    """
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html
    """

    resource_type = "EcsService"
    service_name = "ecs"

    # Name for the service.
    name: str
    # Name for the service.
    # Use name if not provided.
    ecs_service_name: Optional[str] = None

    # EcsCluster for the service.
    # Can be
    # - string: The short name or full Amazon Resource Name (ARN) of the cluster
    # - EcsCluster
    # If you do not specify a cluster, the default cluster is assumed.
    cluster: Optional[Union[EcsCluster, str]] = None

    # EcsTaskDefinition for the service.
    # Can be
    # - string: The family and revision (family:revision ) or full ARN of the task definition.
    # - EcsTaskDefinition
    # If a revision isn't specified, the latest ACTIVE revision is used.
    task_definition: Optional[Union[EcsTaskDefinition, str]] = None

    # A load balancer object representing the load balancers to use with your service.
    load_balancers: Optional[List[Dict[str, Any]]] = None
    service_registries: Optional[List[Dict[str, Any]]] = None
    # The number of instantiations of the specified task definition to place and keep running on your cluster.
    # This is required if schedulingStrategy is REPLICA or isn't specified.
    # If schedulingStrategy is DAEMON then this isn't required.
    desired_count: Optional[int] = None
    # An identifier that you provide to ensure the idempotency of the request. It must be unique and is case-sensitive.
    client_token: Optional[str] = None
    # The infrastructure that you run your service on.
    launch_type: Optional[Literal["EC2", "FARGATE", "EXTERNAL"]] = None
    # The capacity provider strategy to use for the service.
    capacity_provider_strategy: Optional[List[Dict[str, Any]]] = None
    platform_version: Optional[str] = None
    role: Optional[str] = None
    deployment_configuration: Optional[Dict[str, Any]] = None
    placement_constraints: Optional[List[Dict[str, Any]]] = None
    placement_strategy: Optional[List[Dict[str, Any]]] = None
    network_configuration: Optional[Dict[str, Any]] = None
    health_check_grace_period_seconds: Optional[int] = None
    scheduling_strategy: Optional[Literal["REPLICA", "DAEMON"]] = None
    deployment_controller: Optional[Dict[str, Any]] = None
    tags: Optional[List[Dict[str, Any]]] = None
    enable_ecsmanaged_tags: Optional[bool] = None
    propagate_tags: Optional[Literal["TASK_DEFINITION", "SERVICE", "NONE"]] = None
    enable_execute_command: Optional[bool] = None

    force_delete: Optional[bool] = None

    def get_ecs_service_name(self):
        return self.ecs_service_name or self.name

    def get_ecs_cluster_name(self):
        if self.cluster is not None:
            if isinstance(self.cluster, EcsCluster):
                return self.cluster.name
            else:
                return self.cluster

    def get_ecs_task_definition(self):
        if self.task_definition is not None:
            if isinstance(self.task_definition, EcsTaskDefinition):
                return self.task_definition.get_task_family()
            else:
                return self.task_definition

    def _create(self, aws_client: AwsApiClient) -> bool:
        """Create EcsService"""
        print_info(f"Creating {self.get_resource_type()}: {self.get_resource_name()}")

        # create a dict of args which are not null, otherwise aws type validation fails
        not_null_args: Dict[str, Any] = {}

        cluster_name = self.get_ecs_cluster_name()
        if cluster_name is not None:
            not_null_args["cluster"] = cluster_name
        if self.load_balancers is not None:
            not_null_args["loadBalancers"] = self.load_balancers
        if self.service_registries is not None:
            not_null_args["serviceRegistries"] = self.service_registries
        if self.desired_count is not None:
            not_null_args["desiredCount"] = self.desired_count
        if self.client_token is not None:
            not_null_args["clientToken"] = self.client_token
        if self.launch_type is not None:
            not_null_args["launchType"] = self.launch_type
        if self.capacity_provider_strategy is not None:
            not_null_args["capacityProviderStrategy"] = self.capacity_provider_strategy
        if self.platform_version is not None:
            not_null_args["platformVersion"] = self.platform_version
        if self.role is not None:
            not_null_args["role"] = self.role
        if self.deployment_configuration is not None:
            not_null_args["deploymentConfiguration"] = self.deployment_configuration
        if self.placement_constraints is not None:
            not_null_args["placementConstraints"] = self.placement_constraints
        if self.placement_strategy is not None:
            not_null_args["placementStrategy"] = self.placement_strategy
        if self.network_configuration is not None:
            not_null_args["networkConfiguration"] = self.network_configuration
        if self.health_check_grace_period_seconds is not None:
            not_null_args[
                "healthCheckGracePeriodSeconds"
            ] = self.health_check_grace_period_seconds
        if self.scheduling_strategy is not None:
            not_null_args["schedulingStrategy"] = self.scheduling_strategy
        if self.deployment_controller is not None:
            not_null_args["deploymentController"] = self.deployment_controller
        if self.tags is not None:
            not_null_args["tags"] = self.tags
        if self.enable_ecsmanaged_tags is not None:
            not_null_args["enableECSManagedTags"] = self.enable_ecsmanaged_tags
        if self.propagate_tags is not None:
            not_null_args["propagateTags"] = self.propagate_tags
        if self.enable_execute_command is not None:
            not_null_args["enableExecuteCommand"] = self.enable_execute_command

        # Register EcsService
        service_client = self.get_service_client(aws_client)
        try:
            create_response = service_client.create_service(
                serviceName=self.get_ecs_service_name(),
                taskDefinition=self.get_ecs_task_definition(),
                **not_null_args,
            )
            logger.debug(f"EcsService: {create_response}")
            resource_dict = create_response.get("service", {})

            # Validate resource creation
            if resource_dict is not None:
                print_info(f"EcsService created: {self.get_resource_name()}")
                self.active_resource = create_response
                return True
        except Exception as e:
            print_error(f"{self.get_resource_type()} could not be created.")
            print_error(e)
        return False

    def _read(self, aws_client: AwsApiClient) -> Optional[Any]:
        """Read EcsService"""
        from botocore.exceptions import ClientError

        logger.debug(f"Reading {self.get_resource_type()}: {self.get_resource_name()}")

        # create a dict of args which are not null, otherwise aws type validation fails
        not_null_args: Dict[str, Any] = {}

        cluster_name = self.get_ecs_cluster_name()
        if cluster_name is not None:
            not_null_args["cluster"] = cluster_name

        service_client = self.get_service_client(aws_client)
        try:
            service_name = self.get_ecs_service_name()
            describe_response = service_client.describe_services(
                services=[service_name], **not_null_args
            )
            logger.debug(f"EcsService: {describe_response}")
            resource_list = describe_response.get("services", None)

            if resource_list is not None and isinstance(resource_list, list):
                for resource in resource_list:
                    _service_name = resource.get("serviceName", None)
                    if _service_name == service_name:
                        _service_status = resource.get("status", None)
                        if _service_status == "ACTIVE":
                            self.active_resource = resource
                            break
        except ClientError as ce:
            logger.debug(f"ClientError: {ce}")
        except Exception as e:
            print_error(f"Error reading {self.get_resource_type()}.")
            print_error(e)
        return self.active_resource

    def _delete(self, aws_client: AwsApiClient) -> bool:
        """Delete EcsService"""
        print_info(f"Deleting {self.get_resource_type()}: {self.get_resource_name()}")

        # create a dict of args which are not null, otherwise aws type validation fails
        not_null_args: Dict[str, Any] = {}

        cluster_name = self.get_ecs_cluster_name()
        if cluster_name is not None:
            not_null_args["cluster"] = cluster_name
        if self.force_delete is not None:
            not_null_args["force"] = self.force_delete

        service_client = self.get_service_client(aws_client)
        self.active_resource = None
        try:
            delete_response = service_client.delete_service(
                service=self.get_ecs_service_name(),
                **not_null_args,
            )
            logger.debug(f"EcsService: {delete_response}")
            print_info(
                f"{self.get_resource_type()}: {self.get_resource_name()} deleted"
            )
            return True
        except Exception as e:
            print_error(f"{self.get_resource_type()} could not be deleted.")
            print_error("Please try again or delete resources manually.")
            print_error(e)
        return False

    def _update(self, aws_client: AwsApiClient) -> bool:
        """Update EcsService"""
        print_info(f"Updating {self.get_resource_type()}: {self.get_resource_name()}")

        return True