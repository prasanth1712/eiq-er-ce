import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormControl, FormGroup, FormBuilder, Validators, FormArray } from '@angular/forms';
import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../dashboard/_services/commonvariable.service';
import swal from 'sweetalert';
import { Location } from '@angular/common';
import { Title } from '@angular/platform-browser';
import Swal from 'sweetalert2';
import { ToastrService } from 'ngx-toastr';
import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';
@Component({
  selector: 'app-change-user-password',
  templateUrl: './change-user-password.component.html',
  styleUrls: ['./change-user-password.component.css']
})
export class ChangeUserPasswordComponent implements OnInit {
  @Input() insideUserProfile: boolean = false
  @Output() viewParent = new EventEmitter<string>();
  changePassword: FormGroup;
  submitted = false;
  resetPassword:Boolean=JSON.parse(localStorage.getItem('reset_password'));
  isLoading:Boolean = false;
  constructor(
    private fb: FormBuilder,
    private commonapi:CommonapiService,
    private commonvariable: CommonVariableService,
    private _location: Location,
    private titleService: Title,
    private router: Router,
    private toastr: ToastrService,

  ) {   }

  ngOnInit() {
    if(JSON.parse(localStorage.getItem('reset_password'))){
      $('#kt_wrapper').addClass('ktWrapper');
    }else{
      $('#kt_wrapper').removeClass('ktWrapper');
    }
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Change password");
    this.changePassword= this.fb.group({
      existing_Password: [''],
      new_Password: [''],
      confirm_new_Password: ['']
    });

  }


  get f() { return this.changePassword.controls; }

  onSubmit() {
    this.submitted = true;
    if (this.f.existing_Password.value==undefined || this.f.new_Password.value==undefined || this.f.confirm_new_Password.value==undefined ||this.f.existing_Password.value=='' || this.f.new_Password.value=='' || this.f.confirm_new_Password.value=='') {
      this.toastr.error(" Please provide  Existing Password/New Password/ Confirm New Password ",'');
    }  else {
      Swal.fire({
        title: 'Are you sure want to update?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#518c24',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, Update!'
      }).then((result) => {
        if (result.value) {
        this.isLoading = true;
    this.commonapi.changePassword( this.f.existing_Password.value, this.f.new_Password.value, this.f.confirm_new_Password.value).subscribe(
      res => {
        if(res['status'] === 'failure'){
          this.toastr.error(res['message']);
          this.changePassword.reset();
          this.isLoading = false;
        }
        else{
          this.toastr.info("Successfully updated! Please login again");
          this.isLoading = false;
              setTimeout(() => {
                localStorage.removeItem('token');
                localStorage.removeItem('reset_password');
                localStorage.removeItem('roles');
                localStorage.removeItem('all_roles');
                this.router.navigate(['./authentication/login']);
                },2000);
        }
      },);
   }
    })
  }

  }
  goBack(){
    this._location.back();
   }
  
   toggle() {
    this.viewParent.emit(); //emit event here
  } 
}
