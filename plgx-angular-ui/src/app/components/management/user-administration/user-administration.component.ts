import { Component, OnInit,ViewChild } from '@angular/core';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import Swal from 'sweetalert2';
import { ToastrService } from 'ngx-toastr';
import { Location } from '@angular/common';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import {Router, ActivatedRoute} from '@angular/router';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import {Title} from '@angular/platform-browser';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
class DataTablesResponse_platformActivity {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
@Component({
  selector: 'app-user-administration',
  templateUrl: './user-administration.component.html',
  styleUrls: ['./user-administration.component.css']
})
export class UserAdministrationComponent implements OnInit {
  @ViewChild(DataTableDirective, {static: false})
  dtElement_userDetails: DataTableDirective;
  dtTrigger_userDetails: Subject<any> = new Subject();
  dtOptions_userDetails: DataTables.Settings = {};
  dtElement_platformAcitivity: DataTableDirective;
  dtTrigger_platformAcitivity: Subject<any> = new Subject();
  dtOptions_platformAcitivity: DataTables.Settings = {};
  usersList:any;
  createUserForm: FormGroup;
  changeUserPasswordForm:FormGroup
  submitted = false;
  roleslist=['admin','analyst'];
  userId:number
  userName:string
  PlatformActivity=[]

  errorMessage:string
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  constructor(private commonapi: CommonapiService,private formBuilder: FormBuilder,private toaster: ToastrService, private _location: Location,private authorizationService: AuthorizationService,
    private http: HttpClient,private router: Router,private titleService: Title,private commonvariable: CommonVariableService) { }

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"User management");
    this.createUserForm = this.formBuilder.group({
      userName: ['', [Validators.required,Validators.maxLength(48)]],
      firstName: ['',[Validators.maxLength(25),Validators.required]],
      lastName: ['',Validators.maxLength(25)],
      PassWord: ['', Validators.required],
      email: ['',[Validators.required,Validators.pattern("[a-zA-Z0-9.-]{1,}@[a-zA-Z.-]{2,}[.]{1}[a-zA-Z]{3,}")]],
      role: ['admin',Validators.required],
      enable_sso:[false]
      },);
      this.changeUserPasswordForm = this.formBuilder.group({
        passWord: ['',Validators.required],
      })
    this.dtOptions_userDetails = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: true,
      "language": {
        "search": "Search: "
      },
      ajax: (dataTablesParameters: any,callback) => {
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(body.search.value!= ""  &&  body.search.value.length>=1)
        {
          body['searchterm']=body.search.value;
        }
        if(body['searchterm']==undefined){
          body['searchterm']="";
        }
        this.http.get<DataTablesResponse>(environment.api_url+"/users"+"?searchterm="+body['searchterm']+"&start="+body['start']+"&limit="+body['limit'],{ headers: {'x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
        this.usersList=res.data['results']
        if(this.usersList.length >0 &&  this.usersList!=undefined)
        {
          $('.dataTables_filter').show()
          $('#test'+'_paginate').show();
          $('#test'+'_info').show();
        }
        else{
          if(body.search.value=="" || body.search.value == undefined)
          {
            this.errorMessage="No users found. You may create new user";
          }
          else{
            this.errorMessage="No Matching Record Found";
          }
          $('#test'+'_paginate').hide();
          $('#test'+'_info').hide();
        }
          callback({
            recordsTotal: res['data']['total_count'],
            recordsFiltered: res['data']['count'],
            data: []
          });
        },(error) => {
          if(error.status==403){
            //Navigate to dashboard page while Unauthorize user trying to access user administration page
            this.navigateDashboard();
          }
        });
      },
      ordering: false,
      columns: [{ data: 'User' }, { data: 'First Name' }, { data: 'Last Name' }, { data: 'Email' },{ data: 'Role' },{ data: 'Status' },{ data: ' ' }]
    }

