import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpErrorResponse} from '@angular/common/http';
import swal from 'sweetalert';
import { msg } from '../../dashboard/_helpers/common.msg';
import { throwError} from 'rxjs';
@Injectable({
  providedIn: 'root'
})
export class Errorhandler {
  constructor() { }

  public handleError(errorResponse:HttpErrorResponse) {
    console.log(errorResponse);
    if(errorResponse.status==500 || errorResponse.status==502 || errorResponse.status==504){
      swal({
        icon: "warning",
        text: msg.failuremsg,
        buttons: {cancel: {text: "Close",value: null,visible: true,closeModal: true},
        },
      })
    }
    if(errorResponse.error instanceof ErrorEvent){
      console.log(errorResponse.error.message)
    }
    return throwError(errorResponse)
  }

}
