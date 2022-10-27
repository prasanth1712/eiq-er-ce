import { Component, OnInit,ViewChild } from '@angular/core';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { FormBuilder, FormGroup, Validators ,FormControl} from '@angular/forms';
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
  @ViewChild(DataTableDirective)
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
  userDetailSearchTerm: any;
  platformAcitivitySearchTerm: any;
  errorMessage:string;
  roleOptions = [
    { value: 'any', description: 'any' },
    { value: 'admin', description: 'admin' },
    { value: 'analyst', description: 'analyst' },
  ];
  statusOptions = [
    { value: 'any', description: 'any' },
    { value: 'true', description: 'Active' },
    { value: 'false', description: 'Inactive' },
  ];
  roleSelectControl = new FormControl('any');
  statusSelectControl = new FormControl('any');
  selectedRoleFilter : string = "any";
  selectedStatusFilter : string = "any";
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  constructor(private commonapi: CommonapiService,private formBuilder: FormBuilder,private toaster: ToastrService, private _location: Location,private authorizationService: AuthorizationService,
    private http: HttpClient,private router: Router,private titleService: Title,private commonvariable: CommonVariableService,) { }

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"User management");
    this.selectedRoleFilter = "any";
    this.selectedStatusFilter = "any";
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
      this.getUserDetails();
      this.getPlatformAcitivity();
      this.platformSearch();
  }
  getUserDetails(){
    this.dtOptions_userDetails = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: false,
      dom: "<'row'<'col-sm-12'f>>" +
      "<'row table-scroll-hidden flex-1'<'col-sm-12 mt-18 table-scroll full-height'tr>>" +
      "<'row table-controls custom-pagination-margin'<'col-sm-6 table-controls-li pl-0'li><'col-sm-6 pr-0'p>>",
      "initComplete": function (settings, json) {
        $("#test").wrap("<div class='flex-flow-col'></div>");
       },
      "language": {
        "search": "Search: ",
        "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
        "info" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries",
        "infoFiltered": ""
      },
      ajax: (dataTablesParameters: any,callback) => {
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(this.userDetailSearchTerm){
          body['searchterm'] = this.userDetailSearchTerm
        }
        if(this.userDetailSearchTerm!= ""  &&  this.userDetailSearchTerm?.length>=1){
           body['searchterm']=this.userDetailSearchTerm;
        }
        if(body['searchterm']==undefined){
            body['searchterm']="";
        }
        let urlOption = ''
        if (body.order != "" && body.order.length >= 1) {
          body["column"] = body.columns[body.order[0].column].data;
          body["order_by"] = body["order"][0].dir;
          urlOption = environment.api_url+"/users"+"?searchterm="+body['searchterm']+"&start="+body['start']+"&limit="+body['limit']+"&column="+body["column"]+"&order_by="+body["order_by"];
        }
        else{
          urlOption = environment.api_url+"/users"+"?searchterm="+body['searchterm']+"&start="+body['start']+"&limit="+body['limit'];
        }
        // debugger;
        if(this.selectedRoleFilter!=" " && this.selectedRoleFilter != 'any'){
          urlOption = urlOption+"&role="+this.selectedRoleFilter;
        }
        if(this.selectedStatusFilter!=" " && this.selectedStatusFilter != 'any'){
          urlOption = urlOption+"&status="+this.selectedStatusFilter;
        }
        this.http.get<DataTablesResponse>(urlOption,{ headers: {'x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
        this.usersList=res.data['results']
        if(this.usersList.length >0 &&  this.usersList!=undefined)
        {
          $('.dataTables_filter').show()
          $('#test'+'_paginate').show();
          $('#test'+'_info').show();
        }
        else{
          if(body.searchterm=="" || body.searchterm == undefined)
          {
            if(this.selectedStatusFilter == 'false'){this.errorMessage="No users found."}
             else{this.errorMessage="No users found. You may create new user";}
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
      ordering: true,
      order: [],
      columnDefs: [{
        targets: [1,2,3,4,5,6], /* column index */
        orderable: false
      }],
      columns: [{ data: 'username' }, { data: 'first_name' }, { data: 'last_name' }, { data: 'email' },{ data: 'Role' },{ data: 'Status' },{ data: ' ' }]
    }
  }

  getPlatformAcitivity(){
    this.dtOptions_platformAcitivity = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: false,
      searching: false,
      destroy: true,
      dom: "<'row'<'col-sm-12'f>>" +
      "<'row table-scroll-hidden'<'col-sm-12 mt-18 table-scroll full-height'tr>>" +
      "<'row table-controls custom-pagination-margin'<'col-sm-6 table-controls-li pl-0'li><'col-sm-6 pr-0'p>>",
      "language": {
        "search": "Search: ",
        "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
        "info" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries",
      },
      ajax: (dataTablesParameters: any,callback) => {
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(this.platformAcitivitySearchTerm){
          body['searchterm'] = this.platformAcitivitySearchTerm
        }
        if(this.platformAcitivitySearchTerm!= ""  &&  this.platformAcitivitySearchTerm?.length>=1){
           body['searchterm']=this.platformAcitivitySearchTerm;
        }
        if(body['searchterm']==undefined){
            body['searchterm']="";
        }
        this.http.get<DataTablesResponse_platformActivity>(environment.api_url+"/users/platform_activity"+"?&limit="+body['limit']+"&searchterm="+body['searchterm']+"&start="+body['start'],{ headers: {'x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
        this.PlatformActivity=[]
        var resultActivity = res['data']['results'];
        for(var i in resultActivity){
          if(resultActivity[i].text){
            var text = resultActivity[i].text;
            this.PlatformActivity.push({"data": text + " by " + resultActivity[i].user.username,"time":resultActivity[i].created_at})
          }else if(resultActivity[i].item){
            if(resultActivity[i].item.type){
              var type = resultActivity[i].item.type;
              if(resultActivity[i].item.type=='Rule'){
                if(resultActivity[i].item.name){
                  var start = type + " with name '"+resultActivity[i].item.name+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='Tag'){
                if(resultActivity[i].item.name){
                  var start = type + " with name '"+resultActivity[i].item.name+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='Query'){
                if(resultActivity[i].item.name){
                  var start = type + " with name '"+resultActivity[i].item.name+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='Pack'){
                if(resultActivity[i].item.name){
                  var start = type + " with name '"+resultActivity[i].item.name+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='Config'){
                if(resultActivity[i].item.name){
                  var start = type + " of platform '"+resultActivity[i].item.platform+"' with name '"+resultActivity[i].item.name+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='Settings'){
                if(resultActivity[i].item.name){
                  var start = type + " with name '"+resultActivity[i].item.name+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='DefaultFilters'){
                var start = type + " of platform '"+resultActivity[i].item.platform+"' with config name '"+resultActivity[i].item.config_name+"'";
              }else if(resultActivity[i].item.type=='DefaultQuery'){
                var start = type + " '" + resultActivity[i].item.name + "'" + " of platform '"+resultActivity[i].item.platform+"' with config name '"+resultActivity[i].item.config_name+"'";
              }else if(resultActivity[i].item.type=='NodeConfig'){
                var start = type + " of the node with name '"+resultActivity[i].item.hostname+"'";
              }else if(resultActivity[i].item.type=='ThreatIntelCredentials'){
                if(resultActivity[i].item.name){
                  var start = type + " with name '"+resultActivity[i].item.name+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='IOCIntel'){
                var start = type;
              }else if(resultActivity[i].item.type=='VirusTotalAvEngines'){
                var start = type;
              }else if(resultActivity[i].item.type=='Alerts'){
                var start = type + " with id '"+resultActivity[i].item.id+"'";
              }else if(resultActivity[i].item.type=='Node'){
                if(resultActivity[i].item.name){
                  var start = type + " with name '"+resultActivity[i].item.name+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='CarveSession'){
                if(resultActivity[i].item.session_id){
                  var start = type + " with session id '"+resultActivity[i].item.session_id+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }else if(resultActivity[i].item.type=='User'){
                if(resultActivity[i].item.username){
                  var start = type + " with username '"+resultActivity[i].item.username+"'";
                }else{
                  var start = type + " with id '"+resultActivity[i].item.id+"'";
                }
              }
              this.PlatformActivity.push({"data": start + " has been " + resultActivity[i].action + " by " + resultActivity[i].user.username,"time":resultActivity[i].created_at})
            }
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
platformAcitivityTableSearch(){
  this.platformAcitivitySearchTerm = (<HTMLInputElement>document.getElementById('platformId')).value;
  this.dtTrigger_platformAcitivity.next();
}
userDetailsTableSearch(){
  this.userDetailSearchTerm = (<HTMLInputElement>document.getElementById('customsearch')).value;
  this.dtElement_userDetails.dtInstance.then((dtInstance: DataTables.Api) => {
    dtInstance.destroy();
    this.dtTrigger_userDetails.next();
  });
}
platformSearch(){
  $('.platformAcitivity').on('keyup', function(){
    var searchValue = (<HTMLInputElement>document.getElementById('platformId')).value;
    if (searchValue != ''){
      $('.platformAcitivity').addClass("custom-search-typing");
      $('.fa-times').addClass("visible");
    }
     else {
      $('.platformAcitivity').removeClass("custom-search-typing");
      $('.fa-times').removeClass("visible");
    }
  });
}
clearSearch(){
  (<HTMLInputElement>document.getElementById('platformId')).value = ''
  $('.platformAcitivity').removeClass("custom-search-typing");
  $('.fa-times').removeClass("visible");
  this.platformAcitivityTableSearch();
}
  ngAfterViewInit(): void {
    this.dtTrigger_userDetails.next();
    this.dtTrigger_platformAcitivity.next();
  }
  setRoleFilter(status){
    this.selectedRoleFilter = status.value;
    this.dtElement_userDetails.dtInstance.then((dtInstance: DataTables.Api) => {
      dtInstance.destroy();
      this.dtTrigger_userDetails.next();
    });

  }
  setStatusFilter(status){
    this.selectedStatusFilter = status.value;
    this.dtElement_userDetails.dtInstance.then((dtInstance: DataTables.Api) => {
      dtInstance.destroy();
      this.dtTrigger_userDetails.next();
    });
  }
}
