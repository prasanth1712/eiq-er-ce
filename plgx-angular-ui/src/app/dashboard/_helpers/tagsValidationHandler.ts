import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
@Injectable({
  providedIn: 'root'
})
export class TagsValidationHandler {
  errorMessageTag: string;
  maxTagCharacters = (environment?.max_tag_size)? environment.max_tag_size : 64;
  constructor() { }

  public omitSpecialChar(event) {
    var input = String.fromCharCode(event.keyCode);
    if (/[a-zA-Z0-9 @._-]/.test(input)) {
      return true;
    } else {
      event.preventDefault();
      return false;
    }
  }
  public isEmpty(data){
    if(data == '' || data == null || data == undefined){
      return true
    }
    else{
      return false;
    }
  }
  public validatePastedData(event) {
	  var pastedData = event?.clipboardData.getData('text/plain');
	  var regex = new RegExp("^[a-zA-Z0-9 @._-]+$");
	  if (!regex.test(pastedData)) {
          event.preventDefault();
          return false;
       }
       else{
        return true
       }
  }
  public validateData(data) {
	  var regex = new RegExp("^[a-zA-Z0-9 @._-]+$");
	  if (!regex.test(data)) {
          return false;
       }
       else{
        return true
       }
  }
  getAllTags(str) {
    var strArray = str.split("\n");
    var isValidTag = this.validateTags(str);
    if(!isValidTag){
      this.errorMessageTag = 'Accepts only alpha numeric characters with @._-'
      return;
    }
    else{
      this.errorMessageTag = ''
      return strArray.join(",").split(",,").join(",")
    }
  }
  public validateTags(str){
    var strArray = str.split("\n");
    let isInActiveTag:boolean;
    strArray = strArray.filter((item) => {
      if((!(this.validateData(item))) || item?.length > this.maxTagCharacters){
        isInActiveTag = false;
      }
    });
    if(isInActiveTag == false)
    return false;
    else
      return true;
  }
}
