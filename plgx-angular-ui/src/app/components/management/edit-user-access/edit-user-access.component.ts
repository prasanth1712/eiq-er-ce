import { Component, OnInit } from '@angular/core';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import {Router, ActivatedRoute} from '@angular/router';
import Swal from 'sweetalert2';
import { ToastrService } from 'ngx-toastr';
import { Location } from '@angular/common';

@Component({
  selector: 'app-edit-user-access',
  templateUrl: './edit-user-access.component.html',
  styleUrls: ['./edit-user-access.component.css']
})
export class EditUserAccessComponent implements OnInit {
  EditUserForm: FormGroup;
  submitted = false;
  getuser:any
  userId:number
  roleslist=['admin','analyst']
  constructor(private commonapi: CommonapiService,private formBuilder: FormBuilder,private _Activatedroute: ActivatedRoute, private toaster: ToastrService, private _location: Location,  private router: Router,
    ) { }

  ngOnInit() {
    this._Activatedroute.params.subscribe(params => {
      this.userId=parseInt(params.id)
    })
    this.EditUserForm = this.formBuilder.group({
      userName: ['', [Validators.required,Validators.maxLength(48)]],
      firstName: ['',[Validators.required,Validators.maxLength(25)]],
      lastName: ['',Validators.maxLength(25)],
      email: ['',[Validators.required,Validators.pattern("[a-zA-Z0-9.-]{1,}@[a-zA-Z.-]{2,}[.]{1}[a-zA-Z]{3,}")]],
      role: ['',Validators.required],
      status:[''],
      enable_sso:['']
    },);
    this.commonapi.getUser(this.userId).subscribe(res=>{
      this.getuser=res['data'];
      this.EditUserForm.patchValue({
        userName: this.getuser.username,
        firstName: this.getuser.first_name,
        lastName: this.getuser.last_name,
        email: this.getuser.email,
        role:this.getuser.roles[0],
        status:this.getuser.status,
        enable_sso:this.getuser.enable_sso
      })
    },(error) => {
       if(error.status==403){
         //Navigate to dashboard page while Unauthorize user trying to access user administration page
         this.navigateDashboard();
       }
     });
   }
  get f() { return this.EditUserForm.controls; }

  onSubmit() {
    this.submitted = true;
    // stop here if form is invalid
    if (this.EditUserForm.invalid) {
        return;
    }
    let payload={
    "new_user_name": this.f.userName.value,
     "first_name": this.f.firstName.value,
     "last_name": this.f.lastName.value,
     "email": this.f.email.value,
     "role": this.f.role.value,
     "status": this.f.status.value,
     "enable_sso":this.f.enable_sso.value
     }
     Swal.fire({
      title: 'Please Wait..',
      onBeforeOpen: () => {
        Swal.showLoading()
      }
    })
    this.commonapi.editUserForm(this.getuser.id,payload).subscribe(res=>{
        Swal.close()
        if(res['status']=='success'){
          this.toaster.success(res['message']);
          setTimeout(() => {
            this.router.navigate(['/management/UserAdministration']);
            },1500);
        }else{
          this.toaster.error(res['message']);
        }
    },(error) => {
      Swal.close();
      if(error.status==403){
        //Navigate to dashboard page while Unauthorize user trying to access user administration page
        this.navigateDashboard();
      }
    })
  }
  goBack(){
    this._location.back();
  }
  navigateDashboard(){
    setTimeout(() => {
      this.router.navigate(['/dashboard']);
      },1500);
  }
}
