import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { Location } from '@angular/common';
import { Title } from '@angular/platform-browser';
import Swal from 'sweetalert2';
import { ToastrService } from 'ngx-toastr';
import { Messagehandler } from '../../../dashboard/_helpers/messagehandler';
import {Router, ActivatedRoute} from '@angular/router';
@Component({
  selector: 'app-sso-configuration',
  templateUrl: './sso-configuration.component.html',
  styleUrls: ['./sso-configuration.component.css']
})
export class SsoConfigurationComponent implements OnInit {
  ssoConfigureSettings: FormGroup;
  submitted = false;
  constructor(
    private fb: FormBuilder,
    private commonapi:CommonapiService,
    private commonvariable: CommonVariableService,
    private toastr: ToastrService,
    private titleService: Title,
    private location: Location,
    private msgHandler:Messagehandler,
    private router: Router
  ) { }

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"SSO Settings");
    const urlRegex = /^((http|https|ftp|www|wss):\/\/)?([a-zA-Z0-9\~\!\@\#\$\%\^\&\*\(\)_\-\=\+\\\/\?\.\:\;\'\,]*)(\.)([a-zA-Z0-9\~\!\@\#\$\%\^\&\*\(\)_\-\=\+\\\/\?\.\:\;\'\,]+)/g;
    this.ssoConfigureSettings = this.fb.group({
      samlAuthentication: [false],
      idpMetadataUrl: ['', [Validators.required, Validators.pattern(urlRegex)]],
      appName: ['',Validators.required],
      entityId: ['',Validators.required]
    });
    this.getPlatformSettings();
    if(localStorage.getItem('roles') == 'analyst'){
      this.navigateDashboard();
    }
  }

  getPlatformSettings(){
    this.commonapi.getConfigurationSettings().subscribe(res => {
      if(res.data.hasOwnProperty('sso_configuration')){
        this.ssoConfigureSettings.patchValue({
          samlAuthentication: JSON.parse(res.data.sso_enable),
          idpMetadataUrl:  res.data.sso_configuration.idp_metadata_url,
          appName: res.data.sso_configuration.app_name,
          entityId: res.data.sso_configuration.entity_id
        });
      }
    });
  }

  get f() { return this.ssoConfigureSettings.controls; }

  onSubmit() {
    this.submitted = true;
    if (this.ssoConfigureSettings.invalid) {
        return;
    }
      Swal.fire({
        title: 'Are you sure want to update?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#518c24',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, Update!'
      }).then((result) => {
        if (result.value) {
          let payload={"sso_enable": String(this.f.samlAuthentication.value),
                       "sso_configuration":{"idp_metadata_url":this.f.idpMetadataUrl.value,"app_name":this.f.appName.value,"entity_id":this.f.entityId.value,}
           }
          this.commonapi.putConfigurationSettings(payload).subscribe(res => {
              if (res['status'] == 'success') {
                this.msgHandler.successMessage(res['status'],res['message'],false,2500);
              } else {
                this.msgHandler.warningMessage(res['status'],res['message']);
              }
            });
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
