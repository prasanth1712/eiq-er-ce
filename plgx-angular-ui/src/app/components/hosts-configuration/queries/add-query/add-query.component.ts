import { Component, OnInit,ViewChild } from '@angular/core';

import { CommonapiService } from '../../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../../dashboard/_services/commonvariable.service';
import { FormGroup, FormBuilder, FormArray, Validators, FormControl } from '@angular/forms';
import { first } from 'rxjs/operators';
import swal from 'sweetalert';
import { Location } from '@angular/common';
import { Router } from '@angular/router';
import { environment } from '../../../../../environments/environment'
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

import { Title } from '@angular/platform-browser';
import 'ace-builds/src-noconflict/mode-javascript';
import * as THEME from 'ace-builds/src-noconflict/theme-github';
import * as langTools from 'ace-builds/src-noconflict/ext-language_tools';
import { TagsValidationHandler } from '../../../../dashboard/_helpers/tagsValidationHandler';

const tables = "docker_image_labels|docker_images|docker_info|docker_network_labels|docker_networks|docker_version|docker_volume_labels|docker_volumes|drivers|ec2_instance_metadata|ec2_instance_tags|elf_dynamic|elf_info|elf_sections|elf_segments|etc_hosts|etc_protocols|etc_services|event_taps|example|extended_attributes|fan_speed_sensors|fbsd_kmods|file|file_events|firefox_addons|gatekeeper|gatekeeper_approved_apps|groups|hardware_events|hash|homebrew_packages|ie_extensions|intel_me_info|interface_addresses|interface_details|interface_ipv6|iokit_devicetree|iokit_registry|iptables|kernel_extensions|kernel_info|kernel_integrity|kernel_modules|kernel_panics|keychain_acls|keychain_items|known_hosts|kva_speculative_info|last|launchd|launchd_overrides|listening_ports|lldp_neighbors|load_average|logged_in_users|logical_drives|logon_sessions|magic|managed_policies|md_devices|md_drives|md_personalities|mdfind|memory_array_mapped_addresses|memory_arrays|memory_device_mapped_addresses|memory_error_info|memory_info|memory_map|mounts|msr|nfs_shares|npm_packages|ntdomains|ntfs_acl_permissions|nvram|oem_strings|opera_extensions|os_version|osquery_events|osquery_extensions|osquery_flags|osquery_info|osquery_packs|osquery_registry|osquery_schedule|package_bom|package_install_history|package_receipts|patches|pci_devices|physical_disk_performance|pipes|pkg_packages|platform_info|plist|portage_keywords|portage_packages|portage_use|power_sensors|powershell_events|preferences|process_envs|process_events|process_file_events|process_memory_map|process_namespaces|process_open_files|process_open_sockets|processes|programs|prometheus_metrics|python_packages|quicklook_cache|registry|routes|rpm_package_files|rpm_packages|safari_extensions|sandboxes|scheduled_tasks|selinux_events|services|shadow|shared_folders|shared_memory|shared_resources|sharing_preferences|shell_history|signature|sip_config|smart_drive_info|smbios_tables|smc_keys|socket_events|ssh_configs|startup_items|sudoers|suid_bin|syslog_events|system_controls|system_info|temperature_sensors|time|time_machine_backups|time_machine_destinations|ulimit_info|uptime|usb_devices|user_events|user_groups|user_interaction_events|user_ssh_keys|users|video_info|virtual_memory_info|wifi_networks|wifi_status|wifi_survey|winbaseobj|windows_crashes|windows_events|wmi_bios_info|wmi_cli_event_consumers|wmi_event_filters|wmi_filter_consumer_binding|wmi_script_event_consumers|xprotect_entries|xprotect_meta|xprotect_reports|yara|yara_events|yum_sources|win_file_events|win_process_events|win_process_open_events|win_remote_thread_events|win_pefile_events|win_msr|win_removable_media_events|win_http_events|win_epp_table|win_startup_items|win_services|win_programs|win_socket_events|win_image_load_events|win_yara_events| win_yara| win_obfuscated_ps|win_dns_events|win_dns_response_events|win_process_handles|win_registry_events|win_file_timestomp_events|win_hash|win_image_load_process_map|win_mem_perf|win_process_perf|win_logger_events|win_ssl_events|win_suspicious_process_dump|win_suspicious_process_scan|carves|authorized_keys|win_event_log_data|win_event_log_channels";
const keywords = "select|from|where|and|or|group|by|order|limit|offset|having|as|case|when|else|end|type|left|right|join|on|outer|desc|asc|union|table|if|not|null|inner",
  builtinFunctions = "avg|count|first|last|max|min|sum|ucase|lcase|mid|len|round|rank|now|format|coalesce|ifnull|isnull|nvl",
  dataTypes = "int|numeric|decimal|date|varchar|char|bigint|float|double|bit|binary|text|set|timestamp|money|real|number|integer",
  all_columns = "uid|creation_time|failed_login_count|failed_login_timestamp|password_last_set_time|\n" +
    "name|size|md5|domain|option|value|\n" +
    "allow_signed_enabled|firewall_unload|global_state|logging_enabled|logging_option|stealth_enabled|version|\n" +
    "path|state|\n" +
    "process|\n" +
    "service|process|\n" +
    "scheme|handler|enabled|external|protected|\n" +
    "executable|path|description|install_time|type|sdb_id|bundle_executable|bundle_identifier|bundle_name|bundle_short_version|bundle_version|bundle_package_type|environment|element|compiler|development_region|display_name|info_string|minimum_system_version|category|applescript_enabled|copyright|last_opened_time|source|base_uri|release|maintainer|components|architectures|\n" +
    "address|mac|interface|permanent|\n" +
    "time|time_nano_sec|host|sender|facility|pid|gid|level|message|ref_pid|ref_proc|extra|\n" +
    "node|label|original_program_name|serial_number|issuer_name|subject_name|result|\n" +
    "label|plugin|mechanism|privileged|entry|modified|allow_root|timeout|tries|authenticate_user|shared|comment|created|class|session_owner|\n" +
    "uid|algorithm|key|key_file|name|\n" +
    "manufacturer|manufacture_date|model|cycle_count|health|condition|charging|charged|designed_capacity|max_capacity|current_capacity|percent_remaining|amperage|voltage|minutes_until_empty|minutes_to_full_charge|\n" +
    "device_id|drive_letter|persistent_volume_id|conversion_status|protection_status|encryption_method|parent|vendor|block_size|uuid|identifier|sdk|native|disabled|\n" +
    "sensor_id|config_name|collect_store_files|collect_module_loads|collect_module_info|collect_file_mods|collect_reg_mods|collect_net_conns|collect_processes|collect_cross_processes|collect_emet_events|collect_data_file_writes|collect_process_user_context|collect_sensor_operations|log_file_disk_quota_mb|log_file_disk_quota_percentage|protection_disabled|sensor_ip_addr|sensor_backend_server|event_queue|binary_queue|sha256|status|carve_guid|carve|\n" +
    "common_name|subject|issuer|ca|self_signed|not_valid_before|DATETIME|not_valid_after|signing_algorithm|key_algorithm|key_strength|key_usage|subject_key_id|authority_key_id|sha1|serial|summary|author|license|locale|update_url|persistent|permissions|manufacturer|processor_type|availability|cpu_status|number_of_cores|logical_processors|address_width|current_clock_speed|max_clock_speed|socket_designation|\n" +
    "core|user|nice|system|idle|iowait|irq|softirq|steal|guest|guest_nice|\n" +
    "feature|output_register|output_bit|input_eax|\n" +
    "type|crash_path|responsible|datetime|crashed_thread|stack_trace|exception_type|exception_codes|exception_notes|registers|\n" +
    "event|minute|hour|day_of_month|month|day_of_week|command|option_name|option_value|\n" +
    "title|destination|format|completed_time|processing_time|\n" +
    "url|method|user_agent|response_code|round_trip_time|bytes|\n" +
    "hostname|common_name|organization|organization_unit|issuer_common_name|issuer_organization|issuer_organization_unit|valid_from|valid_to|sha256_fingerprint|sha1_fingerprint|arch|revision|\n" +
    "device|partition|filename|inode|mode|atime|mtime|ctime|hard_links|device|offset|blocks_size|blocks|inodes|flags|encrypted|user_uuid|encryption_status|\n" +
    "action|ejectable|mountable|writable|content|media_name|filesystem|checksum|time|eid|\n" +
    "partitions|disk_index|id|pnp_device_id|disk_size|hardware_model|\n" +
    "id|address|netmask|options|driver|rw|propagation|network_id|endpoint_id|gateway|ip_address|ip_prefix_len|ipv6_gateway|ipv6_address|ipv6_prefix_len|mac_address|port|host_ip|host_port|cmdline|euid|egid|suid|sgid|wired_size|resident_size|total_size|start_time|pgroup|threads|cpu|mem|pids|read|preread|interval|disk_read|disk_write|num_procs|cpu_total_usage|cpu_kernelmode_usage|cpu_usermode_usage|system_cpu_usage|online_cpus|pre_cpu_total_usage|pre_cpu_kernelmode_usage|pre_cpu_usermode_usage|pre_system_cpu_usage|pre_online_cpus|memory_usage|memory_max_usage|memory_limit|network_rx_bytes|network_tx_bytes|image|image_id|config_entrypoint|started_at|finished_at|security_options|env_variables|readonly_rootfs|cgroup_namespace|ipc_namespace|mnt_namespace|net_namespace|pid_namespace|user_namespace|uts_namespace|size_bytes|tags|containers|containers_running|containers_paused|containers_stopped|images|storage_driver|swap_limit|kernel_memory|cpu_cfs_period|cpu_cfs_quota|cpu_shares|cpu_set|ipv4_forwarding|bridge_nf_iptables|bridge_nf_ip6tables|oom_kill_disable|logging_driver|cgroup_driver|kernel_version|os|os_type|architecture|cpus|memory|http_proxy|https_proxy|no_proxy|server_version|root_dir|enable_ipv6|subnet|\n" +
    "version|api_version|min_api_version|git_commit|go_version|build_time|mount_point|device_name|service|service_key|inf|provider|driver_key|date|signed|\n" +
    "instance_id|instance_type|region|availability_zone|local_hostname|local_ipv4|security_groups|iam_arn|ami_id|reservation_id|account_id|ssh_public_key|\n" +
    "tag|\n" +
    "class|abi|abi_version|machine|vaddr|link|align|psize|msize|hostnames|number|alias|protocol|aliases|\n" +
    "enabled|event_tap_id|event_tapped|process_being_tapped|tapping_process|points|action|directory|base64|\n" +
    "fan|actual|min|max|target|refs|btime|symlink|attributes|volume_serial|file_id|\n" +
    "target_path|transaction_id|hashed|creator|source_url|visible|active|autoupdate|location|\n" +
    "assessments_enabled|dev_id_enabled|opaque_version|requirement|\n" +
    "gid|gid_signed|groupname|group_sid|vendor_id|model_id|ssdeep|registry_path|\n" +
    "interface|mask|broadcast|point_to_point|friendly_name|\n" +
    "dns_server_search_order|dns_host_name|dns_domain_suffix_search_order|dns_domain|dhcp_server|dhcp_lease_obtained|dhcp_lease_expires|dhcp_enabled|speed|physical_adapter|connection_status|connection_id|mtu|metric|ipackets|opackets|ibytes|obytes|ierrors|oerrors|idrops|odrops|collisions|last_change|hop_limit|forwarding_enabled|redirect_accept|rtadv_accept|device_path|busy_state|retain_count|depth|\n" +
    "filter_name|chain|policy|src_port|dst_port|src_ip|src_mask|iniface|iniface_mask|dst_ip|dst_mask|outiface|outiface_mask|match|packets|\n" +
    "idx|linked_against|arguments|\n" +
    "sycall_addr_modified|text_segment_hash|used_by|frame_backtrace|module_backtrace|dependencies|os_version|system_model|uptime|last_loaded|last_unloaded|\n" +
    "keychain_path|authorizations|\n" +
    "kva_shadow_enabled|kva_shadow_user_global|kva_shadow_pcid|kva_shadow_inv_pcid|bp_mitigations|bp_system_pol_disabled|bp_microcode_disabled|cpu_spec_ctrl_supported|ibrs_support_enabled|stibp_support_enabled|cpu_pred_cmd_supported|\n" +
    "username|tty|program|run_at_load|keep_alive|on_demand|username|stdout_path|stderr_path|start_interval|program_arguments|watch_paths|queue_directories|inetd_compatibility|start_on_mount|root_directory|working_directory|process_type|\n" +
    "pid|family|fd|socket|rid|chassis_id_type|chassis_id|chassis_sysname|chassis_sys_description|chassis_bridge_capability_available|chassis_bridge_capability_enabled|chassis_router_capability_available|chassis_router_capability_enabled|chassis_repeater_capability_available|chassis_repeater_capability_enabled|chassis_wlan_capability_available|chassis_wlan_capability_enabled|chassis_tel_capability_available|chassis_tel_capability_enabled|chassis_docsis_capability_available|chassis_docsis_capability_enabled|chassis_station_capability_available|chassis_station_capability_enabled|chassis_other_capability_available|chassis_other_capability_enabled|chassis_mgmt_ips|port_id_type|port_id|port_description|port_ttl|port_mfs|port_aggregation_id|port_autoneg_supported|port_autoneg_enabled|port_mau_type|port_autoneg_10baset_hd_enabled|port_autoneg_10baset_fd_enabled|port_autoneg_100basetx_hd_enabled|port_autoneg_100basetx_fd_enabled|port_autoneg_100baset2_hd_enabled|port_autoneg_100baset2_fd_enabled|port_autoneg_100baset4_hd_enabled|port_autoneg_100baset4_fd_enabled|port_autoneg_1000basex_hd_enabled|port_autoneg_1000basex_fd_enabled|port_autoneg_1000baset_hd_enabled|port_autoneg_1000baset_fd_enabled|power_device_type|power_mdi_supported|power_mdi_enabled|power_paircontrol_enabled|power_pairs|power_class|power_8023at_enabled|power_8023at_power_type|power_8023at_power_source|power_8023at_power_priority|power_8023at_power_allocated|power_8023at_power_requested|med_device_type|med_capability_capabilities|med_capability_policy|med_capability_location|med_capability_mdi_pse|med_capability_mdi_pd|med_capability_inventory|med_policies|vlans|pvid|ppvids_supported|ppvids_enabled|\n" +
    "period|average|free_space|file_system|boot_partition|\n" +
    "logon_id|logon_domain|authentication_package|logon_type|session_id|logon_sid|logon_time|logon_server|dns_domain_name|upn|logon_script|profile_path|home_directory|home_directory_drive|data|mime_type|mime_encoding|\n" +
    "domain|manual|\n" +
    "device_name|raid_level|chunk_size|raid_disks|nr_raid_disks|working_disks|active_disks|failed_disks|spare_disks|superblock_state|superblock_version|superblock_update_time|bitmap_on_mem|bitmap_chunk_size|bitmap_external_file|recovery_progress|recovery_finish|recovery_speed|resync_progress|resync_finish|resync_speed|reshape_progress|reshape_finish|reshape_speed|check_array_progress|check_array_finish|check_array_speed|unused_devices|other|\n" +
    "md_device_name|drive_name|slot|query|\n" +
    "handle|memory_array_handle|starting_address|ending_address|partition_width|use|memory_error_correction|memory_error_info_handle|number_memory_devices|memory_device_handle|memory_array_mapped_address_handle|partition_row_position|interleave_position|interleave_data_depth|error_type|error_granularity|error_operation|vendor_syndrome|memory_array_error_address|device_error_address|error_resolution|\n" +
    "memory_total|memory_free|buffers|cached|swap_cached|inactive|swap_total|swap_free|start|end|device_alias|blocks_free|blocks_available|inodes_free|\n" +
    "processor_number|turbo_disabled|turbo_ratio_limit|platform_info|perf_ctl|perf_status|feature_control|rapl_power_limit|rapl_energy_status|rapl_power_units|\n" +
    "share|readonly|client_site_name|dc_site_name|dns_forest_name|domain_controller_address|domain_controller_name|domain_name|principal|access|inherited_from|major|minor|patch|build|platform|platform_like|codename|install_date|publisher|subscriptions|events|refreshes|\n" +
    "uuid|sdk_version|default_value|shell_only|instance_id|config_hash|config_valid|extensions|build_platform|build_distro|watcher|shard|discovery_cache_hits|discovery_executions|\n" +
    "registry|owner_uuid|internal|executions|last_executed|blacklisted|output_size|wall_time|user_time|system_time|average_memory|\n" +
    "filepath|modified_time|\n" +
    "package_id|content_type|package_filename|installer_name|\n" +
    "csname|hotfix_id|caption|fix_comments|installed_by|installed_on|\n" +
    "subsystem_model|subsystem_model_id|subsystem_vendor|subsystem_vendor_id|pci_subclass|pci_subclass_id|pci_class_id|pci_slot|pci_class|avg_disk_bytes_per_read|avg_disk_bytes_per_write|avg_disk_read_queue_length|avg_disk_write_queue_length|avg_disk_sec_per_read|avg_disk_sec_per_write|current_disk_queue_length|percent_disk_read_time|percent_disk_write_time|percent_disk_time|percent_idle_time|instances|max_instances|flatsize|\n" +
    "vendor|volume_size|\n" +
    "key|subkey|\n" +
    "package|keyword|unmask|repository|eapi|world|script_block_id|script_block_count|script_text|script_name|script_path|cosine_similarity|forced|cmdline_size|env|env_count|env_size|cwd|auid|owner_uid|owner_gid|overflows|\n" +
    "operation|ppid|executable|partial|dest_path|pseudo|local_address|remote_address|local_port|remote_port|\n" +
    "cpu_subtype|cpu_type|uppid|upid|root|on_disk|disk_bytes_read|disk_bytes_written|install_location|install_source|language|uninstall_string|identifying_number|\n" +
    "target_name|metric_name|metric_value|timestamp_ms|rowid|fs_id|volume_id|last_hit_date|hit_count|icon_mode|cache_path|\n" +
    "hopcount|developer_id|build_id|bundle_path|hidden|last_run_time|next_run_time|last_run_message|last_run_code|service_type|start_type|win32_exit_code|service_exit_code|module_path|user_account|\n" +
    "password_status|hash_alg|warning|expire|flag|\n" +
    "shmid|creator_uid|creator_pid|dtime|attached|locked|\n" +
    "description|allow_maximum|maximum_allowed|\n" +
    "screen_sharing|file_sharing|printer_sharing|remote_login|remote_management|remote_apple_events|internet_sharing|bluetooth_sharing|disc_sharing|content_caching|history_file|hash_resources|cdhash|team_identifier|authority|\n" +
    "config_flag|enabled_nvram|disk_id|driver_type|model_family|device_model|lu_wwn_device_id|additional_product_id|firmware_version|user_capacity|sector_sizes|rotation_rate|form_factor|in_smartctl_db|ata_version|transport_type|sata_version|read_device_identity_failure|smart_supported|smart_enabled|packet_device_type|power_mode|warnings|\n" +
    "number|handle|header_size|success|block|ssh_config_file|args|\n" +
    "header|rule_details|severity|tag|oid|subsystem|current_value|config_value|field_name|cpu_subtype|cpu_brand|cpu_physical_cores|cpu_logical_cores|cpu_microcode|physical_memory|hardware_vendor|hardware_version|hardware_serial|computer_name|celsius|fahrenheit|\n" +
    "weekday|year|day|minutes|seconds|timezone|local_time|local_timezone|unix_time|timestamp|iso_8601|win_timestamp|\n" +
    "destination_id|backup_date|\n" +
    "alias|destination_id|consistency_scan_date|root_volume_uuid|bytes_available|bytes_used|encryption|soft_limit|hard_limit|\n" +
    "days|hours|total_seconds|\n" +
    "usb_address|usb_port|subclass|removable|terminal|uid_signed|shell|\n" +
    "color_depth|driver_date|driver_version|series|video_mode|\n" +
    "free|speculative|throttled|wired|purgeable|faults|copy|zero_fill|reactivated|purged|file_backed|anonymous|uncompressed|compressor|decompressed|compressed|page_ins|page_outs|swap_ins|swap_outs|\n" +
    "ssid|network_name|security_type|last_connected|passpoint|possibly_hidden|roaming|roaming_profile|captive_portal|auto_login|temporarily_disabled|ssid|bssid|country_code|rssi|noise|channel|channel_width|channel_band|transmit_rate|\n" +
    "session_id|object_name|object_type|\n" +
    "datetime|module|tid|process_uptime|exception_code|exception_message|exception_address|command_line|current_directory|machine_name|major_version|minor_version|build_number|provider_name|provider_guid|eventid|task|keywords|command_line_template|executable_path|relative_path|query_language|\n" +
    "consumer|filter|scripting_engine|script_file_name|launch_type|identity|filetype|optional|uses_pattern|\n" +
    "identifier|min_version|user_action|matches|count|sig_group|sigfile|strings|baseurl|gpgcheck|gpgkey|target_path|utc_time|pe_file|process_guid|parent_process_guid|parent_pid|process_name|parent_path|src_pid|src_process_guid|target_pid|target_process_guid|src_path|granted_access|granted_access_value|function_name|module_name|\n" +
    "eid|\n" +
    "turbo_disabled|turbo_ratio_limt|\n" +
    "removable_media_event_type|\n" +
    "event_type|url|\n" +
    "product_type|product_name|product_state|product_signatures|image_path|sign_info|trust_info|num_of_certs|cert_type|pubkey|pubkey_length|pubkey_signhash_algo|signature_algo|subject_dn|issuer_dn|\n" +
    "script_id|time_created|obfuscated_state|obfuscated_score|request_type|request_class|resolved_ip|handle_type|access_mask|target_name|target_new_name|value_data|value_type|old_timestamp|new_timestamp|\n" +
    "sha1|image_size|image_memory_mode|image_base|\n" +
    "physical_memory_load|total_physical|available_physical|total_pagefile|available_pagefile|total_virtual|available_virtual|available_extended_memory|privileged_time|processor_time|thread_count|working_set|creating_process_id|elapsed_time|handle_count|io_data_bytes_per_sec|io_read_bytes_per_sec|io_read_ops_per_sec|io_write_bytes_per_sec|io_write_ops_per_sec|non_paged_pool_bytes|page_pool_bytes_peak|priority_base|private_bytes|working_set_peak|\n" +
    "logger_name|logger_watch_file|log_entry|dns_names|\n" +
    "process_dumps_location|modules_scanned|modules_suspicious|modules_replaced|modules_detached|modules_hooked|modules_implanted|modules_skipped|modules_errors|\n" +
    "carve_guid|carve|sig_group|sigfile";

