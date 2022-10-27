// This file can be replaced during build by using the `fileReplacements` array.
// `ng build --prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,

  api_url:"https://localhost:5001/services/api/v1",
  socket_url: 'wss://localhost:5001/distributed/result',
  liveTerminal_response_socket_url: 'wss://localhost:5001/action/result',
  Statuslog_Export_Socketurl:"wss://localhost:5001/csv/export",
  file_max_size: 2097152,
  input_max_size: 256,
  max_tag_size: 64,
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/plugins/zone-error';  // Included with Angular CLI.
