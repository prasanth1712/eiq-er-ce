# EclecticIQ Endpoint Response

The EclecticIQ Endpoint Response platform is a sophisticated and flexible endpoint monitoring and response platform. It provides endpoint monitoring and visibility, threat detection, and incident response for Security Operating Centers (SOCs).

The platform leverages the [osquery](https://osquery.io/) tool with the EclecticIQ [extension](https://github.com/EclecticIQ/osq-ext-bin). It focuses on osquery-based agent management and offers the following features:

- Visibility into endpoint activities
- Query configuration management
- Live query interface
- Alerting capabilities based on security critical events

## Available flavors

The EclecticIQ Endpoint Response platform is available in two flavors:

- Enterprise Edition
- Community Edition

The Enterprise Edition is the full version and it provides an advanced set of features and dedicated support. The Community Edition provides limited features and allows you to experience most product features.

Here are the high-level differences between the Community Edition and Enterprise Edition.

| Parameter | Description                                                                                                                                                                                  |
|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Response Action       |  This service is not available in the Community Edition. This service improves agent and server performance because response action based config plugin and distributed plugin overrides the continuous requests polling for new config and new live queries by enabling a notification system.                                     |
| Alerts Investigation       | This feature is not available in the Community Edition. This feature allows you to review timeline and process tree plots to understand the alert trend in your setup.                                         |
| User Notes     |   User notes for alerts are not available in the Community Edition.                                                                                                            |
| Security Centre       | This feature is not available in the Community Edition. The Security Centre allows you to manage Windows Defender for Windows-based endpoints. |                                                                         |  
| Live terminal       | This feature is not available in the Community Edition. The Live terminal provides a simple way to execute shell, batch, PowerShell commands remotely.        |
| Automatic download of YARA files        | Automatic download of YARA files only works on Windows in the Community Edition.                                         |
| Process tree graph on recent activity page       | This feature is not available in the Community Edition. In the Enterprise Edition, the recent activity page includes a process tree graph to help you understand the process activity.                                                                       |
| Default rules       | Predefined rule sets are not available in the Community Edition.                                                                            |
| Faster config refresh and Live query refresh       | This feature is not available in the Community Edition. In the Enterprise Edition, config refresh and live queries refresh are quick because of a notification system which inform agents about new updates. In contrast, the Community Edition uses  osquery tls plugin (latency based on refresh interval specified) that polls to server periodically for new config or live query changes.                                                                                 |  

For more information about the Enterprise Edition, see [this](https://github.com/EclecticIQ/eiq-er-docs) or contact [support](mailto:support@eclecticiq.com).

## Components

EclecticIQ Endpoint Response includes two primary components: server and client.

- The server receives, processes, and stores the data sent by the clients.
- The client is installed on each node and monitors all activity on the node. The EclecticIQ Endpoint Response client is based on osquery which is a security tool that exposes an entire operating system as a high-performance relational database that can be queried. Using SQL queries, we can extract and review operating system data, such as running processes, loaded kernel modules, open network connections, browser plugins, hardware events, and file hashes. The EclecticIQ Endpoint Response client extends existing osquery features by adding real time event collection and response capabilities.

## Product documentation

To learn more about the EclecticIQ Endpoint Response Community Edition, review the following:

- [EclecticIQ Endpoint Response Community Edition 3.5.1 Release Notes](docs/eiq_er_ce_release_notes.pdf)
- [EclecticIQ Endpoint Response Community Edition 3.5.1 Deployment Guide](docs/eiq_er_ce_deployment_guide.pdf)
- [EclecticIQ Endpoint Response Community Edition 3.5.1 Product Guide](docs/eiq_er_ce_product_guide.pdf)
- [EclecticIQ Endpoint Response Community Edition 3.5.1 Troubleshooting Guide](docs/eiq_er_ce_troubleshooting_guide.pdf)

## Integration with analytics systems

The EclecticIQ Endpoint Response server is packaged with an rSysLog container. This container can be configured to stream the query results and other logs from the endpoints to backend systems, such as Splunk, ELK, and GrayLog for cross-product correlation, alert enrichment, and other SIEM-related use cases.

To configure rSysLog forwarding, modify the [rsyslogd.conf](rSysLogF/rsyslogd.conf) file to specify the destination address of the server accepting logs in syslog format. In the absence of a destination address, the container may not come up. If needed, the container can be configured at a later point but will need to be manually started.

## License

Review the [LICENSE](LICENSE) file for details on the license for EclecticIQ Endpoint Response Community Edition.

## Contact us

For enquiries and questions, you can contact [support](mailto:support@eclecticiq.com).