@Component({
  selector: 'app-add-query',
  templateUrl: './add-query.component.html',
  styleUrls: ['./add-query.component.css']
})
export class AddQueryComponent implements OnInit {
  @ViewChild('editor', { static: true }) editor;
  addQuery: FormGroup;
  loading = false;
  submitted = false;
  public addQueryObj: any =  {
    interval:"3600",
    platform:"all"

  };
  public result:any;
  maxInputCharacters = (environment?.input_max_size)? environment.input_max_size : 256;
  maxTagCharacters = (environment?.max_tag_size)? environment.max_tag_size : 64;
  snapshot =false;
  error:any;
  Updated:any;
  text: string = "";
  queryText:string = "";
  pack_details:any;
  dropdownPacknameList = [];
  selectedPacknameItems = [];
  dropdownPacknameSettings = {};
  errorMessageTag: string;
  // selected_alerts :any =[];
  pack_data_names=["all-events-pack","binary-monitoring-pack","forensic-pack","hardware-monitoring","incident-response","it-compliance","user-creation-updation-pack","unwanted-chrome-extensions","osquery-monitoring","vuln-management","windows-attacks","windows-hardening"];
  createKeywordMapper = function (map, defaultToken, ignoreCase,) {
    var keywords = Object.create(null);
    var $keywordList = null;
    return Object.keys(map).forEach(function (className) {
      var a = map[className];
      ignoreCase && (a = a.toLowerCase());
      for (var list = a.split("|"), i = list.length; i--;) keywords[list[i]] = className;
    }), Object.getPrototypeOf(keywords) && (keywords.__proto__ = null), $keywordList = Object.keys(keywords), map = null, ignoreCase ? function (value) {
      return keywords[value.toLowerCase()] || defaultToken;
    } : function (value) {
      return keywords[value] || defaultToken;
    };
  };
  keywordMapper = this.createKeywordMapper({
    "osquerycolumn": all_columns,
    "support.function": builtinFunctions,
    keyword: keywords,
    "constant.language": dataTypes,
    "table": tables,
  }, "identifier", null);
  rules = {
    start: [{
      token: "comment",
      regex: "--.*$"
    }, {
      token: "comment",
      start: "/\\*",
      end: "\\*/"
    }, {
      token: "string",
      regex: '".*?"'
    }, {
      token: "string",
      regex: "'.*?'"
    }, {
      token: "constant.numeric",
      regex: "[+-]?\\d+(?:(?:\\.\\d*)?(?:[eE][+-]?\\d+)?)?\\b"
    }, {
      token: this.keywordMapper,
      regex: "[a-zA-Z_$][a-zA-Z0-9_$]*\\b"
    }, {
      token: "keyword.operator",
      regex: "\\+|\\-|\\/|\\/\\/|%|<@>|@>|<@|&|\\^|~|<|>|<=|=>|==|!=|<>|="
    }, {
      token: "paren.lparen",
      regex: "[\\(]"
    }, {
      token: "paren.rparen",
      regex: "[\\)]"
    }, {
      token: "text",
      regex: "\\s+"
    }]
  };

