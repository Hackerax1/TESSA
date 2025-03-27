# TESSA Class Hierarchy Diagram

This diagram shows the class hierarchy of the main classes in TESSA.

```mermaid
classDiagram
    class ProxmoxAPI {
        +__init__()
        +authenticate()
        +api_request()
    }
    class BackupManager {
        +__init__()
        +create_backup()
        +restore_backup()
        +list_backups()
        +delete_backup()
        +verify_backup()
        +configure_backup()
        +configure_recovery_testing()
        +configure_retention_policy()
        +run_backup_now()
        +run_recovery_test_now()
        +run_retention_enforcement_now()
        +run_deduplication_now()
        +configure_notifications()
    }
    class BackupCommands {
        +__init__()
        +create_backup()
        +restore_backup()
        +list_backups()
        +delete_backup()
        +verify_backup()
        +start_backup_scheduler()
        +stop_backup_scheduler()
        +get_scheduler_status()
        +schedule_backup()
        +configure_recovery_testing()
        +configure_retention_policy()
        +run_backup_now()
        +run_recovery_test_now()
        +run_retention_enforcement_now()
        +run_deduplication_now()
        +configure_notifications()
    }
    class BackupSchedulerCommands {
        +__init__()
        +start_scheduler()
        +stop_scheduler()
        +get_scheduler_status()
        +update_scheduler_config()
        +configure_backup_schedule()
        +configure_recovery_testing()
        +configure_retention_policy()
        +configure_notifications()
        +run_backup_now()
        +run_recovery_testing_now()
        +run_retention_enforcement_now()
        +run_deduplication_now()
    }
    class ContainerManager {
        +__init__()
        +list_containers()
        +create_container()
        +start_container()
        +stop_container()
        +delete_container()
        +get_container_status()
    }
    class VMManager {
        +__init__()
        +list_vms()
        +start_vm()
        +stop_vm()
        +restart_vm()
        +get_vm_status()
        +create_vm()
        +delete_vm()
        +get_vm_location()
    }
    class DockerCommands {
        +__init__()
        +list_docker_containers()
        +start_docker_container()
        +stop_docker_container()
        +docker_container_logs()
        +docker_container_info()
        +pull_docker_image()
        +run_docker_container()
        +list_docker_images()
    }
    class DNSManager {
        +__init__()
        +add_dns_record()
        +list_dns_records()
        +delete_dns_record()
        +update_dns_servers()
        +get_dns_servers()
        +check_dns_resolution()
    }
    class FirewallManager {
        +__init__()
        +add_rule()
        +list_rules()
        +delete_rule()
        +add_service_rules()
        +get_firewall_status()
        +toggle_firewall()
    }
    class PXEManager {
        +__init__()
        +enable_pxe_service()
        +disable_pxe_service()
        +get_pxe_status()
        +upload_boot_image()
        +list_boot_images()
    }
    class SSHDeviceManager {
        +__init__()
        +scan_network()
        +discover_devices()
        +add_device()
        +remove_device()
        +list_devices()
        +get_device_groups()
        +execute_command()
        +execute_command_on_multiple()
        +execute_command_on_group()
        +setup_ssh_keys()
        +setup_ssh_keys_for_group()
    }
    class VLANManager {
        +__init__()
        +create_vlan()
        +list_vlans()
        +delete_vlan()
        +assign_vm_to_vlan()
    }
    class ProxmoxCommands {
        +__init__()
        +list_vms()
        +get_cluster_status()
        +start_vm()
        +stop_vm()
        +restart_vm()
        +get_vm_status()
        +create_vm()
        +delete_vm()
        +list_containers()
        +get_node_status()
        +get_storage_info()
        +get_vm_location()
        +get_help()
        +create_backup()
        +restore_backup()
        +list_backups()
        +delete_backup()
        +verify_backup()
        +create_zfs_pool()
        +get_zfs_pools()
        +get_zfs_datasets()
        +create_zfs_dataset()
        +set_zfs_properties()
        +create_zfs_snapshot()
        +setup_auto_snapshots()
        +configure_cloudflare_domain()
        +setup_cloudflare_tunnel()
        +list_cloudflare_domains()
        +list_cloudflare_tunnels()
        +remove_cloudflare_domain()
        +analyze_vm_resources()
        +get_cluster_efficiency()
        +configure_backup()
        +create_backup()
        +verify_backup()
        +restore_backup()
        +configure_remote_storage()
        +get_backup_status()
        +setup_network_segmentation()
        +create_network_segment()
        +get_network_recommendations()
        +configure_service_network()
        +analyze_network_security()
        +auto_configure_node()
        +configure_network()
        +set_network_profile()
        +create_network_profile()
        +detect_network_interfaces()
        +scan_network_for_devices()
        +discover_ssh_devices()
        +list_ssh_devices()
        +get_ssh_device_groups()
        +add_ssh_device()
        +remove_ssh_device()
        +execute_ssh_command()
        +execute_ssh_command_on_multiple()
        +execute_ssh_command_on_group()
        +setup_ssh_keys()
        +setup_ssh_keys_for_group()
        +create_vlan()
        +configure_firewall_rule()
        +ssh_into_device()
        +setup_pxe_service()
        +create_vlan()
        +list_vlans()
        +delete_vlan()
        +assign_vm_to_vlan()
        +add_firewall_rule()
        +list_firewall_rules()
        +delete_firewall_rule()
        +add_service_firewall_rules()
        +get_firewall_status()
        +ssh_into_device()
        +setup_pxe_service()
        +disable_pxe_service()
        +get_pxe_status()
        +upload_pxe_boot_image()
        +list_pxe_boot_images()
        +add_dns_record()
        +list_dns_records()
        +update_dns_servers()
        +merge_existing_proxmox()
        +discover_proxmox_environment()
        +analyze_proxmox_environment()
        +set_environment_merge_options()
        +get_merge_history()
        +start_backup_scheduler()
        +stop_backup_scheduler()
        +get_scheduler_status()
        +schedule_backup()
        +configure_recovery_testing()
        +configure_retention_policy()
        +run_backup_now()
        +run_recovery_test_now()
        +run_retention_enforcement_now()
        +run_deduplication_now()
        +configure_notifications()
        +run_security_audit()
        +get_audit_history()
        +manage_permissions()
        +manage_certificates()
        +manage_firewall()
        +assess_security_posture()
        +generate_security_report()
        +get_security_recommendations()
        +diagnose_issue()
        +analyze_logs()
        +run_network_diagnostics()
        +analyze_performance()
        +auto_resolve_issues()
        +generate_troubleshooting_report()
        +view_troubleshooting_history()
    }
    class SSHCommands {
        +__init__()
        +scan_network()
        +discover_devices()
        +list_devices()
        +get_device_groups()
        +add_device()
        +update_device()
        +remove_device()
        +execute_command()
        +execute_command_on_multiple()
        +execute_command_on_group()
        +setup_ssh_keys()
        +setup_ssh_keys_for_group()
        +upload_file()
        +download_file()
    }
    class BackupManager {
        +__init__()
        +create_backup()
        +restore_backup()
        +list_backups()
        +delete_backup()
        +verify_backup()
        +configure_backup_schedule()
        +get_backup_schedule()
        +remove_backup_schedule()
    }
    class StorageManager {
        +__init__()
        +create_storage()
        +create_zfs_pool()
        +create_lvm_group()
        +create_nfs_storage()
        +create_cifs_storage()
        +get_storage_info()
        +get_zfs_info()
        +get_lvm_info()
        +delete_storage()
        +resize_storage()
        +check_storage_health()
    }
    class ZFSManager {
        +__init__()
        +create_pool()
        +list_pools()
        +list_datasets()
        +create_dataset()
        +set_properties()
        +create_snapshot()
        +list_snapshots()
        +delete_snapshot()
        +rollback_snapshot()
        +setup_auto_snapshots()
        +get_pool_status()
        +scrub_pool()
        +get_scrub_status()
        +create_mirror()
        +replace_device()
        +get_device_health()
    }
    class DiagnosticsManager {
        +__init__()
        +run_system_diagnostics()
        +analyze_performance_issues()
        +get_error_report()
        +run_health_check()
    }
    class TroubleshootingCommands {
        +__init__()
        +process_command()
        +diagnose_issue()
        +analyze_logs()
        +run_network_diagnostics()
        +analyze_performance()
        +auto_resolve_issues()
        +generate_report()
        +view_troubleshooting_history()
        +get_help()
    }
    class UpdateCommand {
        +__init__()
        +check_updates()
        +list_updates()
        +apply_updates()
        +generate_update_plan()
        +schedule_updates()
        +get_update_status()
    }
    class VMCommand {
        +__init__()
        +execute_command()
        +run_cli_command()
    }
    class NetworkConfig
    class ProxmoxAutoConfigurator {
        +__init__()
        +configure_networking()
        +setup_network_segmentation()
        +setup_storage()
        +update_config()
        +auto_configure()
        +set_network_profile()
        +toggle_dhcp()
        +create_network_profile()
    }
    class JobStatus
    Enum <|-- JobStatus
    class JobPriority
    Enum <|-- JobPriority
    class Job {
        +__init__()
        +to_dict()
    }
    class JobQueue {
        +__init__()
        +start()
        +stop()
        +submit()
        +get_job()
        +cancel_job()
        +list_jobs()
        +clear_history()
    }
    class TaskExecutor {
        +__init__()
        +execute_shell_command()
        +execute_api_call()
        +execute_python_function()
        +get_task_status()
        +list_running_tasks()
        +list_all_tasks()
        +cancel_task()
    }
    class TaskScheduler {
        +__init__()
        +start()
        +stop()
        +schedule_task()
        +schedule_at_time()
        +schedule_cron()
        +cancel_task()
        +list_tasks()
        +get_task()
    }
    class WorkflowStatus
    Enum <|-- WorkflowStatus
    class StepStatus
    Enum <|-- StepStatus
    class WorkflowManager {
        +__init__()
        +define_workflow()
        +get_workflow()
        +list_workflows()
        +delete_workflow()
        +update_workflow()
        +execute_workflow()
        +get_execution_status()
        +list_executions()
        +cancel_execution()
        +add_workflow_step()
        +remove_workflow_step()
        +update_workflow_step()
    }
    class BaseNLI {
        +__init__()
        +load_custom_commands()
        +initialize_plugin_system()
        +get_help_text()
        +get_help()
        +get_plugins()
        +enable_plugin()
        +disable_plugin()
    }
    class CommandExecutor {
        +__init__()
        +execute_command()
    }
    class ProxmoxNLI {
        +__init__()
        +execute_intent()
        +confirm_command()
        +process_query()
        +get_recent_activity()
    }
    BaseNLI <|-- ProxmoxNLI
    class DashboardManager {
        +__init__()
        +create_dashboard()
        +get_dashboards()
        +get_dashboard()
        +update_dashboard()
        +delete_dashboard()
        +add_panel()
        +update_panel()
        +delete_panel()
        +initialize_default_dashboard()
        +sync_user_dashboards()
    }
    class AlertManager {
        +__init__()
        +register_alert_handler()
        +create_alert()
        +update_alert()
        +resolve_alert()
        +get_active_alerts()
        +get_alert_history()
        +clean_old_alerts()
        +update_thresholds()
    }
    class AuditLogger {
        +__init__()
        +log_command()
        +get_recent_logs()
        +get_user_activity()
        +get_failed_commands()
    }
    class EventDispatcher {
        +__init__()
        +subscribe()
        +unsubscribe()
        +publish()
        +get_event_history()
        +clear_history()
    }
    class NotificationManager {
        +__init__()
        +send_notification()
        +get_notification_history()
        +update_config()
    }
    class WebhookHandler {
        +__init__()
        +register_webhook()
        +unregister_webhook()
        +handle_event()
        +get_webhook_history()
    }
    class CloudProviderBase {
        +authenticate()
        +list_resources()
        +import_resources()
        +sync_status()
    }
    ABC <|-- CloudProviderBase
    class CloudProvider {
        +__init__()
        +configure_provider()
        +get_provider_status()
        +sync_cloud_resources()
        +import_cloud_resources()
        +update_sync_settings()
    }
    class DNSProviderBase {
        +authenticate()
        +list_records()
        +add_record()
        +update_record()
        +delete_record()
    }
    ABC <|-- DNSProviderBase
    class DNSProvider {
        +__init__()
        +configure_provider()
        +add_zone()
        +sync_records()
        +update_record()
        +add_record()
        +delete_record()
    }
    class EnvironmentMerger {
        +__init__()
        +discover_environment()
        +analyze_environment()
        +generate_merge_plan()
        +execute_merge()
        +merge_existing_environment()
        +set_merge_options()
        +get_merge_history()
    }
    class IdentityBackendBase {
        +configure()
        +test_connection()
        +authenticate_user()
        +get_user_groups()
        +sync_users()
    }
    ABC <|-- IdentityBackendBase
    class IdentityProvider {
        +__init__()
        +configure_backend()
        +add_group_mapping()
        +authenticate()
        +sync_users()
        +get_user_info()
        +test_backend()
    }
    class MonitoringBackendBase {
        +configure()
        +test_connection()
        +register_metrics()
        +send_metrics()
        +query_metrics()
    }
    ABC <|-- MonitoringBackendBase
    class MonitoringIntegration {
        +__init__()
        +configure_backend()
        +register_custom_metric()
        +send_metrics()
        +query_metrics()
        +configure_dashboard()
        +test_backend()
    }
    class MetricsCollector {
        +__init__()
        +start_collection()
        +stop_collection()
        +get_buffered_metrics()
        +collect_all_metrics()
    }
    class PredictiveAnalyzer {
        +__init__()
        +predict_resource_needs()
        +analyze_power_efficiency()
    }
    class PrometheusClient {
        +__init__()
        +query()
        +query_range()
    }
    class PrometheusMetricsCollector {
        +__init__()
        +get_node_metrics()
    }
    class ResourceAnalyzer {
        +__init__()
        +analyze_vm_resources()
        +get_cluster_efficiency()
    }
    class ResourceMonitor {
        +__init__()
        +start_monitoring()
        +stop_monitoring()
        +register_alert_callback()
        +update_thresholds()
        +get_resource_summary()
    }
    class SystemHealth {
        +__init__()
        +start_health_checks()
        +stop_health_checks()
        +get_system_health()
    }
    class CloudflareManager {
        +__init__()
        +configure_domain()
        +create_tunnel()
        +get_domains()
        +get_tunnels()
        +remove_domain()
    }
    class DNSManager {
        +__init__()
        +add_dns_record()
        +delete_dns_record()
        +list_dns_records()
        +lookup_hostname()
        +lookup_ip()
        +update_dns_servers()
    }
    class FirewallManager {
        +__init__()
        +add_rule()
        +delete_rule()
        +list_rules()
        +enable_firewall()
        +disable_firewall()
        +get_firewall_status()
        +add_service_rules()
    }
    class NetworkSegment
    class NetworkManager {
        +__init__()
        +setup_network_segmentation()
        +create_network_segment()
        +get_network_recommendations()
        +configure_service_network()
        +analyze_network_security()
    }
    class PXEManager {
        +__init__()
        +enable_pxe_service()
        +disable_pxe_service()
        +upload_boot_image()
        +list_boot_images()
        +get_pxe_status()
    }
    class VLANHandler {
        +__init__()
        +create_vlan()
        +delete_vlan()
        +list_vlans()
        +assign_vm_to_vlan()
    }
    class ProfileSyncManager {
        +__init__()
        +start_sync_service()
        +stop_sync_service()
        +queue_sync_task()
        +register_device()
        +enable_sync()
    }
    class ResponseGenerator {
        +__init__()
        +set_ollama_client()
        +set_huggingface_client()
        +generate_response()
    }
    class AuthManager {
        +__init__()
        +create_token()
        +verify_token()
        +check_permission()
        +refresh_token()
        +revoke_token()
        +get_active_sessions()
    }
    class CertificateManager {
        +__init__()
        +list_certificates()
        +generate_self_signed_certificate()
        +request_lets_encrypt_certificate()
        +interpret_certificate_command()
        +generate_certificate_report()
    }
    class PermissionHandler {
        +__init__()
        +has_permission()
        +get_role_permissions()
        +add_role_permission()
        +remove_role_permission()
    }
    class SecurityAuditor {
        +__init__()
        +run_full_audit()
        +get_audit_history()
        +interpret_audit_command()
    }
    class SecurityCommands {
        +__init__()
        +handle_command()
    }
    class SecurityManager {
        +__init__()
        +run_security_audit()
        +interpret_permission_command()
        +interpret_firewall_command()
    }
    class SecurityPostureAssessor {
        +__init__()
        +assess_security_posture()
        +generate_posture_report()
        +interpret_posture_command()
    }
    class SessionManager {
        +__init__()
        +create_session()
        +get_session()
        +update_session()
        +end_session()
        +get_active_sessions()
    }
    class TokenManager {
        +__init__()
        +revoke_token()
        +is_token_revoked()
        +clear_revoked_tokens()
    }
    class UserManager {
        +__init__()
        +set_user_preference()
        +get_user_preferences()
        +get_user_statistics()
        +get_recent_activity()
        +get_user_activity()
        +get_failed_commands()
        +add_to_command_history()
        +get_command_history()
        +clear_command_history()
        +add_favorite_command()
        +get_favorite_commands()
        +remove_favorite_command()
        +set_notification_preference()
        +get_notification_preferences()
        +initialize_default_notification_preferences()
        +get_notification_channels_for_event()
        +create_dashboard()
        +get_dashboards()
        +get_dashboard()
        +update_dashboard()
        +delete_dashboard()
        +add_dashboard_panel()
        +update_dashboard_panel()
        +delete_dashboard_panel()
        +initialize_default_dashboard()
        +sync_profile()
        +register_device()
        +get_user_devices()
        +remove_device()
        +get_shortcuts()
        +add_shortcut()
        +delete_shortcut()
        +update_shortcut_position()
        +get_shortcut_categories()
        +initialize_default_shortcuts()
    }
    class DependencyResolver {
        +__init__()
        +get_dependencies()
        +check_circular_dependencies()
        +get_installation_plan()
        +explain_dependencies()
        +get_dependency_diagram()
    }
    class HealthChecker {
        +__init__()
        +check_service_health()
        +check_all_services_health()
        +get_service_metrics()
        +generate_health_report()
    }
    class ServiceConfig {
        +__init__()
        +get_service_config()
        +save_service_config()
        +validate_config()
    }
    class ServiceDeployer {
        +__init__()
        +deploy_service()
        +deploy_services_group()
        +stop_service()
        +remove_service()
    }
    class ServiceHandler {
        +__init__()
        +handle_service_intent()
    }
    class ServiceWizard {
        +__init__()
        +start_wizard()
        +start_goal_based_wizard()
        +process_goal_wizard_step()
        +get_available_goals()
        +get_available_cloud_replacements()
        +deploy_service()
        +process_answers()
    }
    class ServiceHandler {
        +__init__()
        +handle_service_intent()
        +list_available_services()
        +list_deployed_services()
        +find_service()
        +deploy_service()
        +get_service_status()
        +stop_service()
        +remove_service()
    }
    class SSHDevice {
        +to_dict()
    }
    class SSHDeviceManager {
        +__init__()
        +load_devices()
        +save_devices()
        +add_device()
        +remove_device()
        +get_device()
        +get_all_devices()
        +scan_network()
        +discover_and_add_devices()
        +test_connection()
        +execute_command()
        +execute_command_on_multiple()
        +get_device_groups()
        +setup_ssh_keys()
        +upload_file()
        +download_file()
    }
    class BackupManager {
        +__init__()
        +configure_backup()
        +create_backup()
        +verify_backup()
        +restore_backup()
        +configure_remote_storage()
        +get_backup_status()
        +cleanup_old_backups()
        +test_backup_recovery()
        +configure_retention_policy()
        +implement_data_deduplication()
    }
    class BackupScheduler {
        +__init__()
        +update_config()
        +start()
        +stop()
        +get_status()
    }
    class SnapshotManager {
        +__init__()
        +list_snapshots()
        +create_snapshot()
        +delete_snapshot()
        +rollback_snapshot()
        +get_snapshot_details()
        +create_scheduled_snapshots()
        +create_bulk_snapshots()
        +restore_from_snapshot()
        +create_snapshot_policy()
    }
    class StorageManager {
        +__init__()
        +list_storage()
        +get_storage_details()
        +create_storage()
        +delete_storage()
        +update_storage()
        +get_storage_status()
        +get_content()
        +upload_content()
    }
    class ZFSHandler {
        +__init__()
        +list_pools()
        +get_pool_status()
        +create_pool()
        +destroy_pool()
        +list_datasets()
        +create_dataset()
        +destroy_dataset()
        +set_property()
        +get_properties()
        +create_snapshot()
        +list_snapshots()
        +rollback_snapshot()
        +destroy_snapshot()
        +send_receive()
        +scrub_pool()
    }
    class DiagnosticTools {
        +__init__()
        +run_diagnostics()
        +check_network()
        +check_storage()
        +check_system()
        +check_proxmox()
    }
    class LogAnalyzer {
        +__init__()
        +analyze_logs()
        +analyze_system_logs()
        +analyze_vm_logs()
        +analyze_container_logs()
        +analyze_service_logs()
    }
    class NetworkDiagnostics {
        +__init__()
        +run_diagnostics()
        +comprehensive_diagnostics()
        +check_connectivity()
        +check_dns()
        +check_port()
        +check_route()
        +get_network_interfaces()
        +get_listening_ports()
        +get_active_connections()
        +get_firewall_rules()
        +visualize_network()
    }
    class PerformanceAnalyzer {
        +__init__()
        +analyze_performance()
        +analyze_all_performance()
        +analyze_cpu_performance()
        +analyze_memory_performance()
        +analyze_disk_performance()
        +analyze_network_performance()
        +detect_bottlenecks()
    }
    class ReportGenerator {
        +__init__()
        +generate_report()
        +generate_text_report()
        +generate_html_report()
        +generate_json_report()
        +get_report_history()
        +delete_report()
    }
    class SelfHealingTools {
        +__init__()
        +apply_remediation()
        +fix_service_issue()
        +fix_network_connectivity()
        +fix_storage_issue()
        +fix_high_load()
        +fix_cluster_issue()
    }
    class TroubleshootingAssistant {
        +__init__()
        +guided_diagnostics()
        +analyze_logs()
        +detect_bottlenecks()
        +visualize_network()
        +get_self_healing_recommendations()
        +execute_healing_action()
        +auto_resolve_issues()
        +generate_report()
        +get_troubleshooting_history()
    }
    class UserPreferencesManager {
        +__init__()
        +set_preference()
        +get_preference()
        +get_all_preferences()
        +delete_preference()
        +add_favorite_vm()
        +remove_favorite_vm()
        +get_favorite_vms()
        +add_favorite_node()
        +get_favorite_nodes()
        +track_command_usage()
        +get_frequent_commands()
        +add_quick_access_service()
        +get_quick_access_services()
        +add_to_command_history()
        +get_command_history()
        +clear_command_history()
        +add_favorite_command()
        +get_favorite_commands()
        +remove_favorite_command()
        +set_notification_preference()
        +get_notification_preferences()
        +get_notification_preference()
        +get_notification_channels_for_event()
        +initialize_default_notification_preferences()
        +delete_notification_preferences()
        +add_shortcut()
        +get_shortcuts()
        +get_shortcut()
        +delete_shortcut()
        +get_shortcut_categories()
        +update_shortcut_position()
        +initialize_default_shortcuts()
    }
    class UserManager {
        +__init__()
        +add_shortcut()
        +get_shortcuts()
        +get_shortcut()
        +delete_shortcut()
        +update_shortcut_position()
        +initialize_default_shortcuts()
        +get_shortcut_categories()
    }
    class VoiceProfile {
        +to_dict()
        +from_dict()
    }
    class VoiceShortcut {
        +to_dict()
        +from_dict()
    }
    class CommandSequence {
        +to_dict()
        +from_dict()
    }
    class VoiceSignature {
        +to_dict()
        +from_dict()
    }
    class VoiceHandler {
        +__init__()
        +save_profile()
        +save_voice_signature()
        +save_shortcut()
        +save_sequence()
        +set_active_profile()
        +get_active_profile()
        +list_profiles()
        +list_shortcuts()
        +list_sequences()
        +list_available_languages()
        +adapt_to_user_experience()
        +add_personality()
        +extract_voice_features()
        +register_voice()
        +authenticate_voice()
        +start_ambient_mode()
        +stop_ambient_mode()
        +add_wake_word()
        +remove_wake_word()
        +create_voice_shortcut()
        +delete_voice_shortcut()
        +match_voice_shortcut()
        +create_command_sequence()
        +delete_command_sequence()
        +match_command_sequence()
        +update_command_context()
        +clear_command_context()
        +get_next_sequence_step()
        +start_sequence()
        +speech_to_text()
        +text_to_speech()
    }
    class ContextManager {
        +__init__()
        +update_context()
        +set_context()
        +resolve_contextual_references()
        +get_conversation_summary()
        +get_active_context()
        +save_context()
        +load_context()
    }
    class EntityExtractor {
        +__init__()
        +extract_entities()
        +validate_entities()
    }
    class HuggingFaceClient {
        +__init__()
        +get_intent_and_entities()
        +enhance_response()
        +get_contextual_information()
    }
    class IntentIdentifier {
        +__init__()
        +identify_intent()
    }
    class NLU_Engine {
        +__init__()
        +process_query()
        +enhance_response()
        +save_context()
        +load_context()
        +get_conversation_summary()
    }
    class OllamaClient {
        +__init__()
        +get_intent_and_entities()
        +enhance_response()
        +get_contextual_information()
    }
    class Preprocessor {
        +__init__()
        +preprocess_query()
    }
    class BasePlugin {
        +name()
        +version()
        +description()
        +author()
        +dependencies()
        +initialize()
        +get_config_schema()
        +validate_config()
        +on_shutdown()
    }
    ABC <|-- BasePlugin
    class PluginManager {
        +__init__()
        +discover_plugins()
        +load_plugins()
        +get_plugin()
        +get_all_plugins()
        +enable_plugin()
        +disable_plugin()
        +shutdown()
    }
    class ServiceBackupHandler {
        +__init__()
        +backup_service()
        +restore_service()
        +list_backups()
    }
    class DependencyManager {
        +__init__()
        +build_dependency_graph()
        +get_installation_order()
        +detect_circular_dependencies()
        +get_dependency_tree()
        +visualize_dependencies()
        +can_install_service()
    }
    class DependencyVisualizer {
        +__init__()
        +generate_dependency_graph()
        +analyze_dependencies()
        +generate_dependency_report()
        +generate_dot_graph()
        +generate_mermaid_graph()
        +generate_interactive_visualization()
        +generate_natural_language_description()
        +get_service_impact()
        +generate_impact_report()
    }
    class BaseDeployer {
        +__init__()
        +deploy()
        +verify_vm()
        +run_command()
    }
    class DockerDeployer {
        +deploy()
        +stop_service()
        +remove_service()
    }
    BaseDeployer <|-- DockerDeployer
    class ScriptDeployer {
        +deploy()
        +stop_service()
        +remove_service()
    }
    BaseDeployer <|-- ScriptDeployer
    class ServiceValidator {
        +validate_service_definition()
        +validate_custom_params()
    }
    class DockerValidator {
        +validate_image_name()
        +validate_port_mappings()
        +validate_volume_mappings()
        +validate_environment_vars()
        +validate_compose_config()
        +validate_backup_config()
        +validate_deployment_config()
    }
    class ScriptValidator {
        +validate_script_content()
        +validate_command_list()
        +validate_process_name()
        +validate_backup_config()
        +validate_deployment_config()
    }
    class GoalBasedCatalog {
        +__init__()
        +build_indexes()
        +get_goals_with_services()
        +get_services_for_goal()
        +get_services_for_cloud_replacement()
        +get_cloud_replacements_with_services()
        +find_services_by_goal_keywords()
        +get_service_info_with_goals()
        +get_service_recommendations_by_goal()
        +get_service_recommendations_for_cloud()
        +categorize_service_catalog()
    }
    class GoalBasedSetupWizard {
        +__init__()
        +reset_state()
        +get_goal_categories()
        +get_cloud_replacements()
        +start_setup()
        +select_approach()
        +select_goals()
        +select_replacements()
        +select_services()
        +confirm_plan()
        +get_current_state()
        +to_json()
        +from_json()
    }
    class GoalMapper {
        +__init__()
        +load_services()
        +get_service_by_id()
        +is_foss_service()
        +is_excluded_service()
        +get_recommended_services()
        +get_cloud_replacement_services()
        +estimate_resource_requirements()
        +get_service_dependencies()
        +get_all_required_dependencies()
        +get_all_goals()
        +get_all_cloud_services()
    }
    class ServiceHealthMonitor {
        +__init__()
        +start_monitoring()
        +stop_monitoring()
        +check_services_health()
        +get_service_health()
        +get_health_report()
        +get_all_services_health_summary()
        +generate_system_health_report()
        +generate_natural_language_report()
        +get_service_health_summary()
    }
    class ServiceMetricsDashboard {
        +__init__()
        +load_metrics_history()
        +save_metrics_history()
        +update_metrics()
        +update_service_metrics_from_health()
        +get_service_dashboard()
        +generate_dashboard_report()
        +get_system_dashboard()
        +generate_system_dashboard_report()
    }
    class ServiceCatalog {
        +__init__()
        +get_all_services()
        +get_service()
        +find_services_by_keywords()
        +add_service_definition()
        +get_invalid_services()
        +get_service_dependencies()
        +get_all_required_dependencies()
        +get_services_by_goal()
        +get_replacement_services()
    }
    class ServiceManager {
        +__init__()
        +find_service()
        +deploy_service()
        +get_service_status()
        +list_deployed_services()
        +stop_service()
        +remove_service()
        +setup_cloudflare_service()
        +remove_cloudflare_service()
    }
    class TemplateManager {
        +__init__()
        +get_template()
        +get_all_templates()
        +create_template_from_service()
        +create_custom_template()
        +update_template()
        +delete_template()
        +share_template()
        +unshare_template()
        +export_template()
        +import_template()
        +create_service_from_template()
        +search_templates()
        +generate_template_report()
        +generate_template_from_description()
        +get_template_recommendations()
        +generate_template_comparison()
        +get_template_natural_language_description()
    }
```

## Legend

- Classes are shown with their methods
- `+` indicates public methods
- `-` indicates private/protected methods
- Inheritance is shown with arrows pointing from the child to the parent class