    this.dtOptions_platformAcitivity = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: false,
      searching: true,
      destroy: true,
      "language": {
        "search": "Search: "
      },
      ajax: (dataTablesParameters: any,callback) => {
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(body.search.value!= ""  &&  body.search.value.length>=1)
        {
          body['searchterm']=body.search.value;
        }
        if(body['searchterm']==undefined){
          body['searchterm']="";
        }
        this.http.get<DataTablesResponse_platformActivity>(environment.api_url+"/users/platform_activity"+"?&limit="+body['limit']+"&searchterm="+body['searchterm']+"&start="+body['start'],{ headers: {'x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
        this.PlatformActivity=[]
        var resultActivity = res['data']['results'];
        for(var i in resultActivity){
          if(resultActivity[i].item){
            if(resultActivity[i].item.type){
              var type = resultActivity[i].item.type;
              if(resultActivity[i].item.type=='Rule'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='Tag'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='Query'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='Pack'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='Config'){
                var start = type + " of platform '"+resultActivity[i].item.platform+"' with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='Settings'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='DefaultFilters'){
                var start = type + " of platform '"+resultActivity[i].item.platform+"' with config name '"+resultActivity[i].item.config_name+"'";
              }else if(resultActivity[i].item.type=='DefaultQuery'){
                var start = type + " of platform '"+resultActivity[i].item.platform+"' with config name '"+resultActivity[i].item.config_name+"'";
              }else if(resultActivity[i].item.type=='NodeConfig'){
                var start = type + " of the node with name '"+resultActivity[i].item.hostname+"'";
              }else if(resultActivity[i].item.type=='ThreatIntelCredentials'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='IOCIntel'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='VirusTotalAvEngines'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='Alerts'){
                var start = type + " with id '"+resultActivity[i].item.id+"'";
              }else if(resultActivity[i].item.type=='Node'){
                var start = type + " with name '"+resultActivity[i].item.name+"'";
              }else if(resultActivity[i].item.type=='CarveSession'){
                var start = type + " with session id '"+resultActivity[i].item.session_id+"'";
              }
              this.PlatformActivity.push({"data": start + " has been " + resultActivity[i].action + " by " + resultActivity[i].user.username,"time":resultActivity[i].created_at})
            }
          }else if(resultActivity[i].text){
            var text = resultActivity[i].text;
            this.PlatformActivity.push({"data": text + " by " + resultActivity[i].user.username,"time":resultActivity[i].created_at})
          }

        }
          if (this.PlatformActivity.length > 0 && this.PlatformActivity != undefined) {
            $('.dataTables_filter').show()
            $('#platformActivity' + '_paginate').show();
            $('#platformActivity' + '_info').show();
          }
          else {
            if (body.search.value == "" || body.search.value == undefined) {
              this.errorMessage = "No Activity found";
            }
            else {
              this.errorMessage = "No Matching Record Found";
            }
            $('#platformActivity' + '_paginate').hide();
            $('#platformActivity' + '_info').hide();
          }
          callback({
            recordsTotal: res['data']['total_count'],
            recordsFiltered: res['data']['count'],
            data: []
          });
        });
      },
      ordering: false,
      columns: [{ data: 'Activity'}]
    }
  }
  get g() { return this.createUserForm.controls; }
  get f() { return this.changeUserPasswordForm.controls; }
//start:: createUser
  createUserSubmitForm() {
    this.submitted = true;
    // stop here if form is invalid
    if (this.createUserForm.invalid) {
        return;
    }
    let payload={
      "username": this.g.userName.value,
      "first_name": this.g.firstName.value,
      "last_name": this.g.lastName.value,
      "password": this.g.PassWord.value,
      "email": this.g.email.value,
      "role": this.g.role.value,
      "enable_sso":this.g.enable_sso.value
      }
    this.callLoader()
    this.commonapi.createUser(payload).subscribe(res=>{
      Swal.close()
      if(res['status']=='success'){
        this.toaster.success(res['message']);
        setTimeout(() => {
          this.dtElement_userDetails.dtInstance.then((dtInstance: DataTables.Api) => {
            dtInstance.destroy();
            this.dtTrigger_userDetails.next();
          });
      },500);
      this.close_AddUser_modal()
      }else{
        this.toaster.error(res['message']);
      }
      },(error) => {
        if(error.status==403){
          Swal.close();
          //Navigate to dashboard page while Unauthorize user trying to load user administration page
          this.navigateDashboard();
        }
      })
  }
  createUserFormModal(){
    let modal = document.getElementById("createUserFormModel");
    this.createUserForm.get('role').setValue(this.roleslist[0]);
    this.createUserForm.get('enable_sso').setValue(false);
    modal.style.display = "block";
  }

  close_AddUser_modal() {
    this.submitted = false;
    this.createUserForm.reset()
    let modal = document.getElementById("createUserFormModel");
    modal.style.display = "none";
  }
//End:: createUser

//Start:: changeUserPassword
  changeUserPasswordSubmitForm(){
    this.submitted = true;
    // stop here if form is invalid
    if (this.changeUserPasswordForm.invalid) {
        return;
    }
    this.callLoader()
    this.commonapi.changeUserPassword(this.userId,{new_password:this.f.passWord.value}).subscribe(res=>{
      Swal.close()
      if(res['status']=='success'){
        this.toaster.success(res['message']);
        this.closeChangePasswordModal()
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
  changePasswordModal(userId,userName){
    this.userId=userId
    this.userName=userName
    let modal = document.getElementById("changePasswordFromModal");
    modal.style.display = "block";
  }
  closeChangePasswordModal(){
    this.submitted = false;
    this.changeUserPasswordForm.reset()
    let modal = document.getElementById("changePasswordFromModal");
    modal.style.display = "none";
  }
//End:: changeUserPassword
  callLoader(){
    Swal.fire({
      title: 'Please Wait..',
      onBeforeOpen: () => {
        Swal.showLoading()
      }
    })
  }
  goBack(){
    this._location.back()
  }
  navigateDashboard(){
    setTimeout(() => {
      this.router.navigate(['/dashboard']);
      },1500);
}
  ngAfterViewInit(): void {
    this.dtTrigger_userDetails.next();
    this.dtTrigger_platformAcitivity.next();
  }
}