  constructor(private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
    private _location: Location,
    private router: Router,
    private titleService: Title,
    private tagsValidation:TagsValidationHandler,
private fb:FormBuilder) {
  this.addQuery= this.fb.group({
    name:['', [Validators.required, Validators.maxLength(this.maxInputCharacters)]],
    query:'',
    interval:['', [Validators.required, Validators.min(Number.MIN_VALUE),Validators.max(Number.MAX_VALUE)]],
    platform:'all',
    description:'',
    version:'',
    value:'',
    packs:'',
    tags:'',
    snapshot:'false',
    sql:'',

  })


 }


  initialise_query_editor() {
    this.editor.getEditor().setOptions({
      autoScrollEditorIntoView: true,
      theme: THEME,
      highlightSelectedWord: true,
      enableBasicAutocompletion: true,
      enableLiveAutocompletion: true
    });
    this.editor.getEditor().focus();
    var session = this.editor.getEditor().session;
    var rules = this.rules;
    session.setMode('ace/mode/' + 'text', function () {
        // force recreation of tokenizer
        session.$mode.$highlightRules.addRules(rules);
        session.$mode.$tokenizer = null;
        session.bgTokenizer.setTokenizer(session.$mode.getTokenizer());
        // force re-highlight whole document
        session.bgTokenizer.start(0);
      }
    );

    var staticWordCompleter = {
      getCompletions: function (editor, session, pos, prefix, callback) {
        var all_keywords = tables + "|" + keywords + "|" + all_columns + "|" + dataTypes + "|" + builtinFunctions;
        var all_keywords_list = all_keywords.split("|");
        callback(null, all_keywords_list.map(function (word) {
          var table_array = tables.split("|");
          var meta = '';
          if (keywords.includes(word)) {
            meta = 'keyword';
          } else if (builtinFunctions.includes(word)) {
            meta = 'function';
          } else if (table_array.includes(word)) {
            meta = 'table';
          } else if (all_columns.includes(word)) {
            meta = 'column';
          } else if (dataTypes.includes(word)) {
            meta = 'data_type';
          }
          return {
            caption: word,
            value: word,
            meta: meta
          };
        }));
      }
    }

    langTools.setCompleters([staticWordCompleter]);
    this.editor.completers = [staticWordCompleter];
    this.editor.getEditor().commands.addCommand({
      name: "runQuery",
      bindKey: {
        win: "Ctrl-Enter",
        mac: "Command-Enter"
      },
      exec: function require() {
        $(".query-editor__btn-run").trigger("click");
      }
    })
  }

