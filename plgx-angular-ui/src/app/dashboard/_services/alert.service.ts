import { Injectable } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AlertService {

  public editDataDetails: any = [];
  public subject = new Subject<any>();
  private alertNavData = new BehaviorSubject(this.editDataDetails);
  resData = this.alertNavData.asObservable();
  constructor() { }
  getAlertData(data) {
    this.alertNavData.next(data);
  }
}
