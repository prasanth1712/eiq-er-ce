import { Pipe, PipeTransform } from '@angular/core';
import * as moment from 'moment';
import { DatePipe } from '@angular/common';
@Pipe({
  name: 'dateTimeFormatFilter'
})


export class DateTimeFormatPipe implements PipeTransform {
  transform(value: any): any {

    if (value) {
        const temp = value.toString().replace(' ', 'T');
        const datetime=new Date(temp);
        var conv = new Date(temp).toString();
          if (conv.includes('+0530 (India Standard Time)')) {
            conv = conv.replace('+0530 (India Standard Time)', '');
          }
        


        return conv;
    } else {
        return null;
    }
}
}


// transform(value: any, args?: any): any {
//   return super.transform(value, "EEEE d MMMM y h:mm a");
// }
// }