 ngAfterViewInit() {
  this.initialise_query_editor();
  // this.dtTrigger.next();


}

ngOnInit() {
  if(localStorage.getItem('roles') == 'analyst'){
    this.navigateDashboard();
  }
  // LivequeryFunction();
  this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Add query");


  // this.editor.value ='';
  this.dropdownPacknameSettings = {
    singleSelection: false,
    text: "Nothing selected",
    selectAllText:'Select All',
    unSelectAllText:'UnSelect All',
    badgeShowLimit:2,
    enableSearchFilter:true,
    classes: "angular-multiselect-class",
    searchPlaceholderText: "Search Packs here.."
  };


this.commonapi.packs_api().subscribe((res: any) => {
  this.pack_details = res.data.results;
  for(const i in this.pack_details){
    if (this.pack_data_names.includes(this.pack_details[i].name)){
      // console.log(this.pack_details[i].name,"this.pack_details")
    }
    else
    this.pack_data_names.push(this.pack_details[i].name)
  }
  for(const i in this.pack_data_names){
    var pack_name={}
    pack_name["id"]=i
    pack_name["itemName"]=this.pack_data_names[i]
    this.dropdownPacknameList.push(pack_name)

}

});

}
 get f() { return this.addQuery.controls; }


// numberOnly(event): boolean {
//   const charCode = (event.which) ? event.which : event.keyCode;
//   if (charCode > 31 && (charCode < 48 || charCode > 57)) {
//     return false;
//   }
//   return true;

// }

