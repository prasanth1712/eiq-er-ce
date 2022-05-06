// This file can be replaced during build by using the `fileReplacements` array.
// `ng build --prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  // console.log(window.location.origin);
  production: false,

  api_url:"https://localhost/esp-ui/services/api/v1",
  socket_url: 'wss://localhost/distributed/result',
  liveTerminal_response_socket_url: 'wss://localhost/websocket/action/result',
  Statuslog_Export_Socketurl:"wss://localhost/websocket/csv/export"

  // api_url:"https://localhost:5000/services/api/v0",
  // socket_url: 'wss://localhost:5000/distributed/result'
};

/*'https://13.234.136.159:5000/services/api/v0'
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.
