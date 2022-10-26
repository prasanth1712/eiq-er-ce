import { Component, OnInit } from '@angular/core';
import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import Swal from 'sweetalert2';
import swal from 'sweetalert';
import { ToastrService } from 'ngx-toastr';
import { Location } from '@angular/common';
import {Title} from '@angular/platform-browser';
import { CommonVariableService } from '../../dashboard/_services/commonvariable.service';
@Component({
  selector: 'app-user-profile',
  templateUrl: './user-profile.component.html',
  styleUrls: ['./user-profile.component.css']
})
export class UserProfileComponent implements OnInit {
  editUserInformationForm:FormGroup;
  userName:string;
  email:string;
  role:string;
  submitted = false;
  viewChangePassword: boolean = false;
  constructor(private commonapi: CommonapiService,private formBuilder: FormBuilder,private toaster: ToastrService, private _location: Location,private titleService: Title,
    private commonvariable: CommonVariableService,) { }

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"User profile");
    this.editUserInformationForm = this.formBuilder.group({
      firstName: ['',Validators.required],
      lastName: [''],
    })
    this.getUserDetail();
  }
  getUserDetail(){
    this.commonapi.getUserDetails().subscribe(response=>{
      this.role=response['data'].roles[0];
      this.userName = response['data'].username;
      this.email = response['data'].email;
      this.editUserInformationForm.patchValue({
        firstName: response['data'].first_name,
        lastName: response['data'].last_name,
      });
    })
  }
  toggleViewChangePassword(){
    console.log('some')
    this.viewChangePassword = !this.viewChangePassword
  }
  get k() { return this.editUserInformationForm.controls; }
  editUserInformation(){
    this.submitted = true;
    if (this.editUserInformationForm.invalid) {
        return;
    }
      Swal.fire({
        title: 'Please Wait..',
        onBeforeOpen: () => {
          Swal.showLoading()
        }
      })
      this.commonapi.changeUserDetails({first_name:this.k.firstName.value.trim(),last_name:this.k.lastName.value.trim()}).subscribe(response=>{
        Swal.close()
        if(response['status']=='success'){
          swal({
            icon: 'success',
            title: 'success',
            text: response['message'],
            buttons: [false],
            timer: 2000

          })

        }else{
          this.toaster.error(response['message']);
        }

      })
  }
  resetData(){
    this.getUserDetail();
  }
  goBack(){
    this._location.back()
  }
  onChange(event){
   if(event.which ===32 && this.k.firstName.value.trim() == ''){event.preventDefault();}
   if(event.which ===32 && this.k.lastName.value.trim() == ''){event.preventDefault();}
  }
}
