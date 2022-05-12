import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import { Location } from '@angular/common';
import { Title } from '@angular/platform-browser';
import Swal from 'sweetalert2';
import { ToastrService } from 'ngx-toastr';
import { Messagehandler } from '../../../dashboard/_helpers/messagehandler';
@Component({
  selector: 'app-data-purge',
  templateUrl: './data-purge.component.html',
  styleUrls: ['./data-purge.component.css']
})
export class DataPurgeComponent implements OnInit {
  hasAcess=this.authorizationService.hasAccess()
  dataRetentionSettings: FormGroup;
  manualDataPurge:FormGroup;
  submitted = false;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess};
  constructor(
    private fb: FormBuilder,
    private commonapi:CommonapiService,
    private commonvariable: CommonVariableService,
    private toastr: ToastrService,
    private titleService: Title,
    private location: Location,
    private authorizationService: AuthorizationService,
    private msgHandler:Messagehandler,
  ) { }

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Data purge");
    this.dataRetentionSettings = this.fb.group({
      purgeDataDuration: ['', [Validators.required, Validators.min(Number.MIN_VALUE)]],
    });
    this.manualDataPurge = this.fb.group({
      manualDataPurgeval: ['',[Validators.required, Validators.min(Number.MIN_VALUE)]],
    });
    this.getDataRetention();
  }

  get f() { return this.dataRetentionSettings.controls; }
  get g() { return this.manualDataPurge.controls; }

  getDataRetention(){
    this.commonapi.getConfigurationSettings().subscribe(res => {
    this.dataRetentionSettings.patchValue({
      purgeDataDuration: res.data.purge_data_duration
    });
    });
  }

  onSubmit() {
    this.submitted = true;
    if (this.dataRetentionSettings.invalid) {
      return;
    }
    else {
      Swal.fire({
        title: 'Are you sure want to update?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#518c24',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, Update!'
      }).then((result) => {
        if (result.value) {
          let payload={"purge_data_duration":this.f.purgeDataDuration.value}
          this.commonapi.putConfigurationSettings(payload).subscribe(res => {
              if (res['status'] == 'success') {
                this.msgHandler.successMessage(res['status'],res['message'],false,2500);
                this.getDataRetention();
              } else {
                this.msgHandler.warningMessage(res['status'],res['message']);
              }
            });
        }
      })
    }
  }

  onSubmitDataPurge(){
    if (this.manualDataPurge.invalid) {
      this.toastr.warning('Retention days should not be empty');
      return;
    }
    else {
     Swal.fire({
      title: 'Are you sure want to purge?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#518c24',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Yes, Purge!'
    }).then((result) => {
       if (result.value) {
          var payload = {rentention_days:this.g.manualDataPurgeval.value}
          this.commonapi.manualPurge(payload).subscribe(res => {
           if (res['status'] == 'success') {
              this.msgHandler.successMessage(res['status'],res['message'],false,2500);
              this.manualDataPurge = this.fb.group({
              manualDataPurgeval: [''],
              });
            }
           else{
             this.toastr.warning(res['message']);
           }
       })
     }
    })
  }
  }

  goBack() {
    this.location.back();
  }

}
