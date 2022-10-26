import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { JsonEditorComponent, JsonEditorOptions } from 'ang-jsoneditor';
import { Location } from '@angular/common';
import swal from 'sweetalert';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import Swal from 'sweetalert2';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import 'ace-builds/src-noconflict/mode-javascript';
import "ace-builds/webpack-resolver";
@Component({
  selector: 'app-ioc',
  templateUrl: './ioc.component.html',
  styleUrls: ['./ioc.component.css']
})

export class IocComponent implements OnInit {
  public editorOptions: JsonEditorOptions;
  @ViewChild(JsonEditorComponent, { static: true }) editor: JsonEditorComponent;
  options = new JsonEditorOptions();
  ioc_val: any;
  public data = {};
  loading = false;
  submitted = false;
  Updated: any;
  public result: any;
  error: any;
  public json_data: any = {};
  project_name=this.commonvariable.APP_NAME
  ProductNameER=this.commonvariable.ProductNameER
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  isLoading:Boolean = false;
  iocData={};
  constructor(
    private commonapi: CommonapiService,
    private _location: Location,
    private commonvariable: CommonVariableService,
    private authorizationService: AuthorizationService,

  ) {
    // this.options.mode = 'code';
    // this.options.modes = ['code', 'text', 'tree', 'view'];
    this.options.onChange = () => this.json_data['data'] = this.editor.getText()
  }
  toggle: boolean = false;

  ngOnInit() {

    if(this.authorizationService.hasAccess()){
      this.options.modes = ['code', 'text', 'tree', 'view'];
      this.options.mode = 'code';
    } else{
       this.options.mode = 'view';
       this.options.navigationBar = false;
    }
    this.toggle = false;
    setTimeout(()=>{
      this.getIocData();
    }, 100);
  }
  getIocData(){
    this.commonapi.ioc_api().subscribe(res => {
      this.ioc_val = res;
      this.editorOptions = new JsonEditorOptions();
      // this.editorOptions.mode = 'code';
      // this.editorOptions.modes = ['code','text', 'tree', 'view'];
      this.data = this.ioc_val.data;
      this.iocData = this.ioc_val.data;
      this.json_data['data'] = this.data;
      this.toggle = true;
    });
  }

  public setTreeMode() {
    this.editor.setMode('tree');
  }

  onSubmit() {
    try {
      if(typeof this.json_data['data'] === 'string'){
        this.json_data['data'] = JSON.parse(this.json_data.data);
       }
      if(Object.entries(this.json_data.data).length==0){
        Swal.fire({
        icon: 'warning',
        title: 'failure',
        text: "Please upload valid JSON",
        })
        } else{
      this.isLoading = true;
      this.commonapi.ioc_update_api(this.json_data).subscribe(res => {
        this.result = res;
        if (this.result && this.result.status === 'failure') {
          swal({
            icon: 'warning',
            title: this.result.status,
            text: this.result.message,
          })
          this.isLoading = false;
        } else {
          swal({
            icon: 'success',
            title: 'Success',
            text: this.result.message,
            buttons: [false],
            timer: 2000,
          })
          this.error = null;
          this.Updated = true;
          this.isLoading = false;
        }
         setTimeout(() => {
          // location.reload();
          this.ngOnInit()
        },2000);
      },
        error => {
          console.log(error);
        }
      )
      }
   }
   catch (e) {
    Swal.fire({
      icon: 'warning',
      title: 'failure',
      text:"Please upload valid JSON"
      })
      return
   }
  }

  clearIoc() {
    this.data = {}
    setTimeout(() => {this.data = this.iocData},100);
  }
  goBack(){
    this._location.back();
  }

}
