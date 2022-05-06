import {Injectable} from '@angular/core';
import {Observable, Subject} from "rxjs";
import {WebsocketService} from "./websocket.service";
// import { map } from 'rxjs/add/operator/map'
// import { catchError, map } from 'rxjs/operators';
import {map} from "rxjs/operators";
import {environment} from '../../../environments/environment'
// import 'rxjs/add/operator/map';
// import 'rxjs/add/operator/catch';

export interface Message {
  query_id: string;
}

@Injectable()
export class ChatService {
  public messages: Subject<Message>;
  public text: any;
  private subjectData = new Subject<any>();

  constructor(wsService: WebsocketService) {
    console.log(window.location.href);
    var str = window.location.href;
    str = str.substr(str.indexOf(':') + 3);
    var socket_ip = str.substring(0, str.indexOf('/'));
    var live_url = environment.socket_url;
    var socket_url;
    if (live_url) {
      socket_url = environment.socket_url;
    } else {
      socket_url = 'wss://' + socket_ip + '/esp-ui/distributed/result';
    }
    console.log(this.messages);

    this.messages = <Subject<Message>>wsService.connect(socket_url).pipe(map(
      (response: MessageEvent): Message => {
        var blob = new Blob([response.data], {type: 'text/plain'});
        const reader: FileReader = new FileReader();
        reader.addEventListener('loadend', (event: Event) => {
          this.text = reader.result;

          console.log(this.text);
          this.subjectData.next(this.text);
          this.text = '';
        });
        reader.readAsText(blob);
        console.log(reader);

        return {
          query_id: response.data,

        };
      }
    ));

    // console.log(this.messages);
  }

  getText(): Observable<any> {
    return this.subjectData.asObservable();
  }
}
