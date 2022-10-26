import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, FormBuilder, Validators } from '@angular/forms';
import { FormArray } from '@angular/forms';
import { Router,ActivatedRoute } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import {CommonapiService} from '../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../dashboard/_services/commonvariable.service';
import { loginService } from './login.service';
export interface CustomResponse {
  data: any;
  message: any;
  status: any;
}
@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  loading = false;
  submitted = false;
  data: any;
  error: string;
  redirectURL:any;
  fieldTextType: boolean;
  LiveQueriesTable:any;
  ProductName=this.commonvariable.ProductName
  ssoStatus:Boolean
  constructor(
    private router: Router,
    private _loginService: loginService,
    private toastr: ToastrService,
    private _Activatedroute: ActivatedRoute,
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
  ) { }

  ngOnInit() {
    let params = this._Activatedroute.snapshot.queryParams;
     if(localStorage.getItem('token')){
       this.redirectURL = params['redirectURL'];

       if (this.redirectURL) {
            this.router.navigateByUrl(this.redirectURL,)
          .catch(() => this.router.navigate(['/dashboard']))
         } else {
           this.router.navigate(['/dashboard']);
       }
     }
     else{
       if (params['redirectURL']) {
           this.redirectURL = params['redirectURL'];
       }
     }
     this.commonapi.getSSOStatus().subscribe(res=>{

       this.ssoStatus=res['sso_status']
     });
    }

  credentials = {
    username: "",
    password: "",
  }

  onSubmit(object) {
    this.error=''
    if (object.value.username == "" || object.value.username == null || (object.value.password == "" || object.value.password == null)) {
			this.toastr.warning('Please enter Username/Password!');
		}
		else {
    this.submitted = true;
    this.loading = true;

    setTimeout(()=>{
      this.loading = false;
    }, 30000);

    this._loginService.login(object).subscribe(

      response => {
        var temp = response;
        this.loading = false;
        if(temp.token){
          this.data = temp.token;
          localStorage.setItem('reset_password', response.reset_password);
          localStorage.setItem('roles', response.roles);
          localStorage.setItem('all_roles', response.all_roles);
          localStorage.setItem('token',response.token);
          localStorage.setItem('auth_type',response.auth_type);
          if(response.reset_password)
          {
            this.router.navigate(['/authentication/Change-Password']);
            return;
          }
          else if (this.redirectURL) {
               this.router.navigateByUrl(this.redirectURL,).catch(() => this.router.navigate(['/dashboard']))
          } else {
            this.router.navigate(['/dashboard']);
          }
          this.LiveQueryTableSchema();
            if(response.first_name){
            this.toastr.success("Welcome "+response.first_name);
            }
            else{
              this.commonapi.getUserDetails().subscribe(response=>{
                if(response['status'] === 'success'){
                  this.toastr.success("Welcome "+response['data'].username)
                }else{
                  this.toastr.error(response['message'])
                }
              })
            }
        }else{
          this.error = 'Incorrect Username or Password';
          this.toastr.warning("Incorrect Username or Password","");
        }
      },
      error => {
        this.error = 'Something went wrong! Please try again';
        this.loading = false;
      })
    }
  }

  toggleFieldTextType() {
    this.fieldTextType = !this.fieldTextType;
  }

  LiveQueryTableSchema(){
         this.commonapi.live_Queries_tables_schema().subscribe((res: CustomResponse) => {
           var _arraytable = [];
           var _arraycolumn = []
           this.LiveQueriesTable=res.data;
           this.LiveQueriesTable.forEach(function (table) {
               _arraytable.push(table.name);
               _arraycolumn.push(Object.keys(table.schema));
           });
           var _tablestring = _arraytable.toString();
           var _columnstring = _arraycolumn.toString();
           var _newchar = '|'
           var _livequerytabledata = _tablestring.split(',').join(_newchar);
           var _livequerycolumndata = _columnstring.split(',').join(_newchar);
           localStorage.setItem("Livequerytable", _livequerytabledata);
           localStorage.setItem("Livequerycolumn", _livequerycolumndata);
         })
       }
  makeSSOAuth(){
    window.location.href = this.commonapi.getSSOLoginURL();
 }

}