  onSubmit(){
    this.submitted = true;
    if (this.addQuery.invalid) {
              return;
    }
    var snapshor_val = String(this.f.snapshot.value);
    var sql= this.editor._text;;
    console.log(this.f.platform.value);
    if(sql==""){
      swal({
        icon: 'warning',
        text:"Query field is required",
      })
    }
    else{
     this.addQueryObj= {
      "name":this.f.name.value,
      "query":sql,
      "interval":this.f.interval.value,
      "platform":this.f.platform.value == null ? "all" : this.f.platform.value,
      "description":this.f.description.value,
      "version":this.f.version.value,
      "value":this.f.value.value,
      "packs":this.getStringConcatinated(this.f.packs.value),
      "tags":this.f.tags.value,
      "snapshot":this.f.snapshot.value == null ? "false":String(this.f.snapshot.value)
      }

      let objQueryData = Object.assign({}, this.addQueryObj)
      if(!(this.tagsValidation.isEmpty(objQueryData["tags"]))){
        var isValidTagObject;
        isValidTagObject = this.tagsValidation.getAllTags(objQueryData["tags"]);
        if(isValidTagObject){
          this.errorMessageTag = '';
          objQueryData["tags"] = isValidTagObject;
        }
        else {
          this.errorMessageTag = 'Accepts only ' + this.maxTagCharacters + ' alpha numeric characters with @._-'
          return
        }
      }
      console.log("addQueryObj",this.addQueryObj)

    this.commonapi.queriesadd_api(objQueryData).subscribe((res: any) => {
      this.result=res;
      console.log("this.result",this.result.query_id)
            if(this.result && this.result.status === 'failure'){
              swal({
                icon: 'warning',
                title: this.result.status,
                text: this.result.message,
                buttons: [false],
                timer: 2000,
              })
            }else{
              swal({
                icon: 'success',
                title: this.result.status,
                text: this.result.message,
                buttons: [false],
                timer: 2000,
              })
              this.error = null;
              this.Updated = true;
              setTimeout(() => {
                let query_id=this.result.query_id
                this.router.navigate(['hostconfiguration/queries']);
                },2500);

            }
          },
          error => {
            console.log(error);
          }
        )
    }
  }

  getStringConcatinated(array_object){
    console.log(array_object,array_object,"array_object")
    //Join Array elements together to make a string of comma separated list
    let string_object = "";
    try{
      if (array_object.length>0){
        string_object = array_object[0].itemName;
        for (let index = 1; index < array_object.length; index++) {
          string_object = string_object+','+array_object[index].itemName;
        }
        return string_object
      }
    }
    catch(Error){
      return ""
    }
  }
  
  goBack(){
    this._location.back();
  }
  clearQuery(){
    this.queryText = "";
  }
  onItemSelect(item:any){
    console.log(item);
    console.log(this.selectedPacknameItems);
}
OnItemDeSelect(item:any){
    console.log(item);
    console.log(this.selectedPacknameItems);
}
onSelectAll(items: any){
    console.log(items);
}
onDeSelectAll(items: any){
    console.log(items);
}
navigateDashboard(){
  setTimeout(() => {
    this.router.navigate(['/dashboard']);
    },1500);
}
omitSpecialChar(event){
   return this.tagsValidation.omitSpecialChar(event)
}
}
