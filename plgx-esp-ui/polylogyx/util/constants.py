DEFAULT_EVENT_STATE_QUERIES = {
    "windows": {
        "event_queries": [
            'win_file_events',
            'win_process_events',
            'win_process_open_events',
            'win_remote_thread_events',
            'win_pe_file_events',
            'win_removable_media_events',
            'win_http_events',
            'win_socket_events',
            'win_image_load_events',
            'win_dns_events',
            'win_dns_response_events',
            'win_registry_events',
            'win_ssl_events',
            'windows_events',
            'windows_real_time_events',
            'windows_defender_events'
        ],
        "state_queries": [
            'win_epp_table',
            'patches',
            'os_version',
            'kernel_info',
            'startup_items',
            'drivers',
            'etc_hosts',
            'osquery_info',
            'wmi_cli_event_consumers',
            'wmi_script_event_consumers',
            'users',
            'uptime',
            'certificates',
            'chrome_extensions',
            'ie_extensions',
            'scheduled_tasks',
            'appcompat_shims',
            'powershell_events_script_blocks'
        ]
    },
    "linux": {
        "event_queries": [
            'process_events',
            'socket_events',
            'file_events',
            'hardware_events'
        ],
        "state_queries": [
            'etc_hosts',
            'deb_packages',
            'iptables',
            'kernel_info',
            'osquery_info',
            'rpm_packages'
        ]
    },
    "darwin": {
        "event_queries": [
            'process_events',
            'socket_events',
            'file_events',
            'hardware_events'
        ],
        "state_queries": [
            'chrome_extensions',
            'etc_hosts',
            'homebrew_packages',
            'osquery_info',
            'startup_items'
        ]
    },
    "freebsd": {
        "event_queries": [
            'process_events'
        ],
        "state_queries": []
    }
}


DEFAULT_PROCESS_GRAPH_QUERIES = {
        "win_file_events": '1',
        "win_file_timestomp_events": '16',
        "win_http_events": '8',
        "win_pefile_events": '17',
        "win_process_events": '2',
        "win_registry_events": '13',
        "win_socket_events": '10',
        "win_ssl_events": '9',
        "win_defender_events": '18',
        "win_named_pipe_events": '19'
}

