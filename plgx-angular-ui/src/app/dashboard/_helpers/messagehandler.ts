import { Injectable } from '@angular/core';
import Swal from 'sweetalert2';
@Injectable({
  providedIn: 'root'
})
export class Messagehandler {
  constructor() { }

    public successMessage(title,text,isButton,timer) {
      Swal.fire({
        icon: 'success',
        title: title,
        text: text,
        timer: timer,
        showConfirmButton: isButton,
      })
     }

    public warningMessage(title,text) {
    Swal.fire({
      icon: 'warning',
      title: title,
      text: text,
    })
  }


}
