import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { Location } from '@angular/common';
import { Title } from '@angular/platform-browser';
import Swal from 'sweetalert2';
import { ToastrService } from 'ngx-toastr';
import { Messagehandler } from '../../../dashboard/_helpers/messagehandler';
@Component({
  selector: 'app-alert-configuration',
  templateUrl: './alert-configuration.component.html',
  styleUrls: ['./alert-configuration.component.css']
})
export class AlertConfigurationComponent implements OnInit {
  alertConfigureSettings: FormGroup;
  submitted = false;
  constructor(
    private fb: FormBuilder,
    private commonapi:CommonapiService,
    private commonvariable: CommonVariableService,
    private toastr: ToastrService,
    private titleService: Title,
    private location: Location,
    private msgHandler:Messagehandler,
  ) { }

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Alert configuration");
    this.alertConfigureSettings = this.fb.group({
      alertAggregationDuration: ['', [Validators.required, Validators.min(Number.MIN_VALUE)]],
    });
    this.getAlertConfigureSettings();
  }
  get f() { return this.alertConfigureSettings.controls; }
  getAlertConfigureSettings(){
    this.commonapi.getConfigurationSettings().subscribe(res => {
    this.alertConfigureSettings.patchValue({
      alertAggregationDuration:res.data.alert_aggregation_duration,
     });
    });
  }

  onSubmit() {
    this.submitted = true;
    if (this.alertConfigureSettings.invalid) {
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
          let payload={"alert_aggregation_duration": this.f.alertAggregationDuration.value}
          this.commonapi.putConfigurationSettings(payload).subscribe(res => {
              if (res['status'] == 'success') {
              this.msgHandler.successMessage(res['status'],res['message'],false,2500);
                this.getAlertConfigureSettings()
              } else {
                this.msgHandler.warningMessage(res['status'],res['message']);
              }
            });
        }
      })
    }
  }
  goBack() {
    this.location.back();
  }
}
