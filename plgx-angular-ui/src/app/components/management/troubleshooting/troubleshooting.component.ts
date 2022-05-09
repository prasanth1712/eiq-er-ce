import { Component, OnInit } from '@angular/core';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { saveAs } from 'file-saver';
import { ToastrService } from 'ngx-toastr';
import Swal from 'sweetalert2';
import { Location } from '@angular/common';
import { Messagehandler } from '../../../dashboard/_helpers/messagehandler';
import {Router, ActivatedRoute} from '@angular/router';
import {Title} from '@angular/platform-browser';
@Component({
  selector: 'app-troubleshooting',
  templateUrl: './troubleshooting.component.html',
  styleUrls: ['./troubleshooting.component.css']
})
export class TroubleshootingComponent implements OnInit {
   serverName:string="ER";
   logFile:string="";
   logFileList=[];
   erLog:string = 'WARNING';
   erUILog:string = 'WARNING';
  constructor(
    private commonapi:CommonapiService,
    private commonvariable: CommonVariableService,
    private toastr: ToastrService,
    private location: Location,
    private msgHandler:Messagehandler,
    private router: Router,
    private titleService: Title
  ) {}

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Troubleshooting");
    if(localStorage.getItem('roles') == 'analyst'){
      this.navigateDashboard();
    }
    else{
      this.getLogEspServer();
      this.getLogEspUIServer();
      this.getLogFile();
    }
  }

  onChangeLog(val){
    this.serverName = val;
    this.getLogFile();
  }

  onChangeESP(val){
    this.erLog = val;
  }

  onChangeESPUI(val){
    this.erUILog = val;
  }

  getLogEspServer(){
    var payload = 'ER'
    this.commonapi.getLogServer(payload).subscribe(res => {
      if (res['status'] == 'success') {
        this.erLog = res['data'].log_level;
      }
    })
  }

  getLogEspUIServer(){
    var payload = 'ER-UI'
    this.commonapi.getLogServer(payload).subscribe(res => {
      if (res['status'] == 'success') {
        this.erUILog = res['data'].log_level
      }
    })
  }

  getLogFile(){
    this.commonapi.getLogFile(this.serverName).subscribe(res => {
      if (res['status'] == 'success') {
        this.logFileList = res['data'];
        this.logFile =this.logFileList[0]
      }
      else{
        this.toastr.warning(res['message']);
      }
    })
  }

  selectLogFileItem(fileName){
    this.logFile = fileName
  }

  UpdateLogServer(){
    var payload = {er_log_level:this.erLog,er_ui_log_level:this.erUILog}
    Swal.fire({
     title: 'Are you sure want to update?',
     icon: 'warning',
     showCancelButton: true,
     confirmButtonColor: '#518c24',
     cancelButtonColor: '#d33',
     confirmButtonText: 'Yes, Update!'
   }).then((result) => {
      if (result.value) {
        this.commonapi.updateLogSetting(payload).subscribe(res => {
          if (res['status'] == 'success') {
            this.msgHandler.successMessage(res['status'],res['message'],false,2500);
          }else{
            this.toastr.warning(res['message']);
          }
        })
      }
   })
  }

  submitDownloadLogs(){
    var payload = {server_name:this.serverName,filename:this.logFile}
    this.commonapi.downloadLog(payload).subscribe(res => {
      console.log(this.serverName);
      if(res == null){
        this.toastr.warning('No Data Found');
      }else{
        saveAs(res, this.logFile+".txt");
        this.msgHandler.successMessage("success","File Download Completed",false,2500);
      }

    })
  }

  goBack() {
    this.location.back();
  }
  navigateDashboard(){
    setTimeout(() => {
      this.router.navigate(['/dashboard']);
      },1500);
  }
}
