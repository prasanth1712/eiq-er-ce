import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
@Injectable({
  providedIn: 'root'
})
export class ValidDateFormat {
  constructor() { }

  public ValidDateFormat(value) {
    if(value) {
      let date = value.substring(0, 10);
      let time = value.substring(11, 19);
      let millisecond = value.substring(20)
      let year = date.split('-')[0];
      let month = date.split('-')[1];
      let day = date.split('-')[2];
      let validDate = year+'-'+month+'-'+day+ ' ' + time;
      return validDate
    }
  }

}
